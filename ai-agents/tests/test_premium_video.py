"""Offline-only Wan 2.7 adapter tests. Never use real provider credentials."""
import os
from dataclasses import replace
import pytest
from ai_agents.premium_video import (
    AlibabaWanProvider, PremiumVideoDisabled, PremiumVideoProviderError,
    WanRequest, campaign_video_prompt, validate_private_frame,
)

SHOP = "123e4567-e89b-42d3-a456-426614174000"
ORIGIN = "https://jeearzffnjbvghwjjjrf.supabase.co"
FRAME = (ORIGIN + "/storage/v1/object/sign/retailgrowth-media/" +
         SHOP + "/uploads/first-frame.png?token=temporary-test-signature")
WAN = "https://ws123.ap-southeast-1.maas.aliyuncs.com"


def make_provider(recorder, *, enabled=False, limit=1):
    def mock(method, url, headers, payload):
        recorder.append((method, url, headers, payload))
        if method == "POST":
            return {"output": {"task_id": "abc-defghi-123456", "task_status": "PENDING"}}
        return {"output": {"task_id": "abc-defghi-123456", "task_status": "SUCCEEDED",
                           "video_url": "https://provider.example/private-token"}}
    return AlibabaWanProvider(workspace_origin=WAN, api_key="fake-test-only-credential",
                              region="singapore", enabled=enabled,
                              approved_max_usd=limit, supabase_origin=ORIGIN,
                              transport=mock)


def test_disabled_is_default_and_never_calls_paid_api(monkeypatch):
    for key in ("RETAIL_PREMIUM_VIDEO_ENABLED", "RETAIL_WAN_APPROVED_PER_JOB_USD"):
        monkeypatch.delenv(key, raising=False)
    provider = AlibabaWanProvider.from_environment()
    with pytest.raises(PremiumVideoDisabled):
        provider.submit(WanRequest("text", "New collection"))
    assert not provider.enabled


def test_enabled_still_requires_budget_credential_and_trusted_endpoint():
    calls = []
    for origin, key, limit in [(WAN, "", 1), (WAN, "fake-test-only-credential", 0),
                               ("https://attacker.example", "fake-test-only-credential", 1),
                               ("https://ws123.ap-southeast-1.maas.aliyuncs.com.evil.example",
                                "fake-test-only-credential", 1)]:
        provider = make_provider(calls, enabled=True, limit=limit)
        provider.origin = origin
        provider.api_key = key
        with pytest.raises(PremiumVideoDisabled):
            provider.submit(WanRequest("text", "Scenic promo"))
    assert calls == []


@pytest.mark.parametrize("duration", [0, 1, 16, True, 1.5])
def test_invalid_duration_rejected_before_network(duration):
    with pytest.raises(ValueError):
        WanRequest("text", "Scenic promo", duration_seconds=duration)


def test_text_to_video_payload_async_bounded_and_no_url_exposure():
    calls = []
    provider = make_provider(calls, enabled=True, limit=1)
    result = provider.submit(WanRequest("text", "Realistic boutique campaign",
                                        duration_seconds=10, resolution="720P"))
    assert result == {"provider": "alibaba-wan", "model": "wan2.7-t2v-2026-06-12",
                      "task_id": "abc-defghi-123456", "status": "PENDING"}
    method, url, headers, body = calls[0]
    assert method == "POST" and url.endswith("/video-synthesis")
    assert headers["X-DashScope-Async"] == "enable"
    assert body["parameters"]["duration"] == 10
    assert body["parameters"]["ratio"] == "9:16"
    assert body["parameters"]["watermark"] is True
    assert body["model"] == "wan2.7-t2v-2026-06-12"
    assert provider.estimated_usd(WanRequest("text", "clip", 10)) == 1.0
    assert provider.estimated_usd(WanRequest("text", "clip", 10, "1080P")) == 1.5


def test_cost_gate_blocks_before_provider_call():
    calls = []
    with pytest.raises(PremiumVideoDisabled, match="cost ceiling"):
        make_provider(calls, enabled=True, limit=0.7).submit(
            WanRequest("text", "Ad", duration_seconds=10))
    assert calls == []


def test_image_to_video_requires_shop_signed_path_and_omits_ratio():
    calls = []
    provider = make_provider(calls, enabled=True, limit=2)
    request = WanRequest("image", "Animate still image", 5, "1080P",
                         signed_first_frame=FRAME, shop_id=SHOP)
    result = provider.submit(request)
    assert result["model"] == "wan2.7-i2v-2026-04-25"
    body = calls[0][-1]
    assert body["input"]["media"] == [{"type": "first_frame", "url": FRAME}]
    assert "ratio" not in body["parameters"]


@pytest.mark.parametrize("url", [
    "http://jeearzffnjbvghwjjjrf.supabase.co/storage/v1/object/sign/retailgrowth-media/x",
    "https://attacker.example/storage/v1/object/sign/retailgrowth-media/x?token=x",
    ORIGIN + "/storage/v1/object/public/retailgrowth-media/" + SHOP + "/a.png",
    ORIGIN + "/storage/v1/object/sign/retailgrowth-media/" + SHOP + "/../../other.png?token=x",
    ORIGIN + "/storage/v1/object/sign/retailgrowth-media/" + SHOP + "/a.png",
    ORIGIN + "/storage/v1/object/sign/retailgrowth-media/other-shop/a.png?token=x",
    ORIGIN + "/storage/v1/object/sign/retailgrowth-media/" + SHOP + "/a%2Fb.png?token=x",
    ORIGIN.replace(".co", ".co.evil.example") + "/storage/v1/object/sign/retailgrowth-media/" + SHOP + "/a.png?token=x",
])
def test_private_frame_rejects_unsafe_paths(url):
    with pytest.raises(ValueError):
        validate_private_frame(url, shop_id=SHOP, supabase_origin=ORIGIN)


def test_no_external_video_url_released_from_poll():
    calls = []
    provider = make_provider(calls, enabled=True)
    assert provider.poll("abc-defghi-123456") == {
        "task_id": "abc-defghi-123456", "status": "SUCCEEDED"
    }
    assert len(calls) == 1 and calls[0][0] == "GET"
    with pytest.raises(ValueError):
        provider.poll("../private-resource")


def test_untrusted_provider_response_fail_closed():
    calls = []
    provider = make_provider(calls, enabled=True)
    provider.transport = lambda *args: {"output": {"task_id": "bad id"}}
    with pytest.raises(PremiumVideoProviderError):
        provider.submit(WanRequest("text", "Promo"))


def test_campaign_prompt_never_adds_unapproved_discount():
    draft = {"topic": "Autumn clothing", "instagram": {"reel": {"cta": "Explore today"}}}
    prompt = campaign_video_prompt(draft)
    assert "Autumn clothing" in prompt
    assert "Explore today" in prompt
    assert "20% off" not in prompt
    assert "20% off" in campaign_video_prompt(draft, approved_offer="20% off on coats")


def test_invalid_input_never_reaches_transport():
    calls = []
    provider = make_provider(calls, enabled=True, limit=3)
    with pytest.raises(ValueError):
        provider.submit(WanRequest("image", "Illustrate", signed_first_frame=FRAME,
                                   shop_id="another-shop"))
    assert calls == []


def test_private_poll_returns_vendor_link_only_inside_explicit_worker_method():
    calls = []
    provider = make_provider(calls, enabled=True)
    expected_url = ("https://dashscope-a717.oss-accelerate.aliyuncs.com/"
                    "clip.mp4?Expires=9999999999")

    def responder(method, url, headers, payload):
        calls.append((method, url))
        return {"output": {"task_id": "abc-defghi-123456",
                           "task_status": "SUCCEEDED",
                           "video_url": expected_url,
                           "orig_prompt": "should never leak"}}

    provider.transport = responder
    public = provider.poll("abc-defghi-123456")
    private = provider.poll_private("abc-defghi-123456")
    assert public == {"task_id": "abc-defghi-123456", "status": "SUCCEEDED"}
    assert private == {**public, "video_url": expected_url}
    assert "orig_prompt" not in private and "video_url" not in public
    assert [x[0] for x in calls] == ["GET", "GET"]


def test_private_poll_rejects_success_without_media_and_never_leaks_error_text():
    calls = []
    provider = make_provider(calls, enabled=True)
    provider.transport = lambda *args: {
        "output": {"task_id": "abc-defghi-123456", "task_status": "SUCCEEDED"}}
    with pytest.raises(PremiumVideoProviderError, match="missing private output"):
        provider.poll_private("abc-defghi-123456")
    provider.enabled = False
    with pytest.raises(PremiumVideoDisabled):
        provider.poll_private("abc-defghi-123456")
