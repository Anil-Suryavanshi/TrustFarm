from datetime import datetime, timezone


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def analyze_reading(reading, prior_readings, settings):
    flags, components = [], {"freshness": 1.0, "completeness": 1.0, "validity": 1.0, "consistency": 1.0}
    required = ("soil_moisture", "temperature_c", "humidity_pct", "timestamp")
    if any(reading.get(field) is None for field in required):
        flags.append("MISSING_VALUE"); components["completeness"] = 0.0
    age = None
    try:
        age = max(0, (datetime.now(timezone.utc) - parse_time(reading["timestamp"])).total_seconds() / 60)
        if age > settings.freshness_minutes:
            flags.append("STALE_DATA"); components["freshness"] = 0.0
    except (KeyError, TypeError, ValueError):
        flags.append("INVALID_TIMESTAMP"); components["freshness"] = 0.0; components["completeness"] = 0.0
    moisture, temp, humidity = reading.get("soil_moisture"), reading.get("temperature_c"), reading.get("humidity_pct")
    try:
        if (moisture is not None and not 0 <= moisture <= 100) or (temp is not None and not settings.temperature_min <= temp <= settings.temperature_max) or (humidity is not None and not 0 <= humidity <= 100):
            flags.append("OUT_OF_RANGE"); components["validity"] = 0.0
    except TypeError:
        flags.append("INVALID_VALUE_TYPE"); components["validity"] = 0.0
    prior = [item for item in prior_readings if item["sensor_id"] == reading["sensor_id"]]
    if moisture is not None and prior:
        previous = prior[-1].get("soil_moisture")
        if previous is not None and abs(moisture - previous) > 22:
            flags.append("SUDDEN_CHANGE"); components["consistency"] = min(components["consistency"], .25)
        sequence = [item.get("soil_moisture") for item in prior[-(settings.stuck_sequence_length - 1):]]
        if len(sequence) == settings.stuck_sequence_length - 1 and all(value is not None and abs(value - moisture) <= settings.stuck_tolerance for value in sequence):
            flags.append("POSSIBLY_STUCK"); components["consistency"] = min(components["consistency"], .25)
    score = None if components["completeness"] == 0 else round(100 * (.30 * components["freshness"] + .25 * components["completeness"] + .20 * components["validity"] + .25 * components["consistency"]))
    return {"reading_id": reading["reading_id"], "sensor_id": reading["sensor_id"], "score": score, "components": components, "flags": flags, "age_minutes": None if age is None else round(age, 1)}


def analyze_all(readings, settings):
    previous, results = [], []
    for reading in readings:
        result = analyze_reading(reading, previous, settings)
        results.append(result); previous.append(reading)
    return results
