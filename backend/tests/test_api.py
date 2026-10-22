import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app


class TrustFarmApiTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app({"TESTING": True}).test_client()

    def post(self, route, body=None):
        return self.client.post(route, json=body or {})

    def test_health_uses_standard_response(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])

    def test_normal_simulation_creates_all_sensors(self):
        response = self.post("/api/v1/simulation/step", {"scenario": "normal"})
        self.assertEqual(len(response.get_json()["data"]["generated"]), 5)
        summary = self.client.get("/api/v1/dashboard/summary").get_json()["data"]
        self.assertEqual(summary["active_sensors"], 5)

    def test_missing_data_withholds_automatic_decision(self):
        self.post("/api/v1/simulation/step", {"scenario": "missing"})
        decision = self.client.get("/api/v1/analysis/decisions").get_json()["data"]["proposed"]
        self.assertIn(decision["status"], {"VERIFY_DATA", "INSUFFICIENT_DATA"})

    def test_invalid_scenario_is_rejected(self):
        response = self.post("/api/v1/simulation/step", {"scenario": "not-a-scenario"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"]["code"], "VALIDATION_ERROR")

    def test_experiment_calculates_metrics(self):
        response = self.post("/api/v1/experiments/run", {"scenario": "spike", "steps": 4})
        result = response.get_json()["data"]
        self.assertEqual(result["records"], 20)
        self.assertIn("f1_score", result["metrics"])
        self.assertIn("tp", result["metrics"]["confusion_matrix"])

    def test_settings_are_validated(self):
        response = self.client.put("/api/v1/settings", json={"fault_probability": 2})
        self.assertEqual(response.status_code, 400)

    def test_export_returns_csv(self):
        self.post("/api/v1/simulation/step", {"scenario": "normal"})
        response = self.client.get("/api/v1/data/export")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.content_type)
        self.assertIn(b"reading_id", response.data)


if __name__ == "__main__":
    unittest.main()
