"""F3-08 optional Azure Functions Blueprint wiring; never auto-mounted.

The application owner must explicitly register the returned blueprint and
supply a reviewed, server-owned reader factory backed by real JWT/RLS/current
output rights. This module does not provision or enable any hosted endpoint.
"""
from __future__ import annotations

from feature3_private_png_route import handle_private_png_request

ROUTE = "feature3/shops/{shop_id}/jobs/{job_id}/private.png"


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

    blueprint = blueprint_type()

    # Azure's ANONYMOUS host setting is NOT user authorization. The route
    # always delegates to the JWT/RLS/current-rights reader and fails closed.
    # No function key or admin credential is ever a substitute for user JWT.
    @blueprint.route(route=ROUTE, methods=["GET"],
                     auth_level=auth_level.ANONYMOUS)
    def feature3_private_png(request):
        return handle_private_png_request(
            request, reader_factory=reader_factory, response_type=response_type
        )

    return blueprint
