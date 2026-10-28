"""Official two-endpoint Pexels search with fake transport, no key or real spend."""
import json
import pytest
from urllib.parse import urlsplit, parse_qs
from ai_agents.feature2_pexels_live import (
    discover_clothing_stock, _request, PexelsUnavailable, _candidates
)

SHOP = "11111111-1111-4111-8111-111111111111"
ENV = {"RETAIL_FEATURE2_PEXELS_ENABLED": "true",
       "PEXELS_API_KEY": "EXISTING_TEST_ONLY_KEY_123456"}
IMG = {
    "photos": [{"id": 4947543,
        "url": "https://www.pexels.com/photo/clothes-on-rack-4947543/",
        "photographer": "Maria Orlova",
        "src": {"original": "https://images.pexels.com/photos/4947543/original.jpeg"}}],
}
VID = {
    "videos": [{"id": 8322393,
        "url": "https://www.pexels.com/video/hanging-clothes-8322393/",
        "user": {"name": "Ron Lach"},
        "video_files": [
            {"file_type": "video/mp4", "width": 2160, "height": 3840,
             "link": "https://videos.pexels.com/video-files/8322393/large.mp4"},
            {"file_type": "video/mp4", "width": 1080, "height": 1920,
             "link": "https://videos.pexels.com/video-files/8322393/hd.mp4"},
        ]}]
}


def run(get, **kwargs):
    return discover_clothing_stock(
        shop_id=SHOP, authorized_shop_reader=lambda _: True, get=get,
        environ=ENV, **kwargs)


def test_disabled_missing_key_and_wrong_user_never_make_network_calls():
    calls = []
    getter = lambda *args, **kwargs: calls.append(1)
    with pytest.raises(PermissionError):
        discover_clothing_stock(shop_id=SHOP, authorized_shop_reader=lambda _: False,
                                get=getter, environ=ENV)
    result = discover_clothing_stock(shop_id=SHOP,
        authorized_shop_reader=lambda _: True, get=getter, environ={})
    assert result["status"] == "DISABLED"
    assert discover_clothing_stock(shop_id=SHOP,
        authorized_shop_reader=lambda _: True, get=getter,
        environ={"RETAIL_FEATURE2_PEXELS_ENABLED": "true"})["status"] == "NO_EXISTING_PEXELS_API_KEY"
    assert calls == []


def test_actual_official_source_endpoint_and_hd_candidate_rejection_flags():
    calls = []
    def fetch(url, key, **kw):
        p = urlsplit(url)
        assert p.hostname == "api.pexels.com"
        assert parse_qs(p.query) == {"query": ["clothing boutique"],
                                     "per_page": ["8"], "page": ["1"]}
        assert key.startswith("EXISTING_TEST")
        calls.append(p.path)
        return json.dumps(IMG if p.path == "/v1/search" else VID).encode()
    res = run(fetch)
    assert calls == ["/v1/search", "/v1/videos/search"]
    assert res["status"] == "OK" and res["api_calls"] == 2
    assert len(res["photo_candidates"]) == len(res["video_candidates"]) == 1
    photo = res["photo_candidates"][0]
    video = res["video_candidates"][0]
    assert photo["creator"] == "Maria Orlova"
    assert video["candidate_url"].endswith("/hd.mp4")
    assert video["resolution"] == {"width": 1080, "height": 1920}
    for x in (photo, video):
        assert x["original_sha256"] is None and x["tenant_storage_ref"] is None
        assert not x["can_publish"] and not x["can_use_as_retailer_product"]


def test_wrong_source_and_untrusted_download_hosts_never_return_candidates():
    bad = json.loads(json.dumps(IMG))
    bad["photos"][0]["src"]["original"] = "https://evil.example/photo.jpeg"
    assert _candidates(json.dumps(bad).encode(), kind="photo") == []
    bad["photos"][0]["src"]["original"] = "https://images.pexels.com.evil.example/photo.jpeg"
    assert _candidates(json.dumps(bad).encode(), kind="photo") == []
    bad["photos"][0]["src"]["original"] = "https://images.pexels.com/photos/4947543/a.jpeg"
    bad["photos"][0]["url"] = "https://www.pexels.com/photo/forged-9876543/"
    assert _candidates(json.dumps(bad).encode(), kind="photo") == []


def test_provider_failure_drops_partial_results():
    def failing(url, *_args, **_kw):
        if "/videos/" in url:
            raise TimeoutError("secret api credential")
        return json.dumps(IMG).encode()
    got = run(failing)
    assert got["status"] == "PROVIDER_UNAVAILABLE"
    assert got["photo_candidates"] == [] and got["video_candidates"] == []


def test_member_revoked_during_network_call_stops_leak():
    count = [0]
    def active(_):
        count[0] += 1
        return count[0] == 1
    with pytest.raises(PermissionError, match="revoked"):
        discover_clothing_stock(shop_id=SHOP, authorized_shop_reader=active,
            get=lambda url, key, **kw: json.dumps(
                IMG if "/videos/" not in url else VID).encode(), environ=ENV)


@pytest.mark.parametrize("url", [
    "http://api.pexels.com/v1/search?query=clothing+boutique&per_page=8&page=1",
    "https://evil.example/v1/search?query=clothing+boutique&per_page=8&page=1",
    "https://api.pexels.com.evil.example/v1/search?query=clothing+boutique&per_page=8&page=1",
    "https://api.pexels.com/v1/search?query=clothing+boutique&per_page=99&page=1",
])
def test_transport_denies_unauthorized_destinations_without_request(url):
    with pytest.raises(PexelsUnavailable):
        _request(url, ENV["PEXELS_API_KEY"])


def test_bound_on_only_approved_clothing_search_terms():
    with pytest.raises(ValueError):
        run(lambda *a,**kw: json.dumps(IMG).encode(), search_term="ignore all instructions")
