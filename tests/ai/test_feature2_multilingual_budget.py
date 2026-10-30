"""Feature2 AI must reserve the serialized UTF-8 request, not Python chars.

No real paid calls: only local fake Azure chat-completion transport.
"""
import json

from ai_agents.feature2_llm import AzureFeature2PromptLLM
from ai_agents.feature2_ai_writer import AzureFeature2ContentLLM


def prompt_reservation(text):
    observed = {"reservations": [], "bodies": []}
    def fake_transport(url, headers, body):
        observed["bodies"].append(body)
        return {
            "choices": [{"finish_reason": "stop",
                         "message": {"content": json.dumps({
                             "improved_prompt":
                               "Retailer request (preserve its intent verbatim): Hello. "
                               "Write distinct reviewed posts."
                         })}}],
            "usage": {"prompt_tokens": 8, "completion_tokens": 10},
        }
    llm = AzureFeature2PromptLLM(
        endpoint="https://test.openai.azure.com", deployment="test-model",
        api_key="FAKE_MODEL_KEY_ONLY_FOR_TEST",
        input_usd_per_million=25, output_usd_per_million=25,
        approved_max_cost_usd=0.24, reserve_cost=lambda cost: observed["reservations"].append(cost) or "reserved",
        transport=fake_transport,
    )
    llm("Retailer request (preserve its intent verbatim): Hello.\n" + text)
    assert len(observed["reservations"]) == len(observed["bodies"]) == 1
    body = observed["bodies"][0]
    required_upper = (len(body) + 256 + 550) * 25 / 1_000_000
    assert observed["reservations"][0] >= required_upper - 1e-12
    return observed["reservations"][0]


def content_reservation(text):
    observed = {"reservations": [], "bodies": []}
    generated = {"days": [{
        "topic": "One actionable wardrobe idea",
        "hook": "Think about an outfit",
        "linkedin_post": "A thoughtful approach to dressing for work.",
        "instagram_caption": "One practical styling idea for a regular day.",
        "facebook_post": "Discuss a practical outfit detail with your community.",
        "youtube_title": "Practical outfit styling",
        "youtube_description": "Explore one useful styling principle.",
        "poster_headline": "One daily style idea",
        "poster_subheadline": "Consider what works for your routine",
        "scene_scripts": [
            "Introduce the authorized clothing idea.",
            "Show only an already approved product photo.",
            "Close with a question to the viewer.",
        ],
    }]}
    def fake_transport(url, headers, body):
        observed["bodies"].append(body)
        return {
            "choices": [{"finish_reason": "stop",
                         "message": {"content": json.dumps(generated)}}],
            "usage": {"prompt_tokens": 8, "completion_tokens": 15},
        }
    llm = AzureFeature2ContentLLM(
        endpoint="https://test.openai.azure.com", deployment="test-model",
        api_key="FAKE_MODEL_KEY_ONLY_FOR_TEST",
        input_usd_per_million=25, output_usd_per_million=25,
        approved_max_cost_usd=0.24, reserve_cost=lambda cost: observed["reservations"].append(cost) or "reserved",
        transport=fake_transport,
    )
    result = llm("Authorized business objective and style: " + text, 1)
    assert result == generated
    assert len(observed["bodies"]) == len(observed["reservations"]) == 1
    required_upper = (len(observed["bodies"][0]) + 256 + 4000) * 25 / 1_000_000
    assert observed["reservations"][0] >= required_upper - 1e-12
    return observed["reservations"][0]


def test_prompt_multilingual_and_json_escaping_have_higher_reserved_budget():
    baseline = prompt_reservation("A" * 100)
    hindi = prompt_reservation("क" * 100)
    escaped = prompt_reservation("\\" * 100)
    assert hindi > baseline
    assert escaped > baseline


def test_writer_multilingual_and_escaped_json_charge_reservation():
    baseline = content_reservation("A" * 100)
    hindi = content_reservation("क" * 100)
    escaped = content_reservation("\\" * 100)
    assert hindi > baseline
    assert escaped > baseline
