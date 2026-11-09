"""F3-08 offline registration guard; no hosted JWT, Storage or rights proof."""
from __future__ import annotations

import ast
from pathlib import Path
import unittest


SOURCE = (Path(__file__).resolve().parents[2] /
          "azure-functions" / "campaign-api" / "function_app.py")


class PrivatePngRegistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        cls.routes = [n for n in cls.tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                      and n.name == "feature3_private_png_download"]

    def test_registered_once_with_get_only_and_scoped_ids(self):
        self.assertEqual(len(self.routes), 1)
        node = self.routes[0]
        self.assertEqual(len(node.decorator_list), 1)
        dec = node.decorator_list[0]
        self.assertIsInstance(dec, ast.Call)
        self.assertEqual(ast.unparse(dec.func), "app.route")
        kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in dec.keywords}
        self.assertEqual(kwargs, {
            "route": "shops/{shop_id}/feature3-private-png/{job_id}",
            "methods": ["GET"],
        })

    def test_unconfigured_reader_fails_closed_without_json_dispatch(self):
        node = self.routes[0]
        calls = [n for n in ast.walk(node) if isinstance(n, ast.Call)]
        handler = [n for n in calls if isinstance(n.func, ast.Name)
                   and n.func.id == "handle_private_png_request"]
        self.assertEqual(len(handler), 1)
        kwargs = {kw.arg: kw.value for kw in handler[0].keywords}
        self.assertIn("reader_factory", kwargs)
        self.assertIsInstance(kwargs["reader_factory"], ast.Constant)
        self.assertIsNone(kwargs["reader_factory"].value)
        self.assertEqual(ast.unparse(kwargs["response_type"]), "func.HttpResponse")
        self.assertEqual(ast.unparse(handler[0].args[0]), "req")
        self.assertFalse(any(isinstance(n.func, ast.Name) and n.func.id == "dispatch"
                             for n in calls))

    def test_runtime_route_preserves_fail_closed_reader_boundary(self):
        """Execute the registered handler without Azure or real JWT credentials."""
        import copy
        import sys
        from types import ModuleType, SimpleNamespace
        from unittest.mock import patch

        node = copy.deepcopy(self.routes[0])
        node.decorator_list = []
        isolated = ast.Module(body=[node], type_ignores=[])
        ast.fix_missing_locations(isolated)
        calls = []
        sentinel = object()

        def guarded_adapter(request, *, reader_factory, response_type):
            calls.append((request, reader_factory, response_type))
            if reader_factory is not None:
                raise AssertionError("Unreviewed reader activated in public route")
            return sentinel

        fake_module = ModuleType("feature3_private_png_route")
        fake_module.handle_private_png_request = guarded_adapter
        fake_response = object()
        scope = {"func": SimpleNamespace(HttpRequest=object, HttpResponse=fake_response)}
        with patch.dict(sys.modules, {"feature3_private_png_route": fake_module}):
            exec(compile(isolated, str(SOURCE), "exec"), scope)
            request = SimpleNamespace(route_params={"shop_id": "untrusted",
                                                     "job_id": "untrusted"})
            result = scope["feature3_private_png_download"](request)

        self.assertIs(result, sentinel)
        self.assertEqual(calls, [(request, None, fake_response)])

    def test_binary_route_has_no_write_method_or_client_rights_input(self):
        node = self.routes[0]
        names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
        self.assertNotIn("os", names)
        self.assertNotIn("build_api", names)
        self.assertNotIn("get_json", names)
        self.assertNotIn("get_body", names)


if __name__ == "__main__":
    unittest.main()
