"""F4 separate worker release guard, compatible with pytest AND unittest discovery."""
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "scripts" / "deploy" / "package_feature4_cpu.py"
spec = importlib.util.spec_from_file_location("f4_cpu_packager", PACKAGE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Feature4CpuWorkerPackageTests(unittest.TestCase):
    def test_source_manifest_preserves_v1_boundary(self):
        entries = module.sources()
        required = {"function_app.py", "cpu_backend.py", "admin_store.py",
                    "feature4_worker_handoff.py", "render_adapter.py",
                    "hyperframes/render.mjs", "host.json"}
        self.assertLessEqual(required, set(entries))
        self.assertNotIn("render_worker.py", entries)
        self.assertNotIn("http_api.py", entries)
        self.assertEqual(len(entries), len(set(entries)))
        for member in entries:
            self.assertTrue(member and ".." not in Path(member).parts)

    def test_source_only_preflight_requires_no_hosted_credentials(self):
        run = subprocess.run([sys.executable, str(PACKAGE), "--check"],
                             capture_output=True, text=True, timeout=20)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("PASS Feature4 isolated worker sources", run.stdout)

    def test_build_without_pinned_native_dependencies_must_refuse(self):
        class Args:
            node = ffmpeg = ffprobe = python_site_packages = puppeteer_cache = output = None
        with self.assertRaises((TypeError, ValueError)):
            module.build(Args())

    def test_native_binary_symlink_is_rejected_before_version_execution(self):
        import tempfile
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "real-node"
            target.write_text("not executable", encoding="utf-8")
            link = root / "node"
            link.symlink_to(target)
            args = SimpleNamespace(node=str(link), ffmpeg=str(target),
                                   ffprobe=str(target),
                                   python_site_packages=str(root),
                                   puppeteer_cache=str(root),
                                   output=str(root / "worker.zip"))
            with self.assertRaisesRegex(ValueError, "linked native dependency"):
                module.build(args)
            self.assertFalse((root / "worker.zip").exists())

    def test_native_worker_not_silently_added_to_protected_v1_zip(self):
        old = (ROOT / "scripts" / "deploy" / "package.py").read_text(encoding="utf-8")
        self.assertIn(
            'RUNTIME_VIDEO_MODULES = frozenset({"render", "probe", "asset_preflight"})',
            old)
        isolated = (ROOT / "azure-functions" / "feature4-cpu-worker" /
                    "function_app.py").read_text(encoding="utf-8")
        self.assertNotIn("retail-reel-render", isolated)
        self.assertIn("PUPPETEER_EXECUTABLE_PATH", isolated)
        self.assertIn("_DenyRedirects", isolated)
