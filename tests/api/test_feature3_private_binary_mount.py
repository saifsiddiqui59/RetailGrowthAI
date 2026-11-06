"""F3-08 mounted Azure entrypoint regression: source-only, fail-closed.

This deliberately does NOT simulate a real signed DEV tenant or rights grant.
"""
import ast
from pathlib import Path
import unittest

APP = Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api" / "function_app.py"


class MountedPrivatePNGTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(APP.read_text(encoding="utf-8"))
        cls.handlers = [n for n in cls.tree.body if isinstance(n, ast.FunctionDef)
                        and n.name == "feature3_private_png"]

    def test_unique_get_only_route_with_no_public_anonymous_download_fallback(self):
        self.assertEqual(len(self.handlers), 1)
        # Parse the full source before inspecting decorators: escaped newline
        # text in Python expressions must never silently evade CI coverage.
        compile(self.tree, str(APP), "exec")
        routes = []
        for node in self.tree.body:
            if isinstance(node, ast.FunctionDef):
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr == "route":
                        route = next((kw.value.value for kw in dec.keywords
                                      if kw.arg == "route" and isinstance(kw.value, ast.Constant)), None)
                        if route is None and dec.args and isinstance(dec.args[0], ast.Constant):
                            route = dec.args[0].value
                        if route and route.endswith("/private-png"):
                            routes.append((node.name, dec))
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0][0], "feature3_private_png")
        self.assertEqual(next(kw.value.value for kw in routes[0][1].keywords
                              if kw.arg == "route"),
                         "shops/{shop_id}/feature3-gpu-jobs/{job_id}/private-png")
        methods = next(kw.value for kw in routes[0][1].keywords if kw.arg == "methods")
        self.assertEqual(ast.literal_eval(methods), ["GET"])

    def test_mounted_handler_does_not_enable_without_trusted_rights_provider(self):
        handler = self.handlers[0]
        calls = [n for n in ast.walk(handler) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name) and n.func.id == "private_png_response"]
        self.assertEqual(len(calls), 1)
        kwargs = {kw.arg: kw.value for kw in calls[0].keywords}
        self.assertIsNone(ast.literal_eval(kwargs["reader_factory"]))
        self.assertIs(ast.literal_eval(kwargs["enabled"]), False)
        # A source-only mounted route must not accidentally inherit the
        # existing signed-URL download endpoint or browser-provided rights.
        self.assertNotIn("signed_url", ast.unparse(handler).lower())
        self.assertNotIn("service_role", ast.unparse(handler).lower())
        # The mounted route must not create a synthetic rights authority or
        # treat an environment toggle as authorization.
        self.assertNotIn("os.environ", ast.unparse(handler))
        self.assertNotIn("SupabaseJWTVerifier", ast.unparse(handler))


if __name__ == "__main__":
    unittest.main()
