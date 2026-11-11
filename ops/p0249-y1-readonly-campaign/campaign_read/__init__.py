"""Isolated Y1 read-only campaign GET, reusing ORIGINAL RetailGrowthAI auth/RLS API.

A shadow endpoint: NOT a production switch. No JWT in logs, writes, queue or
timer functions, privileged service key, model calls, or retry of mutations.
"""
import json
import os

import azure.functions as func

from request_diagnostics import RequestDiagnostics


def _build_original_api(origin, publishable_key):
    """Defer heavy JWT/RLS imports until the shadow is explicitly enabled.

    Python v1 functions must index even with the shadow disabled. If the
    database or cryptography layer is unavailable, never replace the original
    app with a permissive mock or return customer data.
    """
    from http_api import HTTPAPI
    from security import SupabaseJWTVerifier
    from tenant_store import TenantStore
    return HTTPAPI(SupabaseJWTVerifier(origin), TenantStore(origin, publishable_key))


def handle_campaign_get(authorization, campaign_id, *, environment=None):
    """Purely read-only path; validate JWT and current tenant membership.

    The same original HTTPAPI/tenant_store/security modules used in Flex
    are copied unchanged during package assembly, never forked here.
    """
    if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
        return 401, {"error": "UNAUTHORIZED"}
    token = authorization[7:].strip()
    if not token or len(token) > 8192:
        return 401, {"error": "UNAUTHORIZED"}
    env = os.environ if environment is None else environment
    if env.get("RGAI_P0249_READONLY_SHADOW") != "true":
        return 503, {"error": "SERVICE_NOT_CONFIGURED"}
    origin = env.get("RETAIL_SUPABASE_URL")
    public_key = env.get("RETAIL_SUPABASE_PUBLISHABLE_KEY")
    if not origin or not public_key:
        return 503, {"error": "SERVICE_NOT_CONFIGURED"}
    api = _build_original_api(origin, public_key)
    return api.handle("GET", "/campaigns/" + campaign_id, authorization)


def main(req: func.HttpRequest) -> func.HttpResponse:
    campaign_id = req.route_params.get("campaign_id", "")
    diagnostics = RequestDiagnostics("GET", "/campaigns/" + campaign_id)
    try:
        status, payload = handle_campaign_get(
            req.headers.get("Authorization", ""), campaign_id
        )
    except (KeyError, TypeError, ValueError):
        status, payload = 503, {"error": "SERVICE_NOT_CONFIGURED"}
    except Exception:
        # Do not return auth/Supabase exception details to anyone.
        status, payload = 500, {"error": "INTERNAL_ERROR"}
    return func.HttpResponse(
        json.dumps(payload, separators=(",", ":")), status_code=status,
        mimetype="application/json", headers=diagnostics.complete(status, payload),
    )
