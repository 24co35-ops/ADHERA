import os
os.environ["ENVIRONMENT"] = "test"
os.environ["SENTRY_DSN"] = ""

from unittest.mock import MagicMock, patch
import pytest

@pytest.fixture
def mock_supabase(monkeypatch):
    mock_client = MagicMock()
    table_mock = MagicMock()
    table_mock.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
    table_mock.select.return_value.in_.return_value.execute.return_value.data = []
    mock_client.table.return_value = table_mock
    # Mock both supabase client object and get_supabase function
    monkeypatch.setattr("app.db.supabase.supabase", mock_client)
    try:
        monkeypatch.setattr("app.db.client.get_supabase", lambda: mock_client)
    except Exception:
        pass
    return mock_client


@pytest.fixture(autouse=True)
def mock_audit_insert():
    """
    Suppress all real audit writes for every test.
    audit.py._do_insert is fire-and-forget; without this, failed background
    inserts from one test corrupt the shared httpx connection pool, causing
    the subsequent test's supabase.execute() call to see a disconnected
    client and return db='error' on test_health_returns_ok.
    """
    with patch("app.services.audit._do_insert"):
        yield
