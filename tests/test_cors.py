"""Tests for CORS origin validation in app/main.py."""
import pytest
from unittest.mock import patch


def _get_cors(origin: str, env: str) -> list[str]:
    """Call _get_cors_origins with patched settings."""
    from app import main as m
    with patch.object(m.settings, "CORS_ORIGIN", origin), \
         patch.object(m.settings, "ENVIRONMENT", env):
        return m._get_cors_origins()


# --- Production guard ---

def test_production_wildcard_raises():
    """CORS_ORIGIN=* in production must raise RuntimeError."""
    with pytest.raises(RuntimeError, match="CORS_ORIGIN must be explicitly set"):
        _get_cors("*", "production")


def test_production_empty_raises():
    """Empty CORS_ORIGIN in production must raise RuntimeError."""
    with pytest.raises(RuntimeError, match="CORS_ORIGIN must be explicitly set"):
        _get_cors("", "production")


def test_production_valid_origin():
    """Valid CORS_ORIGIN in production returns that origin only."""
    origins = _get_cors("https://app.adhera.health", "production")
    assert origins == ["https://app.adhera.health"]


def test_production_multi_origin():
    """Comma-separated CORS_ORIGIN in production returns all listed origins."""
    origins = _get_cors("https://app.adhera.health,https://admin.adhera.health", "production")
    assert "https://app.adhera.health" in origins
    assert "https://admin.adhera.health" in origins
    assert len(origins) == 2


# --- Development ---

def test_development_includes_localhost():
    """Development mode always includes localhost origins."""
    origins = _get_cors("http://localhost:8080", "development")
    assert "http://localhost:3000" in origins
    assert "http://localhost:8080" in origins
    assert "http://127.0.0.1:3000" in origins


def test_development_no_duplicate():
    """Configured origin already in dev defaults is not duplicated."""
    origins = _get_cors("http://localhost:3000", "development")
    assert origins.count("http://localhost:3000") == 1


def test_development_custom_origin_merged():
    """Custom origin in development is prepended and localhost defaults appended."""
    origins = _get_cors("https://staging.adhera.health", "development")
    assert "https://staging.adhera.health" in origins
    assert "http://localhost:3000" in origins


def test_staging_env_not_restricted():
    """Non-production envs (staging, test) behave like development."""
    origins = _get_cors("https://staging.adhera.health", "staging")
    assert "http://localhost:3000" in origins
