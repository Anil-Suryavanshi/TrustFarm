import csv
import io
import time
from flask import Flask, jsonify, request, Response

from .analysis import analyze_all
from .config import Settings
from .decisions import baseline_decision, decide
from .repository import ReadingRepository
from .simulator import SCENARIOS, VirtualSensorSimulator


def ok(data=None, message="Request completed successfully", status=200):
    return jsonify({"success": True, "data": data, "message": message}), status


def fail(code, message, status=400, details=None):
    return jsonify({"success": False, "error": {"code": code, "message": message, "details": details or {}}}), status


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=512 * 1024)
    if test_config: app.config.update(test_config)
    settings = Settings()
    repo = ReadingRepository(settings.history_limit)
    simulator = VirtualSensorSimulator(settings)
    experiments = []

    @app.after_request
    def local_cors(response):
        origin = request.headers.get("Origin")
        if origin in {"http://localhost:5173", "http://127.0.0.1:5173"}:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    def state():
        readings = repo.all(); analyses = analyze_all(readings, settings)
        return readings, analyses

    def run_step(scenario):
        readings = simulator.generate(scenario)
        repo.add_many(readings)
        return readings

    @app.get("/api/v1/health")
    def health(): return ok({"status": "healthy", "service": "trustfarm-api"})

    @app.get("/api/v1/dashboard/summary")
    def dashboard_summary():
        readings, analyses = state(); latest = repo.latest_by_sensor(); latest_analysis = {item["sensor_id"]: item for item in analyses}
        valid = [item for item in latest.values() if item.get("soil_moisture") is not None]
        flagged = sum(bool(latest_analysis.get(key, {}).get("flags")) for key in latest)
        decision = decide(readings, analyses, settings)
        return ok({"sensor_count": settings.sensor_count, "active_sensors": len(latest), "flagged_sensors": flagged, "average_soil_moisture": round(sum(item["soil_moisture"] for item in valid) / len(valid), 1) if valid else None, "average_temperature_c": round(sum(item["temperature_c"] for item in valid) / len(valid), 1) if valid else None, "average_humidity_pct": round(sum(item["humidity_pct"] for item in valid) / len(valid), 1) if valid else None, "simulation": {"running": simulator.running, "scenario": readings[-1]["scenario"] if readings else "normal"}, "decision": decision, "recent_alerts": [item for item in analyses if item["flags"]][-10:]})

    @app.get("/api/v1/sensors")
    def sensors():
        readings, analyses = state(); analysis_by_sensor = {x["sensor_id"]: x for x in analyses}
        return ok([{"sensor_id": sensor_id, "latest_reading": reading, "analysis": analysis_by_sensor.get(sensor_id)} for sensor_id, reading in repo.latest_by_sensor().items()])

    @app.get("/api/v1/sensors/<sensor_id>/history")
    def sensor_history(sensor_id):
        items = repo.sensor_history(sensor_id)
        if not items: return fail("NOT_FOUND", "Sensor was not found", 404)
        return ok({"items": items, "analysis": analyze_all(items, settings)})

    @app.get("/api/v1/readings")
    def readings():
        try: page, page_size = max(1, int(request.args.get("page", 1))), min(100, max(1, int(request.args.get("page_size", 25))))
        except ValueError: return fail("VALIDATION_ERROR", "page and page_size must be integers")
        items = repo.all(); sensor_id, scenario = request.args.get("sensor_id"), request.args.get("scenario")
        if sensor_id: items = [x for x in items if x["sensor_id"] == sensor_id]
        if scenario: items = [x for x in items if x["scenario"] == scenario]
        start = (page - 1) * page_size
        return ok({"items": items[start:start + page_size], "page": page, "page_size": page_size, "total_records": len(items), "has_next_page": start + page_size < len(items)})

    @app.route("/api/v1/simulation/<action>", methods=["POST"])
    def simulation(action):
        body = request.get_json(silent=True) or {}
        if action == "start":
            scenario = body.get("scenario", "normal")
            if scenario not in SCENARIOS: return fail("VALIDATION_ERROR", "Unsupported scenario")
            simulator.running = True; items = run_step(scenario)
            return ok({"running": True, "generated": len(items)}, "Simulation started")
        if action == "pause": simulator.running = False; return ok({"running": False}, "Simulation paused")
        if action == "resume": simulator.running = True; return ok({"running": True}, "Simulation resumed")
        if action == "reset": simulator.reset(); repo.clear(); return ok({"running": False}, "Simulation reset")
        if action == "step":
            scenario = body.get("scenario", "normal")
            if scenario not in SCENARIOS: return fail("VALIDATION_ERROR", "Unsupported scenario")
            return ok({"generated": run_step(scenario)}, "Virtual readings generated")
        return fail("NOT_FOUND", "Simulation action not found", 404)

    @app.get("/api/v1/simulation/status")
    def simulation_status(): return ok({"running": simulator.running, "tick": simulator.tick, "scenarios": sorted(SCENARIOS), "settings": settings.public()})

    @app.get("/api/v1/analysis/quality")
    def quality():
        readings, analyses = state()
        return ok({"items": analyses, "total": len(analyses), "flagged": sum(bool(x["flags"]) for x in analyses)})

    @app.get("/api/v1/analysis/decisions")
    def decisions():
        readings, analyses = state(); proposed = decide(readings, analyses, settings)
        baseline = baseline_decision(readings[-1] if readings else None, settings)
        return ok({"proposed": proposed, "baseline": {"status": baseline}, "note": "Simulated decision support only; validate against crop, soil and field conditions."})

    @app.post("/api/v1/analysis/run")
    def analysis_run():
        readings, analyses = state(); return ok({"quality": analyses, "decision": decide(readings, analyses, settings)})

    @app.get("/api/v1/settings")
    def get_settings(): return ok(settings.public())

    @app.put("/api/v1/settings")
    def put_settings():
        body = request.get_json(silent=True)
        if not isinstance(body, dict): return fail("VALIDATION_ERROR", "A JSON object is required")
        try: settings.update(body)
        except ValueError as error: return fail("VALIDATION_ERROR", str(error))
        return ok(settings.public(), "Settings updated")

    @app.post("/api/v1/experiments/run")
    def run_experiment():
        body = request.get_json(silent=True) or {}; scenario = body.get("scenario", "mixed"); steps = body.get("steps", 20)
        if scenario not in SCENARIOS - {"outage"} or not isinstance(steps, int) or not 1 <= steps <= 100: return fail("VALIDATION_ERROR", "Use a supported scenario and 1–100 steps")
        started = time.perf_counter(); temporary = VirtualSensorSimulator(settings); records = []
        for _ in range(steps): records.extend(temporary.generate(scenario))
        analyses = analyze_all(records, settings); actual = [x["ground_truth_fault"] for x in records]; detected = [bool(x["flags"]) for x in analyses]
        tp = sum(a and d for a, d in zip(actual, detected)); fp = sum(not a and d for a, d in zip(actual, detected)); fn = sum(a and not d for a, d in zip(actual, detected)); tn = sum(not a and not d for a, d in zip(actual, detected))
        precision = tp / (tp + fp) if tp + fp else 0; recall = tp / (tp + fn) if tp + fn else 0
        result = {"experiment_id": f"EXP-{len(experiments)+1:03d}", "scenario": scenario, "seed": settings.seed, "records": len(records), "metrics": {"precision": round(precision, 3), "recall": round(recall, 3), "f1_score": round(2 * precision * recall / (precision + recall), 3) if precision + recall else 0, "false_positive_rate": round(fp / (fp + tn), 3) if fp + tn else 0, "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn}, "processing_ms": round((time.perf_counter() - started) * 1000, 2)}}
        experiments.append(result); return ok(result, "Experiment completed")

    @app.get("/api/v1/experiments")
    def list_experiments(): return ok(experiments)

    @app.get("/api/v1/experiments/<experiment_id>")
    def get_experiment(experiment_id):
        result = next((x for x in experiments if x["experiment_id"] == experiment_id), None)
        return ok(result) if result else fail("NOT_FOUND", "Experiment was not found", 404)

    @app.get("/api/v1/data/export")
    def export_data():
        readings = repo.all(); columns = ["reading_id", "sensor_id", "timestamp", "soil_moisture", "temperature_c", "humidity_pct", "scenario", "ground_truth_fault", "data_source"]
        output = io.StringIO(); writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore"); writer.writeheader(); writer.writerows(readings)
        return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=trustfarm_readings.csv"})

    @app.errorhandler(413)
    def too_large(_): return fail("PAYLOAD_TOO_LARGE", "Upload must be smaller than 512 KB", 413)
    @app.errorhandler(404)
    def not_found(_): return fail("NOT_FOUND", "Route not found", 404)
    return app
