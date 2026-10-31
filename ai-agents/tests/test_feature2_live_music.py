"""Official live-source endpoint and authenticated recommendation, mocked transport."""
import json
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit
from ai_agents.feature2_live_music import (
    discover_music, discover_retailer_music, parse_music_popular,
    AudioDiscoveryUnavailable, _get,
)
import pytest

NOW = datetime(2026, 10, 28, 10, tzinfo=timezone.utc)
ENV = {"RETAIL_FEATURE2_MUSIC_YT_ENABLED": "true",
       "RETAIL_FEATURE2_MUSIC_YT_API_KEY": "TEST_VALID_KEY_1234567890"}
SHOP = "11111111-1111-4111-8111-111111111111"


def response(category="10", title="Elegant Fashion Festive Music",
             dt="2026-10-26T12:00:00Z", ident="AbCdEf12345"):
    return json.dumps({"items": [{"id": ident, "snippet": {
        "categoryId": category, "title": title,
        "channelTitle": "Music Studio", "publishedAt": dt},
        "statistics": {"viewCount": "987654321"}}]}).encode()


def test_disabled_or_missing_server_key_never_calls_provider():
    seen = []
    fetch = lambda url, **_: seen.append(url) or response()
    assert discover_music(now=NOW, environ={}, get=fetch)["status"] == "DISABLED"
    assert discover_music(now=NOW, environ={
        "RETAIL_FEATURE2_MUSIC_YT_ENABLED": "true"}, get=fetch)["status"] == "NO_SERVER_API_KEY"
    assert seen == []


def test_authorized_live_chart_creates_unlicensed_shortlist_only():
    urls = []
    def fake_fetch(url, **kwargs):
        parsed = urlsplit(url)
        assert (parsed.scheme, parsed.hostname, parsed.path) == (
            "https", "www.googleapis.com", "/youtube/v3/videos")
        query = parse_qs(parsed.query)
        assert query["videoCategoryId"] == ["10"]
        assert query["regionCode"] == ["IN"]
        urls.append(url)
        return response()
    seen_shops = []
    def allowed(shop):
        seen_shops.append(shop)
        return shop == SHOP
    result = discover_retailer_music(
        shop_id=SHOP, creative_brief="Fashion festive kurti boutique Reel",
        duration_seconds=30, now=NOW, environ=ENV, get=fake_fetch,
        authorized_shop_reader=allowed)
    assert result["discovery_status"] == "OK"
    assert len(urls) == 1 and len(seen_shops) == 2
    assert result["recommendations"][0]["source"] == "youtube_music_video"
    assert result["recommendations"][0]["rights_status"] == "UNVERIFIED"
    assert result["recommendations"][0]["can_attach_to_export"] is False
    assert result["can_publish"] is False and result["can_mix_audio"] is False


def test_denied_or_revoked_membership_has_no_media_leak():
    seen = []
    with pytest.raises(PermissionError):
        discover_retailer_music(shop_id=SHOP,creative_brief="Kurti styling Reel",
            duration_seconds=30,now=NOW,environ=ENV,
            get=lambda *a, **kw: seen.append(1) or response(),
            authorized_shop_reader=lambda _:False)
    assert seen == []
    times = []
    def revoked(_):
        times.append(1)
        return len(times) == 1
    with pytest.raises(PermissionError,match="revoked"):
        discover_retailer_music(shop_id=SHOP,creative_brief="Kurti styling Reel",
            duration_seconds=30,now=NOW,environ=ENV,
            get=lambda *a,**kw: response(),authorized_shop_reader=revoked)


@pytest.mark.parametrize("payload", [
    b'{"items":{}}', b'not json',
    response(category="17"), response(title="<script>BAD</script>"),
    response(ident="bad"),response(dt="2099-01-01T00:00:00Z"),
])
def test_malformed_or_out_of_category_not_promoted_to_viral(payload):
    collected=discover_music(now=NOW,environ=ENV,get=lambda *a,**kw:payload)
    assert collected["candidates"]==[]
    assert collected["status"] in ("EMPTY","UNAVAILABLE")


def test_bad_provider_and_api_host_leak_are_fail_closed():
    assert discover_music(now=NOW,environ=ENV,
       get=lambda *a,**kw: (_ for _ in ()).throw(TimeoutError("secret")))["status"]=="UNAVAILABLE"
    with pytest.raises((AudioDiscoveryUnavailable,ValueError)):
        _get("https://www.googleapis.com.evil.example/youtube/v3/videos?key=TEST_VALID_KEY_1234567890")
    with pytest.raises((AudioDiscoveryUnavailable,ValueError)):
        _get("https://evil.example/youtube/v3/videos?key=TEST_VALID_KEY_1234567890")
