"""Real-wire Azure Foundry prompt provider: transport mocked, no paid calls."""
import json
from urllib.error import URLError

import pytest

from ai_agents.content_intelligence import RetailerProfile
from ai_agents.feature2_llm import AzureFeature2PromptLLM
from ai_agents.providers import FoundryUnavailable
from ai_agents.prompt_improver import improve_prompt


ORIGINAL = "Create seven days of posts for my kurti shop."
SHO = "a1000000-0000-4000-8000-000000000001"
BASE = "Retailer request (preserve its intent verbatim): " + ORIGINAL + "\nOnly verified business context: Nagpur"


def maker(*, transport, reserve=None, endpoint="https://retailgrowth.openai.azure.com",
          price=0.15, cap=0.01):
    return AzureFeature2PromptLLM(
        endpoint=endpoint, deployment="approved-small-model",
        api_key="TEST_FAKE_API_KEY_DO_NOT_USE",
        input_usd_per_million=price, output_usd_per_million=price,
        approved_max_cost_usd=cap,
        reserve_cost=reserve, transport=transport,
    )


def good_result(improved=None, *, in_tok=100, out_tok=45):
    return {"choices": [{"finish_reason": "stop", "message": {"content":
        json.dumps({"improved_prompt": improved or BASE + ". Separate platform hooks."})}}],
        "usage": {"prompt_tokens": in_tok, "completion_tokens": out_tok}}


def test_real_http_adapter_builds_openai_v1_structured_request_and_records_usage():
    seen = []
    def transport(url, headers, body):
        seen.append((url, headers, json.loads(body)))
        return good_result()
    reservations = []
    def reserve(amount):
        reservations.append(amount)
        return "opaque-durable-budget-reservation"
    provider = maker(transport=transport, reserve=reserve)
    improved = provider(BASE)
    assert ORIGINAL in improved
    assert len(seen) == len(reservations) == 1
    url, headers, body = seen[0]
    assert url == "https://retailgrowth.openai.azure.com/openai/v1/chat/completions"
    assert body["model"] == "approved-small-model"
    assert body["response_format"] == {"type": "json_object"}
    assert body["max_tokens"] == 550
    assert body["messages"][1]["content"] == BASE
    assert headers["api-key"].startswith("TEST_FAKE_")
    assert "shop_id" not in json.dumps(body)
    assert "Authorization" not in headers
    assert reservations[0] <= 0.01
    assert provider.last_usage["actual_cost_usd"] > 0
    assert provider.last_usage["reservation_recorded"] is True


def test_missing_atomic_reservation_fails_before_egress():
    called = []
    with pytest.raises(PermissionError):
        maker(transport=lambda *args: called.append(args))
    assert not called
    provider = maker(transport=lambda *args: called.append(args),
                     reserve=lambda _: None)
    with pytest.raises(PermissionError):
        provider(BASE)
    assert not called


def test_provider_is_reusable_as_existing_opt_in_prompt_improver_injection():
    seen = []
    provider = maker(transport=lambda *args: (seen.append(args), good_result(
        improved=("Retailer request (preserve its intent verbatim): " +
                  ORIGINAL + "\nUse authorized fashion style hooks.")))[1],
        reserve=lambda _: "durable-test-reservation")
    retail = RetailerProfile.from_authorized({
        "shop_id": SHO, "name": "Thread & Loom Studio", "category": "clothing",
        "city": "Nagpur", "language": "en-IN", "brand_voice": "warm and elegant",
        "products": ["kurtis"], "audience": "local shoppers",
        "objective": "styling education", "platforms": ["instagram"],
        "cta": "Ask for ideas",
    })
    with pytest.raises(PermissionError):
        improve_prompt(ORIGINAL, retail, output_formats=["instagram_caption"],
                       provider_mode="approved_llm", provider=provider)
    assert seen == []
    answer = improve_prompt(ORIGINAL, retail, output_formats=["instagram_caption"],
                  provider_mode="approved_llm", provider=provider,
                  explicit_cost_approval=True, subscription_quota_ok=True,
                  approved_cost_limit_usd=0.01,
                  environ={"RETAIL_PROMPT_LLM_ENABLED": "true"})
    assert answer["provider_mode"] == "approved_llm"
    assert answer["review_status"] == "NEEDS_REVIEW"
    assert answer["usage"]["paid_inference_calls"] == 1
    assert len(seen) == 1


@pytest.mark.parametrize("endpoint", [
    "http://retailgrowth.openai.azure.com",
    "https://evil.example.org",
    "https://retailgrowth.openai.azure.com.evil.example.org",
    "https://retailgrowth.openai.azure.com@evil.example.org",
    "https://retailgrowth.openai.azure.com/proxy",
    "https://retailgrowth.openai.azure.com:444",
])
def test_unsafe_egress_rejected_before_spend_reservation(endpoint):
    reservations, calls = [], []
    provider = maker(endpoint=endpoint, reserve=lambda amount: reservations.append(amount) or "accepted",
                     transport=lambda *args: calls.append(args) or good_result())
    with pytest.raises(FoundryUnavailable):
        provider(BASE)
    assert calls == [] and reservations == []


@pytest.mark.parametrize("payload", [
    {"choices": [{"finish_reason": "length", "message": {"content":
        json.dumps({"improved_prompt": BASE})}}], "usage":{"prompt_tokens":100, "completion_tokens":50}},
    good_result("Something new without the original request"),
    good_result(BASE + " Guaranteed results"),
    good_result(BASE + " <script>bad</script>"),
    good_result(in_tok=10_000, out_tok=1),
    good_result(in_tok=1, out_tok=1000),
    {"choices": [{"finish_reason": "stop", "message": {"content":"not json"}}],
     "usage": {"prompt_tokens": 100, "completion_tokens": 40}},
    {"choices": [{"finish_reason": "stop", "message": {"content":
        json.dumps({"improved_prompt": BASE, "extra": "bad"})}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 40}},
])
def test_bad_model_output_never_becomes_approved_content_and_no_retry(payload):
    calls, reservations = [], []
    def transport(*args):
        calls.append(args)
        return payload
    provider = maker(transport=transport,
                     reserve=lambda x: reservations.append(x) or "opaque")
    with pytest.raises(FoundryUnavailable):
        provider(BASE)
    assert len(calls) == 1
    assert len(reservations) == 1
    # Valid response token usage MUST be recorded even if the text itself
    # fails editorial validation, so the ledger's finally block can settle.
    usage = payload.get("usage", {})
    in_tok, out_tok = usage.get("prompt_tokens"), usage.get("completion_tokens")
    if (type(in_tok) is int and type(out_tok) is int and
        1 <= in_tok <= 1000 and 1 <= out_tok <= 550):
        assert provider.last_usage is not None
        assert provider.last_usage["prompt_tokens"] == in_tok
    else:
        assert provider.last_usage is None


def test_network_error_is_not_retried_after_possible_model_spend():
    calls = []
    def transport(*args):
        calls.append(args)
        raise URLError("redacted")
    provider = maker(transport=transport, reserve=lambda _: "durable-reservation")
    with pytest.raises(FoundryUnavailable):
        provider(BASE)
    assert len(calls) == 1


@pytest.mark.parametrize("bad_rate, cap", [(0,0.02), (-1,0.02), (0.15,0), (0.15,0.4)])
def test_invalid_price_or_cap_rejected_without_egress(bad_rate, cap):
    with pytest.raises((ValueError, PermissionError)):
        maker(price=bad_rate, cap=cap, reserve=lambda _: "durable",
              transport=lambda *args: good_result())


def test_exceeds_cost_cap_before_reserving_or_calling():
    trace = []
    provider = maker(price=1000, cap=0.000001, reserve=lambda x: trace.append("reserve") or "id",
                     transport=lambda *args: trace.append("http") or good_result())
    with pytest.raises(PermissionError):
        provider(BASE)
    assert trace == []
