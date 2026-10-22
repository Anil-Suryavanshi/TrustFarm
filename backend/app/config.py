from dataclasses import dataclass, field


@dataclass
class Settings:
    sensor_count: int = 5
    interval_seconds: int = 10
    fault_probability: float = 0.15
    seed: int = 42
    history_limit: int = 500
    freshness_minutes: int = 20
    moisture_threshold: float = 30.0
    minimum_trust_score: int = 85
    temperature_min: float = -10.0
    temperature_max: float = 60.0
    stuck_tolerance: float = 0.1
    stuck_sequence_length: int = 3

    def public(self):
        return self.__dict__.copy()

    def update(self, values: dict):
        allowed = set(self.__dict__)
        invalid = {key: value for key, value in values.items() if key not in allowed}
        if invalid:
            raise ValueError(f"Unsupported setting(s): {', '.join(invalid)}")
        for key, value in values.items():
            if key in {"sensor_count", "interval_seconds", "history_limit", "freshness_minutes", "minimum_trust_score", "stuck_sequence_length"}:
                if not isinstance(value, int) or value < 1:
                    raise ValueError(f"{key} must be a positive integer")
            elif key in {"fault_probability"}:
                if not isinstance(value, (int, float)) or not 0 <= value <= 1:
                    raise ValueError("fault_probability must be between 0 and 1")
            elif key in {"moisture_threshold", "temperature_min", "temperature_max", "stuck_tolerance"}:
                if not isinstance(value, (int, float)):
                    raise ValueError(f"{key} must be numeric")
            elif key == "seed" and not isinstance(value, int):
                raise ValueError("seed must be an integer")
            setattr(self, key, value)
        if self.temperature_min >= self.temperature_max:
            raise ValueError("temperature_min must be lower than temperature_max")
