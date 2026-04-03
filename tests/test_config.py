"""Tests for configuration loading."""

import pytest

from meta_ads_mcp.config import MetaAPIConfig, load_config


class TestMetaAPIConfig:
    """Test MetaAPIConfig properties."""

    def test_graph_url_returns_correct_url(self):
        config = MetaAPIConfig(access_token="test_token")
        assert config.graph_url == "https://graph.facebook.com/v22.0"

    def test_graph_url_with_custom_version(self):
        config = MetaAPIConfig(access_token="test_token", api_version="v21.0")
        assert config.graph_url == "https://graph.facebook.com/v21.0"

    def test_graph_url_with_custom_base(self):
        config = MetaAPIConfig(
            access_token="test_token",
            base_url="https://custom.example.com",
            api_version="v22.0",
        )
        assert config.graph_url == "https://custom.example.com/v22.0"


class TestLoadConfig:
    """Test load_config() from environment variables."""

    def test_raises_when_token_not_set(self, monkeypatch):
        monkeypatch.delenv("META_ACCESS_TOKEN", raising=False)
        with pytest.raises(ValueError, match="META_ACCESS_TOKEN"):
            load_config()

    def test_succeeds_when_token_set(self, env_with_token):
        config = load_config()
        assert config.meta.access_token == "FAKE_TOKEN_FOR_TESTING"

    def test_uses_default_api_version(self, env_with_token):
        config = load_config()
        assert config.meta.api_version == "v22.0"

    def test_uses_default_rate_limit(self, env_with_token):
        config = load_config()
        assert config.rate_limit.max_calls_per_hour == 200

    def test_uses_default_log_level(self, env_with_token):
        config = load_config()
        assert config.log_level == "INFO"

    def test_uses_default_debug_false(self, env_with_token):
        config = load_config()
        assert config.debug is False

    def test_custom_api_version(self, env_with_token, monkeypatch):
        monkeypatch.setenv("META_API_VERSION", "v21.0")
        config = load_config()
        assert config.meta.api_version == "v21.0"

    def test_custom_rate_limit(self, env_with_token, monkeypatch):
        monkeypatch.setenv("META_RATE_LIMIT_PER_HOUR", "500")
        config = load_config()
        assert config.rate_limit.max_calls_per_hour == 500

    def test_debug_enabled(self, env_with_token, monkeypatch):
        monkeypatch.setenv("DEBUG", "true")
        config = load_config()
        assert config.debug is True
