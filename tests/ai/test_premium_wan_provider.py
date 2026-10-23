"""Offline/no-network Part 3 provider safety and Wan protocol tests."""
import pytest

from ai_agents.premium_video import (
    AlibabaWanProvider, WanRequest, PremiumVideoDisabled,
    PremiumVideoProviderError, campaign_video_prompt, validate_private_frame,
)

SHOP = "16b9017c-8f02-4a80-b312-5c924213d15a"
SUPABASE = "https://jeearzffnjbvghwjjjrf.supabase.co"
URL = (SUPABASE + "/storage/v1/object/sign/retailgrowth-media/" +
       SHOP + "/uploads/asset.png?token=server-only")


def provider(**kwargs):
    defaults = dict(
        enabled=True, workspace_origin="https://work123.ap-southeast-1.maas.aliyuncs.com",
        api_key="not-a-real-api-key-1234", approved_max_usd=5,
        supabase_origin=SUPABASE,
    )
    defaults.update(kwargs)
    return AlibabaWanProvider(**defaults)


def test_fail_closed_default_and_missing_pricing_gate():
    safe = WanRequest("text", "A video", 5)
    with pytest.raises(PremiumVideoDisabled):
        AlibabaWanProvider().submit(safe)
    with pytest.raises(PremiumVideoDisabled):
        provider(approved_max_usd=0).submit(safe)


def test_rejects_endpoint_ssrf_even_with_key_and_gate():
    for origin in ("http://work123.ap-southeast-1.maas.aliyuncs.com",
                   "https://work123.ap-southeast-1.maas.aliyuncs.com.evil.com",
                   "https://127.0.0.1", "https://work123.ap-southeast-1.maas.aliyuncs.com/path"):
        with pytest.raises(PremiumVideoDisabled):
            provider(workspace_origin=origin).submit(WanRequest("text", "Sample"))


def test_request_types_and_cost_bounds():
    for options in (dict(mode="text", prompt="x", duration_seconds=30),
                    dict(mode="text", prompt="x", duration_seconds=True),
                    dict(mode="text", prompt="x", resolution="4K"),
                    dict(mode="text", prompt="x", ratio="90:10"),
                    dict(mode="image", prompt="x", signed_first_frame=URL)):
        with pytest.raises(ValueError):
            WanRequest(**options)
    with pytest.raises(PremiumVideoDisabled):
        provider(approved_max_usd=.40).submit(WanRequest("text", "Hello", 5))
    assert provider().estimated_usd(WanRequest("text", "Hello", 5)) == .5
    assert provider().estimated_usd(WanRequest("text", "Hello", 10, "1080P")) == 1.5


def test_wan_text_submit_is_async_and_no_unapproved_request():
    calls = []
    def transport(method, url, headers, payload):
        calls.append((method, url, headers, payload))
        return {"output": {"task_id": "task00000042", "task_status": "PENDING"}}

    p = provider(transport=transport)
    task = p.submit(WanRequest("text", "Boutique launch", duration_seconds=5))
    assert task == {"provider": "alibaba-wan", "model": "wan2.7-t2v-2026-06-12",
                    "task_id": "task00000042", "status": "PENDING"}
    method, endpoint, headers, payload = calls[0]
    assert method == "POST" and endpoint.endswith("/video-synthesis")
    assert headers["X-DashScope-Async"] == "enable"
    assert payload["parameters"]["ratio"] == "9:16"
    assert payload["parameters"]["watermark"] is True
    assert payload["input"] == {"prompt": "Boutique launch"}


def test_wan_image_uses_signed_owned_private_frame_only():
    calls = []
    def transport(method, url, headers, payload):
        calls.append(payload)
        return {"output": {"task_id": "task00000123"}}
    spec = WanRequest("image", "Motion", shop_id=SHOP, signed_first_frame=URL)
    assert provider(transport=transport).submit(spec)["model"] == "wan2.7-i2v-2026-04-25"
    assert calls[0]["input"]["media"] == [{"type": "first_frame", "url": URL}]
    assert "ratio" not in calls[0]["parameters"]

    for bad in (
        "https://evil.com/storage/v1/object/sign/retailgrowth-media/" + SHOP + "/a?token=x",
        SUPABASE + "/storage/v1/object/public/retailgrowth-media/" + SHOP + "/a",
        SUPABASE + "/storage/v1/object/sign/retailgrowth-media/other/a?token=x",
        SUPABASE + "/storage/v1/object/sign/retailgrowth-media/" + SHOP + "/a",
        SUPABASE + "/storage/v1/object/sign/retailgrowth-media/" + SHOP + "/../a?token=x",
    ):
        with pytest.raises(ValueError):
            validate_private_frame(bad, shop_id=SHOP, supabase_origin=SUPABASE)


def test_poll_returns_no_externally_signed_video_download_url():
    def transport(method, url, headers, payload):
        assert method == "GET" and url.endswith("/api/v1/tasks/task00000042")
        return {"output": {"task_id": "task00000042",
                            "task_status": "SUCCEEDED",
                            "video_url": "https://untrusted.test/download.mp4?secret=abc"}}
    status = provider(transport=transport).poll("task00000042")
    assert status == {"task_id": "task00000042", "status": "SUCCEEDED"}
    assert "video_url" not in status


def test_invalid_task_ids_and_provider_responses_are_denied():
    with pytest.raises(ValueError):
        provider(transport=lambda *args: {}).poll("../private")
    with pytest.raises(PremiumVideoProviderError):
        provider(transport=lambda *args: {"output": {"task_status": "PENDING"}}).submit(
            WanRequest("text", "Sample"))
    with pytest.raises(PremiumVideoProviderError):
        provider(transport=lambda *args: {"output": {"task_id": "task00000042",
                                                      "task_status": "UNKNOWN_BAD"}}).poll(
            "task00000042")


def test_prompt_uses_reviewed_claims_only():
    day = {"topic": "Day 1 - fresh arrivals", "instagram": {"reel": {"cta": "Visit us"}}}
    result = campaign_video_prompt(day)
    assert "fresh arrivals" in result and "Visit us" in result
    assert "20% off" not in result
    assert "20% off" in campaign_video_prompt(day, approved_offer="20% off")
