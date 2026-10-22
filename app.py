"""Compatibility launcher for the TrustFarm Flask API."""
from backend.run import app

if __name__ == "__main__":
    app.run(port=5000, debug=True)
