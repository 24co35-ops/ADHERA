import pytest
from fastapi.testclient import TestClient
from app.main import app
import jwt
from app.config import settings

client = TestClient(app)

def test_api_contract_success():
    res = client.get("/v1/health")
    data = res.json()
    assert res.status_code == 200
    assert "success" in data
    assert data["success"] is True
    assert "data" in data
    assert "meta" in data
    assert "timestamp" in data["meta"]
    assert data["meta"]["version"] == "1.0"

def test_api_contract_error():
    # Trigger validation error
    res = client.post("/v1/auth/login", json={})
    data = res.json()
    assert res.status_code == 400
    assert "success" in data
    assert data["success"] is False
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
