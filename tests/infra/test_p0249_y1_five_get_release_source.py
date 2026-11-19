"""No-network release/rollback source parity for alternate Issue #249 Y1."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "ops/p0249-y1-readonly-extra-get"
sys.path.insert(0, str(DIR))
from build_five_get_release import FIVE_FILES, TWO_FILES, MODES, stage_release


class Y1FiveRouteReleaseSourceTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        from stage_five_get_sources import SOURCES
        for relative in SOURCES.values():
            src = ROOT / relative
            dst = self.repo / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)

    def stage(self, mode):
        output = self.root / ("staged-" + mode)
        self.assertEqual(stage_release(self.repo, output, mode), output)
        return output

    def test_five_get_originals_only(self):
        stage = self.stage("five")
        actual = {str(p.relative_to(stage)) for p in stage.rglob("*") if p.is_file()}
        self.assertEqual(actual, FIVE_FILES)
        self.assertEqual(set(p.parent.name for p in stage.glob("*/function.json")),
                         {"p0249_health", "campaign_read", "render_job_read",
                          "poster_job_read", "poster_draft_read"})
        self.assertNotIn("function_app.py", actual)

    def test_rollback_two_retains_exact_original_routes(self):
        stage = self.stage("rollback-two")
        actual = {str(p.relative_to(stage)) for p in stage.rglob("*") if p.is_file()}
        self.assertEqual(actual, TWO_FILES)
        self.assertEqual(set(p.parent.name for p in stage.glob("*/function.json")),
                         {"p0249_health", "campaign_read"})
        self.assertFalse((stage / "p0249_readonly_jobs.py").exists())
        self.assertFalse((stage / "poster_job_read").exists())

    def test_both_modes_use_verbatim_original_bytes(self):
        for mode in MODES:
            stage = self.stage(mode)
            from stage_five_get_sources import SOURCES
            for relative in MODES[mode][1]:
                with self.subTest(mode=mode, path=relative):
                    self.assertEqual((stage / relative).read_bytes(),
                                     (self.repo / SOURCES[relative]).read_bytes())

    def test_unknown_mode_denied_before_any_write(self):
        target = self.root / "unknown"
        with self.assertRaisesRegex(ValueError, "unapproved"):
            stage_release(self.repo, target, "six")
        self.assertFalse(target.exists())

    def test_deployable_package_is_not_implicitly_built(self):
        for mode in MODES:
            stage = self.stage(mode)
            self.assertFalse((stage / ".python_packages").exists())
            self.assertFalse((stage / "function_app.py").exists())
            self.assertFalse(any(p.suffix == ".zip" for p in stage.rglob("*")))

    def test_unvendored_original_http_dependency_rejected_before_stage(self):
        source = self.repo / "azure-functions/campaign-api/http_api.py"
        source.write_text(source.read_text() + "\nimport requests\n")
        with self.assertRaisesRegex(ValueError, "unvendored Y1 Python import"):
            stage_release(self.repo, self.root / "no-unpinned-import", "five")
        self.assertFalse((self.root / "no-unpinned-import").exists())

    def test_privileged_worker_dependency_rejected_before_stage(self):
        source = self.repo / "azure-functions/campaign-api/render_api.py"
        source.write_text(source.read_text() + "\nfrom admin_store import AdminStore\n")
        with self.assertRaisesRegex(ValueError, "unvendored Y1 Python import"):
            stage_release(self.repo, self.root / "no-admin-store", "five")
        self.assertFalse((self.root / "no-admin-store").exists())

    def test_unpinned_azure_storage_import_rejected_before_stage(self):
        source = self.repo / "ops/p0249-y1-readonly-extra-get/p0249_readonly_jobs.py"
        source.write_text(source.read_text() + "\nfrom azure.storage.queue import QueueClient\n")
        with self.assertRaisesRegex(ValueError, "unvendored Azure SDK import"):
            stage_release(self.repo, self.root / "no-azure-queue", "five")
        self.assertFalse((self.root / "no-azure-queue").exists())

    def test_azure_namespace_import_cannot_bypass_pinned_sdk(self):
        source = self.repo / "ops/p0249-y1-readonly-extra-get/p0249_readonly_jobs.py"
        source.write_text(source.read_text() + "\nfrom azure import storage\n")
        with self.assertRaisesRegex(ValueError, "unvendored Azure SDK import"):
            stage_release(self.repo, self.root / "no-unpinned-azure-module", "five")
        self.assertFalse((self.root / "no-unpinned-azure-module").exists())

    def test_relative_import_rejected_before_stage(self):
        source = self.repo / "azure-functions/campaign-api/http_api.py"
        source.write_text(source.read_text() + "\nfrom .unsafe import anything\n")
        with self.assertRaisesRegex(ValueError, "unreviewed relative Y1 import"):
            stage_release(self.repo, self.root / "no-relative-import", "rollback-two")
        self.assertFalse((self.root / "no-relative-import").exists())

    def test_fresh_process_indexes_all_approved_functions_without_secrets(self):
        """Test BOTH release shapes in a separate Python interpreter.

        The uv/pytest job MUST use real pinned azure.functions. The existing
        deployment check.sh also runs stdlib-only unittest, where a minimal
        SDK interface stand-in exercises the same no-JWT denial behavior.
        Both execute outside the checkout with user-site imports disabled
        in a separate interpreter: no original app/worker modules may leak into
        sys.modules or sys.path, and no hosted Auth or Azure calls are made.
        """
        script = textwrap.dedent("""
            import importlib.util
            import pathlib
            import sys
            import types

            # The full uv/pytest job installs the real Azure Functions SDK.
            # scripts/deploy/check.sh also runs this test under stdlib-only
            # Python; there a minimal SDK interface checks route behavior.
            try:
                import azure.functions as func
                sdk_mode = "real"
            except ModuleNotFoundError as error:
                assert error.name in ("azure", "azure.functions"), error
                sdk_mode = "stub"
                namespace = types.ModuleType("azure")
                namespace.__path__ = []
                func = types.ModuleType("azure.functions")
                class HttpRequest:
                    def __init__(self, method, url, headers, body, route_params):
                        self.method = method
                        self.url = url
                        self.headers = headers
                        self.body = body
                        self.route_params = route_params
                class HttpResponse:
                    def __init__(self, body, *, status_code, mimetype, headers):
                        self.body = body
                        self.status_code = status_code
                        self.mimetype = mimetype
                        self.headers = headers
                func.HttpRequest = HttpRequest
                func.HttpResponse = HttpResponse
                namespace.functions = func
                sys.modules["azure"] = namespace
                sys.modules["azure.functions"] = func

            root = pathlib.Path(sys.argv[1])
            expected = set(sys.argv[2].split(","))
            assert {p.parent.name for p in root.glob("*/function.json")} == expected
            sys.path.insert(0, str(root))
            params = {
                "campaign_read": "campaign_id",
                "render_job_read": "job_id",
                "poster_job_read": "job_id",
                "poster_draft_read": "draft_id",
            }
            uid = "11111111-1111-4111-8111-111111111111"
            for name in sorted(expected):
                spec = importlib.util.spec_from_file_location(
                    "p0249_test_" + name, root / name / "__init__.py")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                assert callable(module.main), name
                req = func.HttpRequest(
                    method="GET", url="https://example.invalid/api/" + name,
                    headers={}, body=b"", route_params={
                        params[name]: uid
                    } if name in params else {},
                )
                response = module.main(req)
                assert response.status_code == (200 if name == "p0249_health" else 401), (
                    name, response.status_code)
                assert response.headers.get("X-Request-ID"), name
            for lazy in ("http_api", "security", "tenant_store", "render_api",
                         "poster_render_api", "poster_draft_api"):
                assert lazy not in sys.modules, lazy
            print("P0249_Y1_FRESH_INDEX_AND_DENIAL=PASS SDK_MODE=" + sdk_mode)
        """)
        for mode, expected in (
            ("rollback-two", {"p0249_health", "campaign_read"}),
            ("five", {"p0249_health", "campaign_read", "render_job_read",
                      "poster_job_read", "poster_draft_read"}),
        ):
            stage = self.stage(mode)
            env = os.environ.copy()
            for key in ("RGAI_P0249_READONLY_SHADOW", "RGAI_P0249_EXTRA_GET_SHADOW",
                        "RETAIL_SUPABASE_URL", "RETAIL_SUPABASE_PUBLISHABLE_KEY"):
                env.pop(key, None)
            # uv run --with loads transient wheels into the parent process
            # even when sys.executable points at a base interpreter. Pass
            # only installed-package roots (never the checkout) to the
            # isolated child, so real Azure SDK imports resolve in CI.
            # stdlib-only check.sh has no Azure SDK; the subprocess then
            # uses a strict local stand-in. Under uv/pytest, require real SDK.
            import importlib.util
            azure_present = importlib.util.find_spec("azure") is not None
            if "pytest" in sys.modules:
                self.assertTrue(azure_present, "uv/pytest must load the pinned Azure SDK")
            installed = []
            if azure_present:
                import azure.functions as azure_functions
                installed.append(str(Path(azure_functions.__file__).resolve().parents[2]))
            installed.extend(str(Path(p).resolve()) for p in sys.path
                             if p and Path(p).is_dir()
                             and ({"site-packages", "dist-packages"} & set(Path(p).parts)))
            env["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(installed))
            proc = subprocess.run(
                [sys.executable, "-s", "-c", script, str(stage),
                 ",".join(sorted(expected))],
                cwd=self.root, env=env, check=False, text=True,
                capture_output=True, timeout=30,
            )
            self.assertEqual(proc.returncode, 0, msg=mode + " " + proc.stdout + proc.stderr)
            self.assertIn("P0249_Y1_FRESH_INDEX_AND_DENIAL=PASS", proc.stdout)
            self.assertIn("SDK_MODE=" + ("real" if azure_present else "stub"), proc.stdout)

    def test_no_http_write_or_worker_route_in_either_mode(self):
        for mode in MODES:
            stage = self.stage(mode)
            for manifest in stage.glob("*/function.json"):
                with self.subTest(mode=mode, manifest=manifest):
                    bindings = json.loads(manifest.read_text())["bindings"]
                    self.assertEqual(len(bindings), 2)
                    self.assertEqual([b["type"] for b in bindings],
                                     ["httpTrigger", "http"])
                    self.assertEqual(bindings[0]["methods"], ["get"])


if __name__ == "__main__":
    unittest.main()
