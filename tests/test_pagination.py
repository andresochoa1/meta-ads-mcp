"""Pagination tests."""

from meta_ads_mcp.api.pagination import extract_pagination_info


class TestPagination:
    def test_extracts_next_url(self):
        response = {
            "data": [{"id": "1"}],
            "paging": {
                "cursors": {"after": "abc", "before": "xyz"},
                "next": "https://graph.facebook.com/v22.0/act_123/campaigns?after=abc",
            },
        }
        info = extract_pagination_info(response)
        assert info["has_next"] is True
        assert info["after_cursor"] == "abc"

    def test_blocks_ssrf_in_pagination(self):
        response = {
            "data": [],
            "paging": {
                "next": "https://evil.com/steal-data",
            },
        }
        info = extract_pagination_info(response)
        assert info["has_next"] is False
        assert info["next_url"] is None

    def test_handles_no_paging(self):
        response = {"data": [{"id": "1"}]}
        info = extract_pagination_info(response)
        assert info["has_next"] is False
        assert info["has_previous"] is False

    def test_handles_empty_response(self):
        info = extract_pagination_info({})
        assert info["has_next"] is False
