"""F2/F4 versioned HTTP router: authorization, v1 separation and fail-closed OFF.

Pure router only. Registered Azure routes, Supabase transactions, and worker
deployment are intentionally NOT implied by these injected fake tests.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "azure-functions" / "campaign-api"))
sys.path.insert(0, str(ROOT / "video-engine"))

from http_api import HTTPAPI  # noqa: E402
from feature4_http_handoff import Feature4HTTP  # noqa: E402
from security import AuthenticationError  # noqa: E402

SHOP = "11111111-1111-4111-8111-111111111111"
FOREIGN = "44444444-4444-4444-8444-444444444444"
CAMPAIGN = "22222222-2222-4222-8222-222222222222"
JOB = "33333333-3333-4333-8333-333333333333"
LEASE = "55555555-5555-4555-8555-555555555555"
OUTPUT = "66666666-6666-4666-8666-666666666666"
USER = "77777777-7777-4777-8777-777777777777"
OTHER = "88888888-8888-4888-8888-888888888888"


def identity(token):
    if token == "signed-a":
        return USER
    if token == "signed-b":
        return OTHER
    raise AuthenticationError("invalid signature")


class RLS:
    def __init__(self):
        self.allow = True
        self.job = {"id": JOB, "shop_id": SHOP, "status": "QUEUED",
                    "output_asset_id": None}
        self.signs = []

    def campaign(self, token, user, cid):
        if token != "signed-a" or user != USER or cid != CAMPAIGN or not self.allow:
            return None
        return {"id": CAMPAIGN, "shop_id": SHOP, "status": "DRAFT"}

    def member(self, token, user, shop, *, write=False):
        return self.allow and token == "signed-a" and user == USER and shop == SHOP

    def feature4_job(self, token, user, job):
        if token != "signed-a" or user != USER or not self.allow or job != JOB:
            return None
        return self.job

    def asset(self, token, shop, asset):
        if token == "signed-a" and shop == SHOP and asset == OUTPUT:
            return {"shop_id": SHOP, "mime_type": "video/mp4",
                    "storage_bucket": "retailgrowth-media",
                    "object_path": f"{SHOP}/renders/{JOB}/{LEASE}.mp4"}
        return None

    def sign_download(self, token, shop, object_path):
        self.signs.append((token, shop, object_path))
        return ("https://example.supabase.co/storage/v1/object/sign/"
                "retailgrowth-media/" + object_path + "?token=private")


class AtomicFake:
    """Never substitutes for a real transactional/rights-verified DB backend."""
    def __init__(self):
        self.calls = []
    def create_feature4_intent(self, data):
        self.calls.append(data)
        return {"id": JOB, "shop_id": SHOP, "status": "QUEUED"}


def intent():
    return {
        "shop_id": SHOP, "campaign_id": CAMPAIGN, "approval_id": "approved-f2",
        "draft": {"version": "rg_video_v2", "shop_id": SHOP,
                  "duration_seconds": 30, "scenes": [
                      {"start": 0, "duration": 15, "headline": "Sample"},
                      {"start": 15, "duration": 15, "headline": "Visit Us"},
                  ]},
    }


def setup(*, enabled=False):
    users, backend = RLS(), AtomicFake()
    f4 = Feature4HTTP(users, backend) if enabled else None
    return HTTPAPI(identity, users, feature4_api=f4), users, backend


def test_v2_disabled_even_when_v1_is_present_and_jwt_required():
    api, users, backend = setup()
    p = f"/campaigns/{CAMPAIGN}/feature4-renders"
    assert api.handle("POST", p, "", intent()) == (401, {"error": "UNAUTHORIZED"})
    assert api.handle("POST", p, "Bearer forged", intent()) == (401, {"error": "UNAUTHORIZED"})
    assert api.handle("POST", p, "Bearer signed-a", intent()) == (
        503, {"error": "FEATURE4_V2_DISABLED"})
    assert api.handle("GET", f"/feature4-render-jobs/{JOB}", "Bearer signed-a") == (
        503, {"error": "FEATURE4_V2_DISABLED"})
    assert api.handle("GET", f"/feature4-render-jobs/{JOB}/download", "Bearer signed-a") == (
        503, {"error": "FEATURE4_V2_DISABLED"})
    assert api.handle("POST", f"/campaigns/{CAMPAIGN}/renders",
                      "Bearer signed-a", {"day_id": JOB}) == (
                          503, {"error": "RENDER_NOT_CONFIGURED"})
    assert not backend.calls and not users.signs


def test_strict_method_and_route_boundaries_do_not_invoke_f4():
    api, _, backend = setup(enabled=True)
    paths = [
        ("GET", f"/campaigns/{CAMPAIGN}/feature4-renders"),
        ("POST", f"/campaigns/{CAMPAIGN}/days/{JOB}/feature4-renders"),
        ("PUT", f"/feature4-render-jobs/{JOB}"),
        ("POST", f"/feature4-render-jobs/{JOB}/download"),
        ("GET", f"/feature4-render-jobs/{JOB}/download/extra"),
    ]
    for method, path in paths:
        assert api.handle(method, path, "Bearer signed-a", intent())[0] == 404
    assert not backend.calls


def test_verified_user_create_status_and_private_download_when_trusted_backend_injected():
    api, users, backend = setup(enabled=True)
    create = f"/campaigns/{CAMPAIGN}/feature4-renders"
    code, receipt = api.handle("POST", create, "Bearer signed-a", intent())
    assert code == 202 and receipt == {"shop_id": SHOP, "job_id": JOB, "status": "QUEUED"}
    assert len(backend.calls) == 1
    assert backend.calls[0]["requested_by"] == USER
    assert backend.calls[0]["campaign_id"] == CAMPAIGN
    assert backend.calls[0]["preset"] == "feature4_reel_v1"
    assert len(backend.calls[0]["idempotency_key"]) == 64

    read = f"/feature4-render-jobs/{JOB}"
    assert api.handle("GET", read, "Bearer signed-a") == (200, receipt)
    assert api.handle("GET", read + "/download", "Bearer signed-a") == (
        409, {"error": "OUTPUT_NOT_READY"})
    users.job.update(status="SUCCEEDED", output_asset_id=OUTPUT)
    code, signed = api.handle("GET", read + "/download", "Bearer signed-a")
    assert code == 200 and signed["job_id"] == JOB and signed["shop_id"] == SHOP
    assert signed["url"].endswith("?token=private")
    assert users.signs == [("signed-a", SHOP, f"{SHOP}/renders/{JOB}/{LEASE}.mp4")]


def test_foreign_revoked_invalid_plan_never_creates_job_or_signs_media():
    api, users, backend = setup(enabled=True)
    path = f"/campaigns/{CAMPAIGN}/feature4-renders"
    assert api.handle("POST", path, "Bearer signed-b", intent())[0] == 404
    wrong_shop = intent()
    wrong_shop["shop_id"] = FOREIGN
    assert api.handle("POST", path, "Bearer signed-a", wrong_shop)[0] == 400
    changed = intent()
    changed["draft"]["version"] = "unsafe-v3"
    assert api.handle("POST", path, "Bearer signed-a", changed)[0] == 400
    assert not backend.calls
    users.allow = False
    assert api.handle("POST", path, "Bearer signed-a", intent())[0] == 404
    assert api.handle("GET", f"/feature4-render-jobs/{JOB}",
                      "Bearer signed-a")[0] == 404
    assert not users.signs


def test_invalid_path_fails_closed_and_unknown_v1_is_unchanged():
    api, _, backend = setup(enabled=True)
    assert api.handle("POST", "/campaigns/not-a-uuid/feature4-renders",
                      "Bearer signed-a", intent())[0] == 400
    assert api.handle("GET", "/feature4-render-jobs/not-a-uuid",
                      "Bearer signed-a")[0] == 400
    assert api.handle("GET", "/render-jobs/" + JOB,
                      "Bearer signed-a") == (503, {"error": "RENDER_NOT_CONFIGURED"})
    assert not backend.calls
