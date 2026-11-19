"""Feature3 generated-PNG source helpers cannot silently enter Functions ZIP.

These offline checks do not authorize hosted JWT/RLS or output rights.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("feature3_checked_zip", ROOT / "scripts" / "deploy" / "package.py")
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class Feature3RuntimeZipClosureTests(unittest.TestCase):
    def test_source_only_f3_helpers_are_not_shipped(self):
        entries = package.source_files()
        self.assertLessEqual(len(entries) + 3, 120)
        for name in package.F3_SOURCE_ONLY_MODULES:
            self.assertNotIn("azure-functions/campaign-api/" + name + ".py", entries)
        for name in (
            "feature3_private_binary_http",
            "feature3_private_binary_route",
            "feature3_private_png_http",
            "feature3_private_png_route",
            "feature3_private_png_reader",
        ):
            self.assertIn("azure-functions/campaign-api/" + name + ".py", entries)
        self.assertTrue(package.verify_f3_runtime_imports(entries))

    def test_static_or_literal_dynamic_import_of_unshipped_module_fails_closed(self):
        for statement in (
            "import feature3_private_png_runtime",
            "from feature3_private_png_runtime import build_private_png_reader_factory",
            'import importlib; importlib.import_module("feature3_private_png_runtime")',
            'from importlib import import_module; import_module("feature3_private_png_runtime")',
            '__import__("feature3_private_png_runtime")',
        ):
            with self.subTest(statement=statement):
                with self.assertRaisesRegex(ValueError, "Undeclared Feature3 source-only module"):
                    package.verify_f3_runtime_imports({
                        "azure-functions/campaign-api/function_app.py": statement.encode("utf-8")
                    })

    def test_declared_non_sensitive_mounted_route_is_allowed(self):
        self.assertTrue(package.verify_f3_runtime_imports({
            "azure-functions/campaign-api/function_app.py": (
                b"from feature3_private_binary_route import private_png_response"
            ),
        }))


if __name__ == "__main__":
    unittest.main()
