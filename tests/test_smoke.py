"""Basic smoke tests — no AI calls needed."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_analyze_sync_missing_file():
    r = client.post("/analyze/sync", data={"mode": "image", "depth_level": "1"})
    assert r.status_code == 422
