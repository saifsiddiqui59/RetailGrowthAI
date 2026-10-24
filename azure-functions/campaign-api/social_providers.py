"""Part 2: official provider request contracts; no network traffic on import.

A publishing worker must check shop authorization, user approval, subscription
entitlement, connected account scopes, and a durable idempotency record BEFORE
calling these helpers. Ambiguous provider writes must not be blindly retried.
"""
from dataclasses import dataclass, field
from urllib.parse import urlsplit
import re


class ProviderRejected(ValueError):
    """Safe validation failure, never includes provider responses or secrets."""


@dataclass(frozen=True)
class ProviderRequest:
    method: str
    url: str
    headers: dict = field(repr=False)
    body: dict = field(repr=False)


@dataclass(frozen=True)
class ProviderReceipt:
    provider: str
    remote_id: str
    status: str


def _required(value, maximum=5000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ProviderRejected("invalid required provider field")
    return value


def _token(value):
    return _required(value, 8192)


def _id(value, *, urn=False):
    pattern = r"[A-Za-z0-9_:\-]{1,160}" if urn else r"[A-Za-z0-9_\-]{1,160}"
    if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
        raise ProviderRejected("invalid provider account identifier")
    return value


def _graph_version(value):
    if not isinstance(value, str) or not re.fullmatch(r"v\d{1,2}\.\d{1,2}", value):
        raise ProviderRejected("configured Meta Graph version required")
    return value


def private_media_url(url, supabase_origin):
    """Only backend-issued signed tenant media URLs, never arbitrary external URLs."""
    if not isinstance(url, str) or not isinstance(supabase_origin, str):
        raise ProviderRejected("missing private media URL")
    a, b = urlsplit(url), urlsplit(supabase_origin)
    if (a.scheme != "https" or b.scheme != "https" or
        a.netloc != b.netloc or a.username or a.password or a.fragment or
        not a.path.startswith("/storage/v1/object/sign/retailgrowth-media/") or
        not a.query or len(url) > 3500):
        raise ProviderRejected("private media URL is not issued by this tenant store")
    return url


def linkedin_text_request(*, author_urn, token, commentary, api_version):
    urn = _id(author_urn, urn=True)
    if not re.fullmatch(r"urn:li:(person|organization):[A-Za-z0-9_\-]+", urn):
        raise ProviderRejected("only approved LinkedIn member or organization authors")
    if not re.fullmatch(r"20\d{4}", api_version or ""):
        raise ProviderRejected("LinkedIn YYYYMM version required")
    return ProviderRequest(
        "POST", "https://api.linkedin.com/rest/posts",
        {"Authorization": "Bearer " + _token(token),
         "Linkedin-Version": api_version, "X-Restli-Protocol-Version": "2.0.0",
         "Content-Type": "application/json"},
        {"author": urn, "commentary": _required(commentary, 3000),
         "visibility": "PUBLIC",
         "distribution": {"feedDistribution": "MAIN_FEED",
                          "targetEntities": [], "thirdPartyDistributionChannels": []},
         "lifecycleState": "PUBLISHED", "isReshareDisabledByAuthor": False},
    )


def linkedin_receipt(headers):
    rid = _id(headers.get("x-restli-id"), urn=True)
    if not rid.startswith(("urn:li:share:", "urn:li:ugcPost:")):
        raise ProviderRejected("unconfirmed remote post receipt")
    return ProviderReceipt("linkedin", rid, "PUBLISHED")


def facebook_page_request(*, page_id, page_token, text, graph_version):
    return ProviderRequest(
        "POST", f"https://graph.facebook.com/{_graph_version(graph_version)}/{_id(page_id)}/feed",
        {"Authorization": "Bearer " + _token(page_token)},
        {"message": _required(text, 5000), "published": True},
    )


def instagram_reel_container_request(*, ig_user_id, token, video_url,
                                     caption, supabase_origin, graph_version):
    return ProviderRequest(
        "POST", f"https://graph.facebook.com/{_graph_version(graph_version)}/{_id(ig_user_id)}/media",
        {"Authorization": "Bearer " + _token(token)},
        {"media_type": "REELS",
         "video_url": private_media_url(video_url, supabase_origin),
         "caption": _required(caption, 2200), "share_to_feed": True},
    )


def instagram_container_status_request(*, container_id, token, graph_version):
    return ProviderRequest(
        "GET", f"https://graph.facebook.com/{_graph_version(graph_version)}/{_id(container_id)}?fields=status_code",
        {"Authorization": "Bearer " + _token(token)}, {},
    )


def instagram_publish_request(*, ig_user_id, container_id, container_status,
                              token, graph_version):
    # Creating a container does NOT publish anything: only FINISHED is publishable.
    if container_status != "FINISHED":
        raise ProviderRejected("Instagram container not ready")
    return ProviderRequest(
        "POST", f"https://graph.facebook.com/{_graph_version(graph_version)}/{_id(ig_user_id)}/media_publish",
        {"Authorization": "Bearer " + _token(token)},
        {"creation_id": _id(container_id)},
    )


def youtube_resumable_init_request(*, token, title, description, size_bytes):
    """Initialize an upload as PRIVATE. Transfer/verification is another step.

    Upload session Location headers contain sensitive credentials; store them
    encrypted on the server and do not expose via user-facing APIs or logs.
    """
    if not isinstance(size_bytes, int) or not 0 < size_bytes <= 256 * 1024**3:
        raise ProviderRejected("unsupported video size")
    return ProviderRequest(
        "POST", "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        {"Authorization": "Bearer " + _token(token),
         "X-Upload-Content-Type": "video/mp4",
         "X-Upload-Content-Length": str(size_bytes),
         "Content-Type": "application/json"},
        {"snippet": {"title": _required(title, 100),
                     "description": _required(description, 5000)},
         "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}},
    )


def youtube_upload_location(value):
    """Strict session URL; used with server bearer token by upload/status PUTs."""
    if (not isinstance(value, str) or not 1 <= len(value) <= 4096
            or value != value.strip()
            or any(ord(char) <= 32 or ord(char) == 127 for char in value)):
        raise ProviderRejected("untrusted resumable upload session")
    try:
        parsed = urlsplit(value)
        valid = (parsed.scheme == "https" and parsed.hostname in
            {"www.googleapis.com", "youtube.googleapis.com"}
            and parsed.port in (None, 443)
            and not parsed.username and not parsed.password
            and not parsed.fragment
            and parsed.path == "/upload/youtube/v3/videos"
            and bool(parsed.query))
    except ValueError:
        valid = False
    if not valid:
        raise ProviderRejected("untrusted resumable upload session")
    return value
