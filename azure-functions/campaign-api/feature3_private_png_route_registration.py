"""F3-08 optional Azure Functions Blueprint wiring; never auto-mounted.

This matches the existing fail-closed function_app.py route. Registering both
the Blueprint and the existing handler would duplicate the HTTP route; use
only one after independent review of a trusted reader binding.

The application owner must explicitly register the returned blueprint and
supply a reviewed, server-owned reader factory backed by real JWT/RLS/current
output rights. This module does not provision or enable any hosted endpoint.
"""
from __future__ import annotations

from feature3_private_png_route import handle_private_png_request

ROUTE = "shops/{shop_id}/feature3-private-png/{job_id}"


def build_private_png_blueprint(*, azure_functions, reader_factory):
    """Construct an isolated GET-only Blueprint without registering it.

    Never infer rights from route, query, browser claims or Azure function
    keys. The injected reader factory must perform fresh user verification.
    """
    if not callable(reader_factory):
        raise ValueError("Trusted server-owned reader factory required")
    if azure_functions is None:
        raise ValueError("Azure Functions module required")
    blueprint_type = getattr(azure_functions, "Blueprint", None)
    response_type = getattr(azure_functions, "HttpResponse", None)
    auth_level = getattr(azure_functions, "AuthLevel", None)
    if (not callable(blueprint_type) or not callable(response_type) or
            auth_level is None or not hasattr(auth_level, "ANONYMOUS")):
        raise ValueError("Azure Functions Blueprint/response contract required")

    # Fail before registration if a malformed host shim cannot provide a
    # genuine decorator. Never silently publish an unguarded HTTP handler.
    try:
        blueprint = blueprint_type()
        route_decorator = getattr(blueprint, "route", None)
    except Exception as exc:
        # A broken host constructor or dynamic route attribute must never
        # leak its exception (potentially containing environment secrets).
        raise ValueError("Azure Functions Blueprint initialization failed") from exc
    if not callable(route_decorator):
        raise ValueError("Azure Functions Blueprint route decorator required")

    # Azure's ANONYMOUS host setting is NOT user authorization. The route
    # always delegates to the JWT/RLS/current-rights reader and fails closed.
    # No function key or admin credential is ever a substitute for user JWT.
    def feature3_private_png(request):
        return handle_private_png_request(
            request, reader_factory=reader_factory, response_type=response_type
        )

    # Do not allow a host shim/decorator to replace this security boundary
    # with a different callable. A callable replacement could bypass the
    # injected reader even though a simple callable() check would pass.
    # A broken host decorator must never leave an apparently usable
    # Blueprint. Normalize host errors without leaking adapter diagnostics.
    try:
        decorator = route_decorator(
            route=ROUTE, methods=["GET"], auth_level=auth_level.ANONYMOUS
        )
        if not callable(decorator):
            raise ValueError("Azure Functions route decorator returned no callable")
        decorated = decorator(feature3_private_png)
    except Exception as exc:
        raise ValueError("Azure Functions private route registration failed") from exc
    if decorated is not feature3_private_png:
        raise ValueError("Azure Functions route registration replaced private handler")
    return blueprint
