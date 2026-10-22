from datetime import datetime, timedelta, timezone
import random
import uuid


SCENARIOS = {"normal", "missing", "stale", "out_of_range", "spike", "stuck", "outage", "mixed"}


class VirtualSensorSimulator:
    def __init__(self, settings):
        self.settings = settings
        self.random = random.Random(settings.seed)
        self.running = False
        self.tick = 0
        self.last_values = {}

    def reset(self):
        self.random = random.Random(self.settings.seed)
        self.tick, self.last_values, self.running = 0, {}, False

    def generate(self, scenario="normal"):
        if scenario not in SCENARIOS:
            raise ValueError("Unsupported scenario")
        if scenario == "outage":
            self.tick += 1
            return []
        now = datetime.now(timezone.utc)
        readings = []
        for index in range(1, self.settings.sensor_count + 1):
            sensor_id = f"SENSOR_{index:02d}"
            base = self.last_values.get(sensor_id, {"soil_moisture": 45 - index, "temperature_c": 27 + index / 2, "humidity_pct": 65 - index})
            values = {
                "soil_moisture": round(max(5, min(90, base["soil_moisture"] + self.random.uniform(-2.2, 1.0))), 1),
                "temperature_c": round(max(10, min(48, base["temperature_c"] + self.random.uniform(-1.0, 1.0))), 1),
                "humidity_pct": round(max(15, min(95, base["humidity_pct"] + self.random.uniform(-2.0, 2.0))), 1),
            }
            fault = False
            active_scenario = scenario
            if scenario == "mixed":
                active_scenario = self.random.choice(["missing", "stale", "spike", "stuck", "out_of_range"])
            if active_scenario == "missing" and index % 2 == 0:
                values["soil_moisture"] = None; fault = True
            elif active_scenario == "stale":
                timestamp = now - timedelta(minutes=self.settings.freshness_minutes + 15); fault = True
            elif active_scenario == "out_of_range":
                values["soil_moisture"] = 125.0; fault = True
            elif active_scenario == "spike":
                values["soil_moisture"] = 92.0 if base["soil_moisture"] < 60 else 4.0; fault = True
            elif active_scenario == "stuck":
                values = base.copy(); fault = True
            timestamp = locals().get("timestamp", now)
            reading = {"reading_id": f"R-{uuid.uuid4().hex[:10].upper()}", "sensor_id": sensor_id, "timestamp": timestamp.isoformat(), **values, "scenario": scenario, "ground_truth_fault": fault, "quality_flags": [], "data_source": "simulated"}
            readings.append(reading)
            if values["soil_moisture"] is not None:
                self.last_values[sensor_id] = values.copy()
            if "timestamp" in locals(): del timestamp
        self.tick += 1
        return readings
