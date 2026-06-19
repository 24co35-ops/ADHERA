"""Tests for slowapi rate limiting integration."""
import json
import asyncio
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app, _rate_limit_handler

client = TestClient(app)


def _make_rate_limit_exc():
    """Build a valid RateLimitExceeded using a mock limit object."""
    from slowapi.errors import RateLimitExceeded
    limit = MagicMock()
    limit.error_message = None
    exc = RateLimitExceeded.__new__(RateLimitExceeded)
    exc.status_code = 429
    exc.detail = "Rate limit exceeded"
    exc.limit = limit
    return exc


def test_rate_limit_429_shape():
    """RateLimitExceeded handler must return ADHERA error shape with 429."""
    mock_request = MagicMock()
    exc = _make_rate_limit_exc()

    response = asyncio.get_event_loop().run_until_complete(
        _rate_limit_handler(mock_request, exc)
    )
    data = json.loads(response.body)

    assert response.status_code == 429
    assert data["success"] is False
    assert data["error"]["code"] == "RATE_LIMITED"
    assert data["error"]["message"] == "Too many requests"


def test_slowapi_middleware_registered():
    """SlowAPIMiddleware must be in the middleware stack and limiter on app.state."""
    from slowapi.middleware import SlowAPIMiddleware
    assert hasattr(app.state, "limiter")
    mw_classes = [m.cls for m in app.user_middleware if hasattr(m, "cls")]
    assert SlowAPIMiddleware in mw_classes
