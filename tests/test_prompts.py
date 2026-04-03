"""Tests for MCP prompt definitions and message generation."""

from meta_ads_mcp.prompts.analysis import PROMPTS, get_prompt_messages


class TestPromptsRegistry:
    """Test the PROMPTS dictionary structure."""

    def test_prompts_has_exactly_five_entries(self):
        assert len(PROMPTS) == 5

    def test_expected_prompt_names_present(self):
        expected = {
            "analyze-campaign-performance",
            "find-underperformers",
            "daily-monitoring-report",
            "budget-efficiency-check",
            "creative-fatigue-audit",
        }
        assert set(PROMPTS.keys()) == expected

    def test_each_prompt_has_required_fields(self):
        for name, prompt in PROMPTS.items():
            assert "name" in prompt, f"Prompt '{name}' missing 'name'"
            assert "description" in prompt, f"Prompt '{name}' missing 'description'"
            assert "arguments" in prompt, f"Prompt '{name}' missing 'arguments'"

    def test_each_prompt_name_matches_key(self):
        for key, prompt in PROMPTS.items():
            assert prompt["name"] == key

    def test_all_arguments_have_name_and_description(self):
        for prompt_name, prompt in PROMPTS.items():
            for arg in prompt["arguments"]:
                assert "name" in arg, f"Argument in '{prompt_name}' missing 'name'"
                assert "description" in arg, (
                    f"Argument '{arg.get('name')}' in '{prompt_name}' missing 'description'"
                )

    def test_all_descriptions_are_non_empty(self):
        for name, prompt in PROMPTS.items():
            assert len(prompt["description"]) > 0, f"Prompt '{name}' has empty description"


class TestGetPromptMessages:
    """Test prompt message generation."""

    def test_returns_messages_for_valid_prompt(self):
        messages = get_prompt_messages("analyze-campaign-performance", {"campaign_id": "123"})
        assert isinstance(messages, list)
        assert len(messages) >= 1
        assert messages[0]["role"] == "user"

    def test_campaign_id_included_in_message(self):
        messages = get_prompt_messages("analyze-campaign-performance", {"campaign_id": "99999"})
        text = messages[0]["content"]["text"]
        assert "99999" in text

    def test_returns_message_for_unknown_prompt(self):
        messages = get_prompt_messages("nonexistent-prompt", {})
        assert isinstance(messages, list)
        assert len(messages) >= 1
        text = messages[0]["content"]["text"]
        assert "Unknown prompt" in text

    def test_all_known_prompts_generate_messages(self):
        for prompt_name in PROMPTS:
            messages = get_prompt_messages(prompt_name, {"account_id": "act_123"})
            assert isinstance(messages, list)
            assert len(messages) >= 1
            assert messages[0]["role"] == "user"

    def test_find_underperformers_includes_targets(self):
        messages = get_prompt_messages(
            "find-underperformers",
            {"account_id": "act_123", "cpa_target": "5.00", "roas_target": "3.0"},
        )
        text = messages[0]["content"]["text"]
        assert "5.00" in text
        assert "3.0" in text

    def test_creative_fatigue_includes_days(self):
        messages = get_prompt_messages(
            "creative-fatigue-audit",
            {"account_id": "act_123", "days": "30"},
        )
        text = messages[0]["content"]["text"]
        assert "30" in text
