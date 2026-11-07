"""F3-08 Azure Functions response adapter (source-only, disabled by default).

The route's reader_factory MUST be server-owned and wired to real JWT/RLS
membership and current generated-output rights. This module does not supply
a rights shortcut, trust caller-provided claims, or activate a public route.
"""
from __future__ import annotations

from feature3_private_png_http import private_png_http


def handle_private_png_request(request, *, reader_factory, response_type):
    """Adapt an Azure HttpRequest to HttpResponse without JSON/base64 leakage.

    The caller must provide a trusted reader_factory; absent authorization
    infrastructure fails closed before any private storage access.
    """
    params = getattr(request, "route_params", None)
    headers = getattr(request, "headers", None)
    if not isinstance(params, dict) or not callable(getattr(headers, "get", None)):
        raise ValueError("Invalid private binary request adapter")
    reply = private_png_http(
        authorization=headers.get("Authorization", ""),
        shop_id=params.get("shop_id"),
        job_id=params.get("job_id"),
        reader_factory=reader_factory,
    )
    return response_type(
        body=reply.body,
        status_code=reply.status,
        headers=reply.headers,
        mimetype="image/png" if reply.status == 200 else None,
    )
