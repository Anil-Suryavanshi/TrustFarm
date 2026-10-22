def decide(readings, analyses, settings):
    pairs = list(zip(readings, analyses))
    # The overview recommendation represents the current sensor network, not
    # just whichever sensor happened to be generated last.
    latest = {}
    for reading, analysis in pairs:
        latest[reading["sensor_id"]] = (reading, analysis)
    if latest and any("MISSING_VALUE" in analysis["flags"] for _, analysis in latest.values()):
        return {"status": "INSUFFICIENT_DATA", "explanation": "At least one current virtual sensor is missing a required value; verify the network before acting.", "data_used": None}
    usable = [(r, a) for r, a in pairs if r.get("soil_moisture") is not None]
    if not usable:
        return {"status": "INSUFFICIENT_DATA", "explanation": "No complete soil-moisture reading is available.", "data_used": None}
    reading, analysis = usable[-1]
    if analysis["score"] is None:
        return {"status": "INSUFFICIENT_DATA", "explanation": "The latest reading is incomplete.", "data_used": reading}
    if analysis["score"] < settings.minimum_trust_score:
        return {"status": "VERIFY_DATA", "explanation": "Data quality is below the configured minimum; verify the virtual sensor before acting.", "data_used": reading}
    status = "IRRIGATION_RECOMMENDED" if reading["soil_moisture"] < settings.moisture_threshold else "NO_IRRIGATION_RECOMMENDED"
    return {"status": status, "explanation": f"Reliable simulated soil moisture is {reading['soil_moisture']}% against the demonstration threshold of {settings.moisture_threshold}%.", "data_used": reading}


def baseline_decision(reading, settings):
    if reading is None or reading.get("soil_moisture") is None:
        return "INSUFFICIENT_DATA"
    return "IRRIGATION_RECOMMENDED" if reading["soil_moisture"] < settings.moisture_threshold else "NO_IRRIGATION_RECOMMENDED"
