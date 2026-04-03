"""Tests for MetaAPIClient._prepare_params()."""

import json

from meta_ads_mcp.api.client import MetaAPIClient


class TestPrepareParams:
    """Test parameter preparation for Meta Graph API requests."""

    def test_fields_list_gets_comma_joined(self, mock_config):
        client = MetaAPIClient(mock_config)
        result = client._prepare_params({"fields": ["name", "id", "status"]})
        assert result["fields"] == "name,id,status"

    def test_breakdowns_list_gets_comma_joined(self, mock_config):
        client = MetaAPIClient(mock_config)
        result = client._prepare_params({"breakdowns": ["age", "gender"]})
        assert result["breakdowns"] == "age,gender"

    def test_action_breakdowns_list_gets_comma_joined(self, mock_config):
        client = MetaAPIClient(mock_config)
        result = client._prepare_params({"action_breakdowns": ["action_type"]})
        assert result["action_breakdowns"] == "action_type"

    def test_filtering_dict_gets_json_encoded(self, mock_config):
        client = MetaAPIClient(mock_config)
        filtering = [{"field": "spend", "operator": "GREATER_THAN", "value": 0}]
        result = client._prepare_params({"filtering": filtering})
        assert result["filtering"] == json.dumps(filtering)

    def test_time_range_dict_gets_json_encoded(self, mock_config):
        client = MetaAPIClient(mock_config)
        time_range = {"since": "2026-01-01", "until": "2026-01-31"}
        result = client._prepare_params({"time_range": time_range})
        assert result["time_range"] == json.dumps(time_range)

    def test_effective_status_list_gets_json_encoded(self, mock_config):
        client = MetaAPIClient(mock_config)
        statuses = ["ACTIVE", "PAUSED"]
        result = client._prepare_params({"effective_status": statuses})
        assert result["effective_status"] == json.dumps(statuses)

    def test_boolean_true_becomes_string(self, mock_config):
        client = MetaAPIClient(mock_config)
        result = client._prepare_params({"include_deleted": True})
        assert result["include_deleted"] == "true"

    def test_boolean_false_becomes_string(self, mock_config):
        client = MetaAPIClient(mock_config)
        result = client._prepare_params({"include_deleted": False})
        assert result["include_deleted"] == "false"

    def test_none_values_are_skipped(self, mock_config):
        client = MetaAPIClient(mock_config)
        result = client._prepare_params({"fields": None, "limit": 10})
        assert "fields" not in result
        assert result["limit"] == 10

    def test_empty_params_returns_empty_dict(self, mock_config):
        client = MetaAPIClient(mock_config)
        result = client._prepare_params({})
        assert result == {}

    def test_plain_values_pass_through(self, mock_config):
        client = MetaAPIClient(mock_config)
        result = client._prepare_params({"limit": 25, "date_preset": "last_7d"})
        assert result["limit"] == 25
        assert result["date_preset"] == "last_7d"

    def test_mixed_params(self, mock_config):
        client = MetaAPIClient(mock_config)
        result = client._prepare_params(
            {
                "fields": ["name", "id"],
                "filtering": [{"field": "spend", "operator": "GREATER_THAN", "value": 0}],
                "include_deleted": True,
                "limit": 50,
                "date_preset": None,
            }
        )
        assert result["fields"] == "name,id"
        assert result["filtering"] == json.dumps(
            [{"field": "spend", "operator": "GREATER_THAN", "value": 0}]
        )
        assert result["include_deleted"] == "true"
        assert result["limit"] == 50
        assert "date_preset" not in result
