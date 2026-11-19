"""Issue #249 Y1 GET-only status shadow for three original authorized endpoints.

SOURCE ONLY: no deployment or endpoint registration on the existing Y1.
Requires a separately reviewed, exact-scoped ZIP and explicit second opt-in.
Never loads auth/database modules before flags are enabled. No service role,
work queue, POST/PATCH, timer, render engine, image provider or paid model.
"""
from __future__ import annotations

import json
import os
from uuid import UUID

ROUTES = {
    "render_job": ("render-jobs", "job_id"),
    "poster_job": ("poster-jobs", "job_id"),
    "poster_draft": ("poster-drafts", "draft_id"),
}
SHADOW_FLAG = "RGAI_P0249_READONLY_SHADOW"
EXTRA_FLAG = "RGAI_P0249_EXTRA_GET_SHADOW"


def _build_original_api(origin: str, public_key: str):
    """Use original signed JWT + original user's RLS-scoped TenantStore.

    RenderAPI/PosterDraftAPI/PosterRenderAPI are constructed for their GET
    handlers only. Their write methods are not externally routed here.
    """
    from http_api import HTTPAPI
    from security import cached_supabase_verifier
    from tenant_store import TenantStore
    from render_api import RenderAPI
    from poster_draft_api import PosterDraftAPI
    from poster_render_api import PosterRenderAPI

    store = TenantStore(origin, public_key)
    return HTTPAPI(
        cached_supabase_verifier(origin), store,
        planning_queue=None, failure_store=None,
        render_api=RenderAPI(store, None, None),
        poster_api=PosterDraftAPI(store),
        poster_render_api=PosterRenderAPI(store),
    )


def _canonical(value):
    if not isinstance(value, str) or len(value) != 36:
        return None
    try:
        return value if str(UUID(value)) == value else None
    except (TypeError, ValueError, AttributeError):
        return None


def handle_get(kind: str, identifier: str, authorization: str, *, environment=None):
    """Only one of three literal GET paths can reach the original HTTPAPI."""
    if kind not in ROUTES:
        return 404, {"error": "NOT_FOUND"}
    if (not isinstance(authorization, str) or
            not authorization.startswith("Bearer ") or
            not authorization[7:].strip() or len(authorization[7:].strip()) > 8192):
        return 401, {"error": "UNAUTHORIZED"}
    identifier = _canonical(identifier)
    if identifier is None:
        return 400, {"error": "INVALID_REQUEST"}
    env = os.environ if environment is None else environment
    if env.get(SHADOW_FLAG) != "true" or env.get(EXTRA_FLAG) != "true":
        return 503, {"error": "SERVICE_NOT_CONFIGURED"}
    origin = env.get("RETAIL_SUPABASE_URL")
    public_key = env.get("RETAIL_SUPABASE_PUBLISHABLE_KEY")
    if not origin or not public_key:
        return 503, {"error": "SERVICE_NOT_CONFIGURED"}
    endpoint, _ = ROUTES[kind]
    # Never let an untrusted caller pass a method, arbitrary path or host.
    return _build_original_api(origin, public_key).handle(
        "GET", "/" + endpoint + "/" + identifier, authorization
    )


def serve(request, kind: str):
    """Common function entrypoint, preserving original safe request diagnostics."""
    from azure import functions as func
    from request_diagnostics import RequestDiagnostics

    endpoint, param = ROUTES[kind]  # only hard-coded callers
    identifier = request.route_params.get(param, "")
    diagnostic = RequestDiagnostics("GET", "/" + endpoint + "/" + str(identifier))
    try:
        if request.method != "GET":
            status, payload = 405, {"error": "METHOD_NOT_ALLOWED"}
        else:
            status, payload = handle_get(
                kind, identifier, request.headers.get("Authorization", "")
            )
    except (KeyError, TypeError, ValueError):
        status, payload = 503, {"error": "SERVICE_NOT_CONFIGURED"}
    except Exception:
        status, payload = 500, {"error": "INTERNAL_ERROR"}
    return func.HttpResponse(
        json.dumps(payload, separators=(",", ":")), status_code=status,
        mimetype="application/json",
        headers=diagnostic.complete(status, payload),
    )
