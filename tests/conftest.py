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
