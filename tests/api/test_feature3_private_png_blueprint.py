"""F3-08 optional Blueprint wiring: synthetic only, no hosted auth claim."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_route_registration import ROUTE, build_private_png_blueprint


class Response:
    def __init__(self, *, body, status_code, headers, mimetype):
        self.body, self.status_code = body, status_code
        self.headers, self.mimetype = headers, mimetype


class Blueprint:
    def __init__(self):
        self.routes = []

    def route(self, **options):
        def decorate(handler):
            self.routes.append((options, handler))
            return handler
        return decorate


class BlueprintTests(unittest.TestCase):
    def setUp(self):
        self.azure = SimpleNamespace(
            Blueprint=Blueprint, HttpResponse=Response,
            AuthLevel=SimpleNamespace(ANONYMOUS="anonymous"))

    def test_optional_route_matches_existing_fail_closed_registration(self):
        # Static source contract: never introduce a second public path for
        # the same private asset or accidentally enable an unreviewed reader.
        source = (Path(__file__).resolve().parents[2] / "azure-functions" /
                  "campaign-api" / "function_app.py").read_text(encoding="utf-8")
        self.assertIn('route="' + ROUTE + '"', source)
        self.assertIn("reader_factory=None, response_type=func.HttpResponse", source)
        self.assertNotIn("register_blueprint", source)

    def test_untrusted_factory_or_incomplete_host_contract_refused(self):
        for factory in (None, object(), "browser-rights"):
            with self.assertRaises(ValueError):
                build_private_png_blueprint(
                    azure_functions=self.azure, reader_factory=factory)
        for module in (None, SimpleNamespace(), SimpleNamespace(
                Blueprint=Blueprint, HttpResponse=Response)):
            with self.assertRaises(ValueError):
                build_private_png_blueprint(
                    azure_functions=module, reader_factory=lambda *_: None)

    def test_opt_in_get_route_and_backend_failure_are_fail_closed(self):
        calls = []
        def factory(*args):
            calls.append(args)
            raise RuntimeError("synthetic backend unavailable")
        blueprint = build_private_png_blueprint(
            azure_functions=self.azure, reader_factory=factory)
        self.assertEqual(len(blueprint.routes), 1)
        options, handler = blueprint.routes[0]
        self.assertEqual(options, {
            "route": ROUTE, "methods": ["GET"], "auth_level": "anonymous"})
        self.assertEqual(calls, [])
        shop, job = str(uuid4()), str(uuid4())
        req = SimpleNamespace(
            method="GET", route_params={"shop_id": shop, "job_id": job},
            headers={"Authorization": "Bearer " + "x" * 30},
            params={}, get_body=lambda: b"")
        reply = handler(req)
        self.assertEqual((reply.status_code, reply.body), (503, b""))
        self.assertEqual(calls, [(shop, job)])
        self.assertEqual(reply.headers["Cache-Control"], "no-store, private")

    def test_foreign_scope_or_missing_auth_never_invokes_reader(self):
        calls = []
        def factory(*args):
            calls.append(args)
            raise RuntimeError("unreachable")
        handler = build_private_png_blueprint(
            azure_functions=self.azure,
            reader_factory=factory).routes[0][1]
        for params, headers in (
            ({"shop_id": "foreign", "job_id": str(uuid4())},
             {"Authorization": "Bearer " + "x" * 30}),
            ({"shop_id": str(uuid4()), "job_id": str(uuid4())}, {}),
        ):
            req = SimpleNamespace(
                method="GET", route_params=params, headers=headers,
                params={}, get_body=lambda: b"")
            reply = handler(req)
            self.assertNotEqual(reply.status_code, 200)
            self.assertEqual(reply.body, b"")
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
