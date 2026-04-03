"""Tests for tool handler functions (accounts module)."""

from unittest.mock import MagicMock

import pytest

from meta_ads_mcp.tools.accounts import (
    get_ad_account_details,
    list_ad_accounts,
)


@pytest.fixture
def mock_client():
    """Create a mocked MetaAPIClient."""
    client = MagicMock()
    return client


class TestListAdAccounts:
    """Test list_ad_accounts tool handler."""

    def test_calls_get_me_with_correct_fields(self, mock_client):
        mock_client.get_me.return_value = {"adaccounts": {"data": []}}
        list_ad_accounts(mock_client)
        mock_client.get_me.assert_called_once()
        call_kwargs = mock_client.get_me.call_args
        assert "adaccounts" in call_kwargs.kwargs.get("fields", "")

    def test_returns_dict_with_data_key(self, mock_client):
        mock_client.get_me.return_value = {
            "adaccounts": {
                "data": [{"id": "act_123", "name": "Test Account"}],
            }
        }
        result = list_ad_accounts(mock_client)
        assert "data" in result
        assert "pagination" in result
        assert len(result["data"]) == 1

    def test_handles_empty_adaccounts(self, mock_client):
        mock_client.get_me.return_value = {}
        result = list_ad_accounts(mock_client)
        assert result["data"] == []

    def test_returns_pagination_info(self, mock_client):
        mock_client.get_me.return_value = {
            "adaccounts": {
                "data": [],
                "paging": {
                    "cursors": {"after": "abc123", "before": "xyz789"},
                    "next": "https://graph.facebook.com/v22.0/me/adaccounts?after=abc123",
                },
            }
        }
        result = list_ad_accounts(mock_client)
        assert result["pagination"]["has_next"] is True
        assert result["pagination"]["after_cursor"] == "abc123"


class TestGetAdAccountDetails:
    """Test get_ad_account_details tool handler."""

    def test_calls_get_node_with_account_id(self, mock_client):
        mock_client.get_node.return_value = {"id": "act_123", "name": "Test"}
        get_ad_account_details(mock_client, "act_123")
        mock_client.get_node.assert_called_once()
        assert mock_client.get_node.call_args.args[0] == "act_123"

    def test_returns_dict_with_data_key(self, mock_client):
        mock_client.get_node.return_value = {"id": "act_123", "name": "Test"}
        result = get_ad_account_details(mock_client, "act_123")
        assert "data" in result
        assert result["data"]["id"] == "act_123"

    def test_rejects_invalid_account_id(self, mock_client):
        with pytest.raises(ValueError, match="Invalid"):
            get_ad_account_details(mock_client, "../../etc/passwd")

    def test_rejects_script_injection_id(self, mock_client):
        with pytest.raises(ValueError, match="Invalid"):
            get_ad_account_details(mock_client, "<script>alert(1)</script>")

    def test_rejects_empty_id(self, mock_client):
        with pytest.raises(ValueError, match="Invalid"):
            get_ad_account_details(mock_client, "")

    def test_accepts_numeric_id(self, mock_client):
        mock_client.get_node.return_value = {"id": "123456789"}
        result = get_ad_account_details(mock_client, "123456789")
        assert result["data"]["id"] == "123456789"

    def test_accepts_act_prefix_id(self, mock_client):
        mock_client.get_node.return_value = {"id": "act_123456789"}
        result = get_ad_account_details(mock_client, "act_123456789")
        assert result["data"]["id"] == "act_123456789"

    def test_uses_custom_fields(self, mock_client):
        mock_client.get_node.return_value = {"id": "act_123"}
        get_ad_account_details(mock_client, "act_123", fields=["name", "currency"])
        call_kwargs = mock_client.get_node.call_args.kwargs
        assert call_kwargs["fields"] == ["name", "currency"]
