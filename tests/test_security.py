"""Security tests: SSRF protection, token redaction, input validation."""

import pytest

from meta_ads_mcp.security import (
    redact_sensitive_params,
    validate_id,
    validate_url,
)


class TestURLValidation:
    """SSRF protection tests."""

    def test_allows_graph_facebook(self):
        url = "https://graph.facebook.com/v22.0/me"
        assert validate_url(url) == url

    def test_allows_www_facebook(self):
        url = "https://www.facebook.com/some/path"
        assert validate_url(url) == url

    def test_blocks_arbitrary_domain(self):
        with pytest.raises(ValueError, match="not in the allowlist"):
            validate_url("https://evil.com/steal-data")

    def test_blocks_localhost(self):
        with pytest.raises(ValueError, match="not in the allowlist"):
            validate_url("https://localhost/internal")

    def test_blocks_internal_ip(self):
        with pytest.raises(ValueError, match="not in the allowlist"):
            validate_url("https://192.168.1.1/admin")

    def test_blocks_http(self):
        with pytest.raises(ValueError, match="only HTTPS"):
            validate_url("http://graph.facebook.com/v22.0/me")

    def test_blocks_no_hostname(self):
        with pytest.raises(ValueError, match="no hostname"):
            validate_url("/relative/path")

    def test_blocks_meta_lookalike(self):
        with pytest.raises(ValueError, match="not in the allowlist"):
            validate_url("https://graph.facebook.com.evil.com/v22.0/me")

    def test_blocks_subdomain_bypass(self):
        with pytest.raises(ValueError, match="not in the allowlist"):
            validate_url("https://evil.graph.facebook.com/v22.0/me")


class TestIDValidation:
    """Input validation for Meta Ads IDs."""

    def test_valid_numeric_id(self):
        assert validate_id("123456789") == "123456789"

    def test_valid_act_prefix(self):
        assert validate_id("act_123456789") == "act_123456789"

    def test_rejects_empty(self):
        with pytest.raises(ValueError, match="Invalid"):
            validate_id("")

    def test_rejects_special_chars(self):
        with pytest.raises(ValueError, match="Invalid"):
            validate_id("123; DROP TABLE")

    def test_rejects_path_traversal(self):
        with pytest.raises(ValueError, match="Invalid"):
            validate_id("../../../etc/passwd")

    def test_rejects_url(self):
        with pytest.raises(ValueError, match="Invalid"):
            validate_id("https://evil.com")


class TestTokenRedaction:
    """Ensure tokens never appear in logs."""

    def test_redacts_access_token(self):
        params = {"access_token": "secret123", "fields": "name,id"}
        redacted = redact_sensitive_params(params)
        assert redacted["access_token"] == "***REDACTED***"
        assert redacted["fields"] == "name,id"

    def test_redacts_multiple_sensitive_fields(self):
        params = {
            "access_token": "tok123",
            "appsecret_proof": "proof456",
            "password": "pass789",
            "fields": "name",
        }
        redacted = redact_sensitive_params(params)
        assert redacted["access_token"] == "***REDACTED***"
        assert redacted["appsecret_proof"] == "***REDACTED***"
        assert redacted["password"] == "***REDACTED***"
        assert redacted["fields"] == "name"

    def test_handles_empty_dict(self):
        assert redact_sensitive_params({}) == {}

    def test_preserves_non_sensitive(self):
        params = {"limit": 25, "after": "cursor123"}
        assert redact_sensitive_params(params) == params
