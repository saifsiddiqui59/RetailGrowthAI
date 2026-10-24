"""Provider contract tests: strictly mocked, no internet, no credentials."""
import importlib.util
from pathlib import Path
import sys
import pytest

path = Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api" / "social_providers.py"
spec = importlib.util.spec_from_file_location("social_providers", path)
social = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = social
spec.loader.exec_module(social)


def test_linkedin_uses_current_versioned_posts_api():
    r = social.linkedin_text_request(author_urn="urn:li:organization:99", token="opaque",
        commentary="Approved post", api_version="202609")
    assert r.url == "https://api.linkedin.com/rest/posts"
    assert r.headers["Linkedin-Version"] == "202609"
    assert social.linkedin_receipt({"x-restli-id": "urn:li:share:123"}).remote_id == "urn:li:share:123"
    with pytest.raises(social.ProviderRejected):
        social.linkedin_text_request(author_urn="not-an-urn", token="x", commentary="x", api_version="202609")


def test_facebook_page_only_and_ig_reel_two_step():
    fb = social.facebook_page_request(page_id="123", page_token="opaque", text="Reviewed",
                                      graph_version="v24.0")
    assert fb.url.endswith("/123/feed")
    url = "https://example.supabase.co/storage/v1/object/sign/retailgrowth-social-exports/31000000-0000-4000-8000-000000000001/video/62000000-0000-4000-8000-000000000001/1/abababababababababababababababababababababababababababababababab.mp4?token=VALIDSIGNEDTOKEN123456789012345"
    ig = social.instagram_reel_container_request(ig_user_id="123", token="opaque",
        video_url=url, caption="Approved", supabase_origin="https://example.supabase.co",
        graph_version="v24.0")
    assert ig.body["media_type"] == "REELS"
    with pytest.raises(social.ProviderRejected):
        social.instagram_reel_container_request(ig_user_id="123", token="opaque",
            video_url="https://bad.example/video.mp4", caption="x",
            supabase_origin="https://example.supabase.co", graph_version="v24.0")
    with pytest.raises(social.ProviderRejected):
        social.instagram_publish_request(ig_user_id="123", token="opaque", container_id="123",
            container_status="IN_PROGRESS", graph_version="v24.0")
    assert social.instagram_publish_request(ig_user_id="123", token="opaque", container_id="123",
        container_status="FINISHED", graph_version="v24.0").url.endswith("/media_publish")


def test_youtube_request_initializes_private_resumable_only():
    r = social.youtube_resumable_init_request(token="opaque", title="Short",
        description="Reviewed", size_bytes=2048)
    assert "uploadType=resumable" in r.url
    assert r.body["status"]["privacyStatus"] == "private"
    with pytest.raises(social.ProviderRejected):
        social.youtube_upload_location("https://attacker.example/upload/s")
    assert social.youtube_upload_location(
        "https://www.googleapis.com/upload/youtube/v3/videos?upload_id=opaque")


def test_provider_request_repr_cannot_leak_token_or_signed_media():
    r = social.instagram_reel_container_request(
        ig_user_id="123", token="VERY-SECRET-BEARER", 
        video_url="https://example.supabase.co/storage/v1/object/sign/retailgrowth-social-exports/31000000-0000-4000-8000-000000000001/video/62000000-0000-4000-8000-000000000001/1/abababababababababababababababababababababababababababababababab.mp4?token=PRIVATE-SIGNED-TOKEN-1234567890",
        caption="approved", supabase_origin="https://example.supabase.co", graph_version="v24.0")
    rendered = repr(r)
    assert "VERY-SECRET-BEARER" not in rendered
    assert "PRIVATE-SIGNED" not in rendered
    assert "headers=" not in rendered and "body=" not in rendered
