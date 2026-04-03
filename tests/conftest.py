"""Shared test fixtures."""

import pytest

from meta_ads_mcp.config import MetaAPIConfig, RateLimitConfig, ServerConfig


@pytest.fixture
def mock_config():
    """Server config with a fake token for testing."""
    return ServerConfig(
        meta=MetaAPIConfig(access_token="FAKE_TOKEN_FOR_TESTING"),
        rate_limit=RateLimitConfig(max_calls_per_hour=100, burst_size=10),
        log_level="DEBUG",
        debug=True,
    )


@pytest.fixture
def env_with_token(monkeypatch):
    """Set META_ACCESS_TOKEN in environment for config loading tests."""
    monkeypatch.setenv("META_ACCESS_TOKEN", "FAKE_TOKEN_FOR_TESTING")
