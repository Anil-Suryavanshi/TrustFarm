from __future__ import annotations

from datetime import datetime, timedelta, timezone
import random

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
MOISTURE_THRESHOLD = 30
MAX_AGE_MINUTES = 20
MINIMUM_ACTION_SCORE = 85
history: list[dict] = []


def now() -> datetime:
    return datetime.now(timezone.utc)


def make_reading(scenario: str = "normal") -> dict:
    previous = history[-1] if history else None
    moisture_base = previous.get("soil_moisture", 42) if previous and previous.get("soil_moisture") is not None else 42
    temperature_base = previous.get("temperature", 29) if previous else 29
    humidity_base = previous.get("humidity", 62) if previous else 62
    reading = {
        "timestamp": now().isoformat(),
        "soil_moisture": round(max(12, min(75, moisture_base + random.uniform(-3.5, 1.2))), 1),
        "temperature": round(max(18, min(45, temperature_base + random.uniform(-1.5, 1.8))), 1),
        "humidity": round(max(20, min(95, humidity_base + random.uniform(-3, 3))), 1),
        "scenario": scenario,
    }
    if scenario == "dry":
        reading["soil_moisture"] = round(random.uniform(18, 27), 1)
    elif scenario == "missing":
        reading["soil_moisture"] = None
    elif scenario == "stale":
        reading["timestamp"] = (now() - timedelta(minutes=45)).isoformat()
    elif scenario == "anomaly":
        reading["soil_moisture"] = round(random.choice([random.uniform(0, 8), random.uniform(88, 100)]), 1)
    return reading


def analyze(reading: dict) -> dict:
    issues = []
    components = {"freshness": 1.0, "completeness": 1.0, "validity": 1.0, "consistency": 1.0}
    values = [reading.get("soil_moisture"), reading.get("temperature"), reading.get("humidity")]
    if any(value is None for value in values):
        components["completeness"] = 0.0
        issues.append("Missing sensor value")
    age_minutes = (now() - datetime.fromisoformat(reading["timestamp"])).total_seconds() / 60
    if age_minutes > MAX_AGE_MINUTES:
        components["freshness"] = 0.15
        issues.append(f"Data is stale ({age_minutes:.0f} minutes old)")
    moisture = reading.get("soil_moisture")
    temperature = reading.get("temperature")
    humidity = reading.get("humidity")
    if (moisture is not None and not 0 <= moisture <= 100) or (temperature is not None and not -10 <= temperature <= 60) or (humidity is not None and not 0 <= humidity <= 100):
        components["validity"] = 0.0
        issues.append("A reading is outside its physical range")
    if moisture is not None and len(history) > 1:
        # The dashboard analyses the newest item, so compare it with the
        # immediately preceding observation rather than with itself.
        prior = history[-2].get("soil_moisture")
        if prior is not None and abs(moisture - prior) > 22:
            components["consistency"] = 0.25
            issues.append("Sudden soil-moisture change detected")
    score = round(100 * (0.30 * components["freshness"] + 0.25 * components["completeness"] + 0.20 * components["validity"] + 0.25 * components["consistency"]))
    if score < MINIMUM_ACTION_SCORE:
        decision = "Verify data first"
        explanation = "The system abstained because the latest data is not sufficiently reliable."
    elif moisture < MOISTURE_THRESHOLD:
        decision = "Irrigate"
        explanation = f"Soil moisture is below the configured {MOISTURE_THRESHOLD}% threshold and data quality is acceptable."
    else:
        decision = "Do not irrigate"
        explanation = f"Soil moisture is at or above the configured {MOISTURE_THRESHOLD}% threshold and data quality is acceptable."
    return {"trust_score": score, "components": components, "issues": issues, "decision": decision, "explanation": explanation, "age_minutes": round(max(0, age_minutes), 1)}


def seed() -> None:
    for offset in range(11, 0, -1):
        reading = {
            "timestamp": (now() - timedelta(minutes=offset * 10)).isoformat(),
            "soil_moisture": round(51 - (11 - offset) * 1.4 + random.uniform(-1.5, 1.5), 1),
            "temperature": round(27 + random.uniform(-1.2, 2.4), 1),
            "humidity": round(68 - (11 - offset) * 0.8 + random.uniform(-2, 2), 1),
            "scenario": "normal",
        }
        history.append(reading)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/dashboard")
def dashboard():
    latest = history[-1]
    analysis = analyze(latest)
    return jsonify({"latest": latest, "analysis": analysis, "history": history[-24:], "threshold": MOISTURE_THRESHOLD})


@app.post("/api/simulate")
def simulate():
    body = request.get_json(silent=True) or {}
    scenario = body.get("scenario", "normal")
    if scenario not in {"normal", "dry", "missing", "stale", "anomaly"}:
        return jsonify({"error": "Unknown simulation scenario"}), 400
    reading = make_reading(scenario)
    history.append(reading)
    return dashboard()


seed()

if __name__ == "__main__":
    app.run(debug=True)
