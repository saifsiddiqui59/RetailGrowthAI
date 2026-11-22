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

    def test_native_binary_linked_parent_is_rejected_before_execution(self):
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real"
            real.mkdir()
            binary = real / "node"
            binary.write_text("not executable", encoding="utf-8")
            alias = root / "current"
            alias.symlink_to(real, target_is_directory=True)
            with patch.object(module.subprocess, "check_output") as execute:
                with self.assertRaisesRegex(ValueError, "linked native dependency"):
                    module._version(alias / "node", ["--version"], r"^v22\\.")
                execute.assert_not_called()

    def test_runtime_dependency_symlinks_rejected_before_archive(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dependencies = root / "dependencies"
            dependencies.mkdir()
            real = dependencies / "real.py"
            real.write_text("safe", encoding="utf-8")
            (dependencies / "alias.py").symlink_to(real)
            with self.assertRaisesRegex(ValueError, "Symlink in F4 package"):
                module._collect_tree(dependencies, "deps")
            (dependencies / "alias.py").unlink()
            nested = dependencies / "nested"
            nested.mkdir()
            (nested / "payload.py").write_text("safe", encoding="utf-8")
            (dependencies / "linked_dir").symlink_to(nested, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "Symlink in F4 package"):
                module._collect_tree(dependencies, "deps")

    @unittest.skipUnless(hasattr(__import__("os"), "mkfifo"), "POSIX FIFO required")
    def test_fifo_dependency_rejected_before_archive_read(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            os.mkfifo(root / "blocking.pipe")
            with self.assertRaisesRegex(ValueError, "Non-regular F4 package dependency"):
                module._collect_tree(root, "deps")

    @unittest.skipUnless(hasattr(__import__("os"), "mkfifo"), "POSIX FIFO required")
    def test_fifo_archive_source_rejected_before_read(self):
        import os
        import tempfile
        from zipfile import ZipFile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pipe = root / "blocking.pipe"
            os.mkfifo(pipe)
            with ZipFile(root / "artifact.zip", "w") as archive:
                with self.assertRaisesRegex(ValueError, "Unsafe non-regular F4 archive source"):
                    module._write_member(archive, "deps/blocking.pipe", pipe)

    def test_archive_source_with_linked_parent_is_rejected(self):
        import tempfile
        from zipfile import ZipFile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            actual = root / "actual"
            actual.mkdir()
            (actual / "payload.txt").write_text("synthetic", encoding="utf-8")
            alias = root / "linked"
            alias.symlink_to(actual, target_is_directory=True)
            with ZipFile(root / "artifact.zip", "w") as archive:
                with self.assertRaisesRegex(ValueError, "linked F4 archive source"):
                    module._write_member(archive, "deps/payload.txt", alias / "payload.txt")
                self.assertEqual(archive.namelist(), [])

    def test_archive_member_traversal_rejected_before_read(self):
        import tempfile
        from zipfile import ZipFile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / "payload.txt"
            payload.write_text("synthetic", encoding="utf-8")
            with ZipFile(root / "artifact.zip", "w") as archive:
                for unsafe in ("../escape", "/absolute", "deps/../escape",
                               "deps//double", "deps/./dot", "deps\\\\windows"):
                    with self.subTest(member=unsafe):
                        with self.assertRaisesRegex(ValueError, "Unsafe F4 archive member"):
                            module._write_member(archive, unsafe, payload)
                self.assertEqual(archive.namelist(), [])

    def test_duplicate_archive_member_rejected_without_overwriting(self):
        import tempfile
        from zipfile import ZipFile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / "payload.txt"
            payload.write_text("synthetic", encoding="utf-8")
            with ZipFile(root / "artifact.zip", "w") as archive:
                module._write_member(archive, "deps/payload.txt", payload)
                with self.assertRaisesRegex(ValueError, "Duplicate F4 archive member"):
                    module._write_member(archive, "deps/payload.txt", payload)
                self.assertEqual(archive.namelist(), ["deps/payload.txt"])

    def test_oversized_member_refused_before_read_or_zip_write(self):
        import tempfile
        from unittest.mock import patch
        from zipfile import ZipFile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / "oversized.bin"
            payload.write_bytes(b"synthetic")
            with ZipFile(root / "artifact.zip", "w") as archive:
                with patch.object(module, "MAX_ARCHIVE", 4):
                    with patch.object(Path, "read_bytes", side_effect=AssertionError("read attempted")):
                        with self.assertRaisesRegex(ValueError, "exceeds 1GB limit"):
                            module._write_member(archive, "deps/oversized.bin", payload)
                self.assertEqual(archive.namelist(), [])

    def test_archive_member_streams_and_matches_sha256(self):
        import hashlib
        import tempfile
        from zipfile import ZipFile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / "large-synthetic.bin"
            data = b"synthetic-private-free" * 100000
            payload.write_bytes(data)
            archive_path = root / "artifact.zip"
            with ZipFile(archive_path, "w") as archive:
                digest = module._write_member(archive, "deps/payload.bin", payload)
            self.assertEqual(digest, hashlib.sha256(data).hexdigest())
            with ZipFile(archive_path) as archive:
                self.assertEqual(archive.read("deps/payload.bin"), data)

    def test_npm_bin_shims_excluded_but_runtime_links_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".bin").mkdir()
            (root / "lib").mkdir()
            runtime = root / "lib" / "module.js"
            runtime.write_text("synthetic", encoding="utf-8")
            (root / ".bin" / "module").symlink_to(runtime)
            listing = module._collect_tree(root, "node_modules", omit_bin_shims=True)
            self.assertEqual(set(listing), {"node_modules/lib/module.js"})
            with self.assertRaisesRegex(ValueError, "Symlink in F4 package"):
                module._collect_tree(root, "node_modules")
            (root / "lib" / "alias.js").symlink_to(runtime)
            with self.assertRaisesRegex(ValueError, "Symlink in F4 package"):
                module._collect_tree(root, "node_modules", omit_bin_shims=True)

    def test_dependency_root_symlink_is_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            actual = root / "real"
            actual.mkdir()
            (actual / "payload.py").write_text("safe", encoding="utf-8")
            alias = root / "linked"
            alias.symlink_to(actual, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "linked offline build dependency"):
                module._collect_tree(alias, "deps")

    def test_dependency_root_with_linked_ancestor_is_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            actual = root / "real"
            dependencies = actual / "node_modules"
            dependencies.mkdir(parents=True)
            (dependencies / "payload.js").write_text("synthetic", encoding="utf-8")
            alias = root / "linked"
            alias.symlink_to(actual, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "linked offline build dependency"):
                module._collect_tree(alias / "node_modules", "deps")

    def test_linked_source_directory_rejected(self):
        import tempfile
        import shutil
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            actual = root / "actual"
            actual.mkdir()
            for name in ("host.json", "requirements.txt", *module.SERVICE_MODULES):
                shutil.copy2(module.SERVICE / name, actual / name)
            alias = root / "linked"
            alias.symlink_to(actual, target_is_directory=True)
            with patch.object(module, "SERVICE", alias):
                with self.assertRaisesRegex(ValueError, "Linked Feature4 package source directory"):
                    module.sources()

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
