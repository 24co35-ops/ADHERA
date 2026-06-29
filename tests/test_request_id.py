import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_request_id_generated():
    """If no X-Request-ID header is sent, a fresh UUID must be generated and returned."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    req_id = response.headers.get("X-Request-ID")
    assert req_id is not None
    # Must be a valid UUID
    val = uuid.UUID(req_id)
    assert val is not None

def test_request_id_propagated():
    """If X-Request-ID header is sent, it must be returned in the response."""
    test_id = "test-req-id-12345"
    response = client.get("/v1/health", headers={"X-Request-ID": test_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == test_id
