"""F3-08 private PNG Azure response adapter; not a registered public route.

The injected reader factory must be constructed server-side with verified
JWT/RLS membership and fresh independent rights checks. No fallback reader.
"""
from __future__ import annotations

from feature3_private_png_http import private_png_http


def _denied(status, response_type):
    return response_type(
        body=b"", status_code=status, mimetype=None,
        headers={
            "Cache-Control": "no-store, private",
            "Pragma": "no-cache",
            "X-Content-Type-Options": "nosniff",
            "Content-Length": "0",
        },
    )


def handle_private_png_request(request, *, reader_factory, response_type):
    """Adapt a GET-only Azure request without trusting request-selected rights.

    Reject ambiguous request metadata *before* invoking the private reader.
    No token, path, shop or rights assertion is accepted from query/body.
    """
    if not callable(response_type):
        raise ValueError("Trusted Azure response constructor required")
    if request is None or getattr(request, "method", None) != "GET":
        return _denied(405, response_type)
    params = getattr(request, "route_params", None)
    headers = getattr(request, "headers", None)
    if (type(params) is not dict or set(params) != {"shop_id", "job_id"} or
            not callable(getattr(headers, "get", None))):
        return _denied(400, response_type)
    # A query or request body must never override trusted route identifiers.
    query = getattr(request, "params", None)
    if query is not None and (not isinstance(query, dict) or bool(query)):
        return _denied(400, response_type)
    if not callable(reader_factory):
        return _denied(503, response_type)
    reply = private_png_http(
        authorization=headers.get("Authorization", ""),
        shop_id=params["shop_id"],
        job_id=params["job_id"],
        reader_factory=reader_factory,
    )
    return response_type(
        body=reply.body, status_code=reply.status, headers=reply.headers,
        mimetype="image/png" if reply.status == 200 else None,
    )
