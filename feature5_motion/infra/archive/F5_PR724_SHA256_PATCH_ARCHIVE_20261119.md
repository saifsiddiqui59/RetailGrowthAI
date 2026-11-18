# Feature5 draft #724 exact source patch archive — 2026-11-19

Original [PR #724](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/724) HEAD `359221f2bd198ce498c01e1807b59f4284fb9227` (4 full changed-file patches) is stacked on obsolete F5 branch, not directly eligible for main. It adds an opt-in full mounted Azure Files model readback path; as written, a full read may incur 34GB+ Azure Files transactions and must NEVER be executed by CI, as a model generation shortcut, or without separately authorized operator cost controls.

Original Feature5 parent #323 / stacked #465 remain OPEN/DRAFT; original F5-14 source isn't hosted tested or accepted. Preserve exact original source, tests and handoff to allow future current-main compatible review, **do not** restore old GPU/weights model storage settings or start cloud infrastructure. Full model data was explicitly requested not to be re-created. Archive does not claim full user-rights/model-license acceptance.

## docs/feature5/F5_22_TASK_DEPENDENCIES_20261029.json
~~~~diff
@@ -117,7 +117,8 @@
       "dependency_id": "F5-WEIGHTS",
       "owner": "Feature5/Runtime",
       "required_output": "read-only mounted actual Wan checkpoint files",
-      "acceptance_criteria": "Stream full original 3 files, exact SHA/size"
+      "acceptance_criteria": "Stream full original 3 files, exact SHA/size",
+      "source_progress": "GPU-OFF optional full SHA-256 mounted-byte scanner and tiny-local-fixture negative tests proposed on feat/feature5-readonly-model-sha256-audit-20261030; actual 34GB readback, approved runtime and exact-head CI NOT yet verified. Do not count as DONE."
     },
     {
       "task": 15,
~~~~

## feature5_motion/infra/FEATURE35_SHARED_MOUNT_HANDOFF.md
~~~~diff
@@ -97,3 +97,10 @@ Read-only source inspection at pinned official Comfy-Org/workflow_templates comm
 - Additional launch safety: even a correctly formatted immutable job image is **not** sufficient; execution now requires `RETAIL_F5_REVIEWED_RUNTIME_IMAGE` to EXACTLY equal the reviewed `registry/image@sha256:<64 hex>` of the actual deployed job. Missing/other hash and tags such as `latest` fail closed independently of manual paid approval, runtime/tenant eligibility and spend quote. This is a source-only gate; NO actual pinned image was built or supplied by us.
 - Model licensing: the FLUX.2 Klein 4B/Qwen3/Wan 5B model licenses require their exact dependency/source notices; ComfyUI itself is GPL-3.0. Commercial SaaS is not necessarily forbidden, but distribution/source obligations must be professionally reviewed before release. Do not mark rights approved or generate with unapproved customer photographs.
 - The still-open source PRs #323 (Feature5 runtime) and stacked draft #465 remain integration/QA-gated; preserve part owner scope and coordinator files. No WineShopPOS/PROD changes.
+
+## 2026-10-30 — Feature5 F5-14 full original-byte readback source (GPU OFF)
+
+- Added an **explicit operator-only** `verify_mounted_sha256(root)` to `feature5_motion/shared_model_mount.py`. It opens each pinned file through no-follow directory descriptors, refuses symlinked parent components and nonregular/wrong-sized files, streams at most 4 MiB per read, checks stable file identity/size/timestamps and compares the full SHA-256 against the six pinned staging digests. No cloud APIs, model downloads, inference or write operations are in this function.
+- A full share scan reads **34,277,265,757 bytes** and can incur remote Azure Files I/O/transaction costs. It is **never automatic**; the CLI requires all of `--mounted-root /mnt/retailgrowth-models --verify-sha256 --confirm-full-scan`. Do not invoke against Azure without separate operator cost/permission approval. Existing default `--mounted-root` remains a cheap metadata-only check.
+- Added CPU-only tiny-local-file tests for successful digest readback, same-size tampering, symlinked ancestor denial and the two required explicit CLI flags. These tests use no genuine model weights and are **not** evidence of actual mounted checkpoint integrity.
+- **F5-14 stays IN PROGRESS:** no full 34GB readback was performed, no protected running container mount was accessed, and there is no runtime ABI/licensing approval. F5-13 OCI digest/SBOM, F5-15 protected ComfyUI node inventory, F5-16 paid authorization and F5-17 genuine Wan inference remain independently gated. This branch is a source-only review proposal; the coordinator alone integrates and updates canonical shared status.
~~~~

## feature5_motion/shared_model_mount.py
~~~~diff
@@ -6,9 +6,12 @@
 """
 from __future__ import annotations
 import argparse
+from contextlib import ExitStack
+from hashlib import sha256
 import json
 import os
 import re
+import stat
 from pathlib import Path, PurePosixPath
 
 ACCOUNT = "rgaimodelseastus26"
@@ -70,18 +73,82 @@ def validate_manifest(obj):
     return revisions
 
 
+def _open_model_fd(root, relative):
+    """Open every path component without following links, including parent dirs.
+
+    This is a local, read-only Linux preflight; it never fetches model bytes from
+    Azure APIs. A platform without dir_fd/O_NOFOLLOW support must fail closed.
+    """
+    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
+        raise PreflightError("Secure mounted-file inspection requires POSIX no-follow opens")
+    if relative not in EXPECTED:
+        raise PreflightError("Model path not in the pinned inventory")
+    parts = PurePosixPath(relative).parts
+    dir_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
+    file_flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
+    try:
+        with ExitStack() as stack:
+            directory_fd = os.open(os.fspath(root), dir_flags)
+            stack.callback(os.close, directory_fd)
+            for part in parts[:-1]:
+                directory_fd = os.open(part, dir_flags, dir_fd=directory_fd)
+                stack.callback(os.close, directory_fd)
+            return os.open(parts[-1], file_flags, dir_fd=directory_fd)
+    except (OSError, ValueError, TypeError) as exc:
+        raise PreflightError("Cannot securely open mounted model: " + relative) from exc
+
+
+def _checked_stat(fd, relative, expected_size):
+    info = os.fstat(fd)
+    if not stat.S_ISREG(info.st_mode) or info.st_size != expected_size:
+        raise PreflightError("Missing, nonregular or wrong-sized model: " + relative)
+    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
+
+
 def check_mounted_files(root):
     """Cheap, optional filesystem STAT check only; no large file re-read."""
-    base = Path(root)
-    if not base.is_dir() or base.is_symlink():
-        raise PreflightError("Private model root not mounted as a directory")
     for relative, (size, _, _) in EXPECTED.items():
-        file = base.joinpath(*PurePosixPath(relative).parts)
-        if file.is_symlink() or not file.is_file() or file.stat().st_size != size:
-            raise PreflightError("Missing, symlinked or wrong-sized model: " + relative)
+        fd = _open_model_fd(root, relative)
+        try:
+            _checked_stat(fd, relative, size)
+        finally:
+            os.close(fd)
     return True
 
 
+def verify_mounted_sha256(root):
+    """Explicit opt-in: stream ALL mounted model bytes and compare pinned hashes.
+
+    This can read over 34 GB from an existing mount. Never call automatically
+    from CI, GPU start, metadata preflight or a paid cloud operation.
+    """
+    verified = {}
+    for relative, (expected_size, expected_digest, _) in EXPECTED.items():
+        fd = _open_model_fd(root, relative)
+        try:
+            original = _checked_stat(fd, relative, expected_size)
+            digest = sha256()
+            total = 0
+            while True:
+                chunk = os.read(fd, 4 * 1024 * 1024)
+                if not chunk:
+                    break
+                total += len(chunk)
+                if total > expected_size:
+                    raise PreflightError("Mounted model grew during SHA-256 scan: " + relative)
+                digest.update(chunk)
+            if total != expected_size or _checked_stat(fd, relative, expected_size) != original:
+                raise PreflightError("Mounted model changed during SHA-256 scan: " + relative)
+            if digest.hexdigest() != expected_digest:
+                raise PreflightError("Mounted model SHA-256 mismatch: " + relative)
+            verified[relative] = digest.hexdigest()
+        except OSError as exc:
+            raise PreflightError("Mounted model read failed: " + relative) from exc
+        finally:
+            os.close(fd)
+    return verified
+
+
 def comfy_extra_paths():
     """ComfyUI built-in extra_model_paths YAML; same mounted share, no copies."""
     return (
@@ -124,14 +191,24 @@ def main(argv=None):
     p = argparse.ArgumentParser(description="No-network, no-GPU shared FLUX/Wan mount preflight")
     p.add_argument("--manifest", help="Locally provided copy of private Azure completion manifest")
     p.add_argument("--mounted-root", help="Optional existing mounted path for stat-only check")
+    p.add_argument("--verify-sha256", action="store_true", help="Opt-in full original-byte scan of all six models (>34GB I/O)")
+    p.add_argument("--confirm-full-scan", action="store_true", help="Explicitly acknowledge full read-only model-share I/O")
     p.add_argument("--format", choices=["plan", "yaml"], default="plan")
     args = p.parse_args(argv)
+    if args.verify_sha256 and (not args.mounted_root or not args.confirm_full_scan):
+        p.error("--verify-sha256 requires --mounted-root and --confirm-full-scan")
+    if args.confirm_full_scan and not args.verify_sha256:
+        p.error("--confirm-full-scan requires --verify-sha256")
     if args.manifest:
         with open(args.manifest, encoding="utf8") as f:
             print("Manifest revisions validated:", json.dumps(validate_manifest(json.load(f)), sort_keys=True))
     if args.mounted_root:
         check_mounted_files(args.mounted_root)
-        print("Six mounted model paths and byte counts pass STAT-only check (not SHA rehash)")
+        if args.verify_sha256:
+            verified = verify_mounted_sha256(args.mounted_root)
+            print(f"{len(verified)} mounted model files passed full SHA-256 readback (not a GPU or licensing approval)")
+        else:
+            print("Six mounted model paths and byte counts pass STAT-only check (not SHA rehash)")
     print(comfy_extra_paths() if args.format == "yaml" else json.dumps(job_volume_fragment(), indent=2))
     return 0
 
~~~~

## tests/ai/test_feature5_shared_model_mount.py
~~~~diff
@@ -1,7 +1,9 @@
 """CPU-only, zero-cloud tests for shared Feature3/Feature5 Azure Files mount plan."""
+from hashlib import sha256
 import json
 import tempfile
 import unittest
+from unittest.mock import patch
 from pathlib import Path
 from feature5_motion import shared_model_mount as m
 
@@ -78,5 +80,46 @@ def test_mounted_files_must_exist_and_not_be_symlinks(self):
                 m.check_mounted_files(bad_root)
 
 
+    def test_explicit_full_sha256_readback_of_small_local_fixture_only(self):
+        """Never read the actual 34GB Azure share in automated tests."""
+        relative = "feature5/vae/wan2.2_vae.safetensors"
+        original = b"tiny CPU-only fixture, NOT real Wan weights"
+        with tempfile.TemporaryDirectory() as temp:
+            path = Path(temp) / relative
+            path.parent.mkdir(parents=True)
+            path.write_bytes(original)
+            expected = {relative: (len(original), sha256(original).hexdigest(), "fixture-only")}
+            with patch.dict(m.EXPECTED, expected, clear=True):
+                self.assertTrue(m.check_mounted_files(temp))
+                self.assertEqual(m.verify_mounted_sha256(temp), {relative: sha256(original).hexdigest()})
+                # Same byte count and metadata shape do not establish integrity.
+                path.write_bytes(b"x" * len(original))
+                self.assertTrue(m.check_mounted_files(temp))
+                with self.assertRaisesRegex(m.PreflightError, "SHA-256 mismatch"):
+                    m.verify_mounted_sha256(temp)
+
+    def test_full_scan_rejects_parent_directory_symlinks(self):
+        relative = "feature5/vae/wan2.2_vae.safetensors"
+        payload = b"safe synthetic bytes"
+        with tempfile.TemporaryDirectory() as temp:
+            real = Path(temp) / "actual" / "vae"
+            real.mkdir(parents=True)
+            (real / "wan2.2_vae.safetensors").write_bytes(payload)
+            (Path(temp) / "feature5").symlink_to(Path(temp) / "actual", target_is_directory=True)
+            with patch.dict(m.EXPECTED, {relative: (len(payload), sha256(payload).hexdigest(), "fixture")}, clear=True):
+                with self.assertRaises(m.PreflightError):
+                    m.check_mounted_files(temp)
+                with self.assertRaises(m.PreflightError):
+                    m.verify_mounted_sha256(temp)
+
+    def test_full_scan_never_runs_without_two_explicit_cli_flags(self):
+        with tempfile.TemporaryDirectory() as temp:
+            for args in (["--verify-sha256"], ["--verify-sha256", "--mounted-root", temp],
+                         ["--confirm-full-scan", "--mounted-root", temp]):
+                with self.subTest(args=args), self.assertRaises(SystemExit) as caught:
+                    m.main(args)
+                self.assertEqual(caught.exception.code, 2)
+
+
 if __name__ == "__main__":
     unittest.main()
~~~~

## Outstanding
Original F5-14 secure mounted-volume full SHA source implementation, relevance to currently staged weights/removed models, permitted Azure Files transaction cost and independent F3/F5 model security review must be reconsidered before enabling. GPU OFF; no paid AI, Azure resource mutation, PROD or WineShopPOS.