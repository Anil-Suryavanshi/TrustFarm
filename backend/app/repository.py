from collections import deque


class ReadingRepository:
    def __init__(self, limit: int):
        self.limit = limit
        self.readings = deque(maxlen=limit)

    def add_many(self, readings):
        self.readings.extend(readings)

    def clear(self):
        self.readings.clear()

    def all(self):
        return list(self.readings)

    def sensor_history(self, sensor_id):
        return [item for item in self.readings if item["sensor_id"] == sensor_id]

    def latest_by_sensor(self):
        result = {}
        for item in self.readings:
            result[item["sensor_id"]] = item
        return result
