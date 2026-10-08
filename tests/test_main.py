import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Posture server is running"}


def test_measure_ok():
    response = client.post("/measure", json={"distance": 40})
    assert response.status_code == 200
    assert response.json()["current"] == "ok"


def test_measure_warning():
    response = client.post("/measure", json={"distance": 10})
    assert response.status_code == 200
    assert response.json()["current"] == "warning"


def test_status():
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "distance" in data
    assert "status" in data


def test_settings():
    response = client.get("/settings")
    assert response.status_code == 200
    data = response.json()
    assert "threshold" in data
    assert "duration" in data
    assert "calibrated" in data


def test_update_settings():
    client.post("/settings", json={"threshold": 15})
    response = client.get("/settings")
    assert response.json()["threshold"] == 15


def test_calibrate():
    client.post("/measure", json={"distance": 50})
    response = client.post("/calibrate")
    assert response.status_code == 200
    assert response.json()["distance"] == 50


def test_stats():
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "good_minutes" in data
    assert "bad_minutes" in data