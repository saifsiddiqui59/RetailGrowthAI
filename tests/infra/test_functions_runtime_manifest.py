"""Coordinator-owned Functions runtime manifest tests: pytest AND stdlib unittest."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"scripts"/"deploy"/"package.py"
spec=importlib.util.spec_from_file_location("issue650_runtime_packager",P)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class FunctionsRuntimeManifestTests(unittest.TestCase):
    def test_versioned_functions_runtime_allowlist_under_zip_budget(self):
        source=mod.source_files()
        self.assertLessEqual(len(source)+3,120)  # ffmpeg, ffprobe, licenses
        self.assertIn("function_app.py",source)
        self.assertIn("host.json",source)
        self.assertIn("azure-functions/campaign-api/render_worker.py",source)
        for filename in ("feature2_ai_writer.py","feature2_llm.py","prompt_improver.py"):
            self.assertIn("ai_agents/"+filename,source)
        self.assertTrue(mod.verify_runtime_agent_imports(source))
        self.assertNotIn("ai_agents/feature2_kokoro_local.py",source)
        self.assertNotIn("ai_agents/feature2_voice_quality.py",source)

    def test_extra_twenty_offline_f2_modules_not_silently_shipped(self):
        with tempfile.TemporaryDirectory() as temp:
            home=Path(temp)
            for module in mod.RUNTIME_AGENT_MODULES:
                (home/(module+".py")).write_bytes(
                    (mod.AGENTS/(module+".py")).read_bytes())
            for count in range(20):
                (home/("feature2_offline_research_"+str(count)+".py")).write_text(
                    "OFFLINE_SOURCE_ONLY=True\n",encoding="utf-8")
            with patch.object(mod,"AGENTS",home):
                entries=mod.source_files()
            self.assertLessEqual(len(entries)+3,120)
            self.assertFalse(any("offline_research" in path for path in entries))

    def test_future_registered_agent_import_must_be_declared(self):
        candidate=mod.source_files()
        candidate["azure-functions/campaign-api/future_private_voice.py"]=(
            b"from ai_agents.feature2_kokoro_local import synthesize_local\n")
        with self.assertRaisesRegex(ValueError,"Undeclared ai_agents runtime import"):
            mod.verify_runtime_agent_imports(candidate)

    def test_dynamic_literal_import_is_not_silently_omitted(self):
        candidate=mod.source_files()
        candidate["azure-functions/campaign-api/future_private_voice.py"]=(
            b"import importlib\n"
            b"worker=importlib.import_module('ai_agents.feature2_kokoro_local')\n")
        with self.assertRaisesRegex(ValueError,"Undeclared ai_agents runtime import"):
            mod.verify_runtime_agent_imports(candidate)

    def test_excluded_source_module_package_import_forms_fail_closed(self):
        # These import forms were invisible to the original manifest audit.
        # Synthetic modules avoid any real model or provider dependency.
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            (home / "offline_voice.py").write_text("SAFE_TEST_FIXTURE = True\n", encoding="utf-8")
            (home / "schemas.py").write_text("SAFE_TEST_FIXTURE = True\n", encoding="utf-8")
            forms = (
                b"from ai_agents import offline_voice\n",
                b"from . import offline_voice\n",
                b"worker = __import__('ai_agents.offline_voice')\n",
            )
            with patch.object(mod, "AGENTS", home):
                for statement in forms:
                    with self.subTest(statement=statement):
                        candidate = {"ai_agents/schemas.py": statement}
                        with self.assertRaisesRegex(
                            ValueError, "Undeclared ai_agents runtime import"
                        ):
                            mod.verify_runtime_agent_imports(candidate)

    def test_aliased_importlib_module_calls_fail_closed(self):
        # A source-only worker can import through either legal alias form.
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            (home / "offline_voice.py").write_text("SAFE_TEST_FIXTURE = True\n", encoding="utf-8")
            forms = (
                b"from importlib import import_module as load; load('ai_agents.offline_voice')\n",
                b"import importlib as il; il.import_module('ai_agents.offline_voice')\n",
            )
            with patch.object(mod, "AGENTS", home):
                for statement in forms:
                    with self.subTest(statement=statement):
                        candidate = {"ai_agents/schemas.py": statement}
                        with self.assertRaisesRegex(ValueError, "Undeclared ai_agents runtime import"):
                            mod.verify_runtime_agent_imports(candidate)

    def test_exported_symbol_is_not_mistaken_for_excluded_module(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            (home / "schemas.py").write_text("SAFE_TEST_FIXTURE = True\n", encoding="utf-8")
            candidate = {
                "ai_agents/schemas.py": b"from ai_agents import exported_symbol\n"
            }
            with patch.object(mod, "AGENTS", home):
                self.assertTrue(mod.verify_runtime_agent_imports(candidate))

    def test_mandatory_agent_missing_fails_closed_even_with_test_fixture(self):
        with tempfile.TemporaryDirectory() as temp:
            home=Path(temp)
            for module in mod.RUNTIME_AGENT_MODULES:
                if module!="schemas":
                    (home/(module+".py")).write_bytes(
                        (mod.AGENTS/(module+".py")).read_bytes())
            with patch.object(mod,"AGENTS",home):
                with self.assertRaises(ValueError):
                    mod.source_files()

    def test_missing_runtime_module_fails_dependency_check(self):
        candidate=mod.source_files()
        candidate.pop("ai_agents/providers.py")
        with self.assertRaisesRegex(ValueError,"Undeclared ai_agents runtime import"):
            mod.verify_runtime_agent_imports(candidate)


    def test_extracted_zip_wrapper_registers_all_source_routes_offline(self):
        """Exercise the actual ZIP wrapper and route decorators after extraction.

        External services are deliberately stubbed: this is NOT a real Azure
        Functions host indexing, authenticated E2E or deployment test.
        """
        import subprocess
        import sys
        from zipfile import ZipFile

        stub_smoke = r'''
import ast
import pathlib
import sys
import types

root = pathlib.Path(sys.argv[1])
service = root / "azure-functions" / "campaign-api" / "function_app.py"
tree = ast.parse(service.read_text(encoding="utf-8"))
registrations = []

class FunctionApp:
    def __init__(self, **kwargs):
        self.registrations = registrations
    def __getattr__(self, name):
        if name not in ("route", "queue_trigger", "timer_trigger"):
            raise AttributeError(name)
        def decorator(**kwargs):
            def register(fn):
                registrations.append((name, kwargs, fn.__name__))
                return fn
            return register
        return decorator

azure = types.ModuleType("azure")
azure.__path__ = []
functions = types.ModuleType("azure.functions")
functions.FunctionApp = FunctionApp
functions.AuthLevel = types.SimpleNamespace(ANONYMOUS="anonymous")
for name in ("HttpRequest", "HttpResponse", "QueueMessage", "TimerRequest"):
    setattr(functions, name, type(name, (), {}))
azure.functions = functions
sys.modules["azure"] = azure
sys.modules["azure.functions"] = functions

# Only import-time service symbols are stubbed. Actual source module bytes,
# root wrapper, Python annotations and decorator registration are executed.
for node in tree.body:
    if isinstance(node, ast.ImportFrom) and node.level == 0:
        module = types.ModuleType(node.module)
        for alias in node.names:
            setattr(module, alias.name, type(alias.name, (), {}))
        sys.modules[node.module] = module

wrapper = root / "function_app.py"
namespace = {"__name__": "offline_zip_wrapper", "__file__": str(wrapper)}
exec(compile(wrapper.read_bytes(), str(wrapper), "exec"), namespace)
assert namespace["app"].registrations is registrations
expected = sum(
    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and sum(isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
            and isinstance(d.func.value, ast.Name) and d.func.value.id == "app"
            for d in node.decorator_list)
    for node in tree.body
)
assert len(registrations) == expected and expected >= 30, (len(registrations), expected)
queues = {kwargs["queue_name"] for kind, kwargs, _ in registrations
          if kind == "queue_trigger"}
assert {"retail-campaign-planning", "retail-reel-render",
        "retail-campaign-planning-poison", "retail-reel-render-poison",
        "retail-poster-render"} <= queues, queues
for kind, kwargs, _ in registrations:
    if kind == "queue_trigger":
        assert kwargs["connection"] == "RETAIL_STORAGE"
    if kind == "timer_trigger":
        assert kwargs["run_on_startup"] is False and kwargs["use_monitor"] is True
routes = [(kwargs["route"], tuple(kwargs.get("methods", [])))
          for kind, kwargs, _ in registrations if kind == "route"]
assert len(routes) == len(set(routes)), "Duplicate registered route/method pairs"
assert ("campaigns", ("POST",)) in routes
print("OFFLINE_EXTRACTED_ZIP_DECORATOR_SMOKE_OK", len(registrations))
'''
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            zip_path = folder / "source-only-fixture.zip"
            mod.write_zip(zip_path, mod.source_files())
            extracted = folder / "extracted"
            with ZipFile(zip_path) as archive:
                archive.extractall(extracted)
            result = subprocess.run(
                [sys.executable, "-I", "-c", stub_smoke, str(extracted)],
                capture_output=True, text=True, timeout=20, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("OFFLINE_EXTRACTED_ZIP_DECORATOR_SMOKE_OK", result.stdout)



if __name__=="__main__":
    unittest.main()
