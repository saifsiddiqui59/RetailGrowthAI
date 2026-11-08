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
    if request is None:
        return _denied(400, response_type)
    try:
        method = request.method
        params = request.route_params
        headers = request.headers
        query = request.params
        get_body = request.get_body
    except Exception:
        return _denied(400, response_type)
    if method != "GET":
        return _denied(405, response_type)
    if (type(params) is not dict or set(params) != {"shop_id", "job_id"} or
            not callable(getattr(headers, "get", None))):
        return _denied(400, response_type)
    # A query or request body must never override trusted route identifiers.
    if query is not None and (not isinstance(query, dict) or bool(query)):
        return _denied(400, response_type)
    # Refuse GET bodies so proxies cannot disagree about credential or scope.
    if not callable(get_body):
        return _denied(400, response_type)
    try:
        body = get_body()
    except Exception:
        return _denied(400, response_type)
    if type(body) is not bytes or body:
        return _denied(400, response_type)
    if not callable(reader_factory):
        return _denied(503, response_type)
    try:
        authorization = headers.get("Authorization", "")
    except Exception:
        return _denied(400, response_type)
    if type(authorization) is not str:
        return _denied(400, response_type)
    # A proxy/framework may preserve differently cased duplicate headers.
    # Never allow an ambiguous bearer token to reach the private reader.
    try:
        names = list(headers.keys())
        if (any(type(name) is not str for name in names) or
                sum(name.lower() == "authorization" for name in names) != 1):
            return _denied(400, response_type)
        actual_name = next(name for name in names if name.lower() == "authorization")
        if type(headers.get(actual_name)) is not str or headers.get(actual_name) != authorization:
            return _denied(400, response_type)
    except Exception:
        return _denied(400, response_type)
    # A backend provider/reader can fail after request validation. Never
    # propagate its exception or diagnostic details into a public response.
    # In particular, a partial binary result must not be returned on failure.
    try:
        reply = private_png_http(
            authorization=authorization,
            shop_id=params["shop_id"],
            job_id=params["job_id"],
            reader_factory=reader_factory,
        )
    except Exception:
        return _denied(503, response_type)
    return response_type(
        body=reply.body, status_code=reply.status, headers=reply.headers,
        mimetype="image/png" if reply.status == 200 else None,
    )
