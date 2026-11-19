# F5 historical parent #323 original patch hunks — part 2 of 2

- Source head: `ffc464c09f719a0bfb6b15b5c34608f89d76234b`; original PR https://github.com/saifsiddiqui59/RetailGrowthAI/pull/323
- This file preserves 15 original GitHub changed-file patch hunks *exactly*. This is non-executing archive data, not recovered F5 runtime integration.
- Current-main recovery already merged: #1011 GPU-OFF manifest/contract subset with exact-head + postmerge 4/4; #1013 human QA source is a separate active cross-feature review PR. Do not overwrite newer current main with historical worker, pricing or Azure GPU deployment code.
- Original Feature5 22 task IDs and #125/#724 review/rights remain open; no weights, model execution, GPU, remote Azure Files readback, paid services, PROD or WineShopPOS are authorized by this archive.

## feature5_motion/worker.py

~~~~diff
@@ -0,0 +1,218 @@
+"""Source-only worker boundary: authoritative DB claim/reservation are injected.
+
+Never launch this directly from customer HTTP. Production persistence and credit
+reservation MUST be provided by the coordinator's EXISTING ledger/RLS subsystem.
+"""
+from __future__ import annotations
+
+import json
+from decimal import Decimal, InvalidOperation
+from pathlib import Path
+import shutil
+import subprocess
+from time import monotonic
+from typing import Protocol
+
+from .contracts import MotionError, MotionSpec, AssetGrant, canonical_uuid, validate_source
+from .azure_pricing import MotionSpendGuard
+
+
+class ReconciliationRequired(MotionError):
+    """Unknown paid outcome: never convert to FAILED or automatically refund."""
+
+
+class JobStore(Protocol):
+    def claim(self, job_id: str) -> dict | None: ...
+    def complete(self, job_id: str, attempt_token: str, media_record: dict) -> bool: ...
+    def fail(self, job_id: str, attempt_token: str, category: str) -> bool: ...
+    def mark_unknown(self, job_id: str, attempt_token: str, category: str) -> bool: ...
+
+
+class TenantMedia(Protocol):
+    def grant(self, shop_id: str, asset_id: str) -> AssetGrant: ...
+    def stage(self, shop_id: str, asset_id: str, workdir: Path) -> Path: ...
+    def upload_private(self, shop_id: str, job_id: str, attempt_token: str, path: Path, metadata: dict) -> dict: ...
+
+
+def validate_clip(path: Path, *, ffprobe="ffprobe", max_bytes=80 * 1024 * 1024) -> dict:
+    """Read file-only local MP4; machine metrics only, NOT garment visual QA."""
+    path = Path(path).resolve(strict=True)
+    if not path.is_file() or path.suffix.lower() != ".mp4" or not 0 < path.stat().st_size <= max_bytes:
+        raise MotionError("Invalid generated clip")
+    try:
+        result = subprocess.run([ffprobe, "-v", "error", "-protocol_whitelist", "file",
+                                 "-show_entries", "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
+                                 "-of", "json", str(path)], capture_output=True, timeout=20, check=True)
+        data = json.loads(result.stdout[:20000])
+        streams = data.get("streams", [])
+        video = [s for s in streams if s.get("codec_type") == "video"]
+        duration = float(data["format"]["duration"])
+        if len(video) != 1 or video[0].get("codec_name") != "h264" or not 4.5 <= duration <= 5.5:
+            raise ValueError("Unexpected codec or duration")
+        w, h = int(video[0]["width"]), int(video[0]["height"])
+        if min(w, h) < 256 or max(w, h) > 1280 or (w, h) not in ((480, 832), (832, 480), (480, 854), (854, 480)):
+            raise ValueError("Unapproved generated dimensions")
+        rate = video[0].get("r_frame_rate")
+        if rate != "24/1":
+            raise ValueError("Unexpected frame rate")
+        return {"codec": "h264", "container": "mp4", "duration_seconds": duration,
+                "width": w, "height": h, "fps": 24, "bytes": path.stat().st_size}
+    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
+        raise MotionError("Generated clip did not pass local media validation") from exc
+
+
+def _valid_amount(amount):
+    """A NaN/Infinity/bool must never disable a monetary approval ceiling."""
+    if isinstance(amount, bool):
+        return None
+    try:
+        value = Decimal(str(amount))
+    except (InvalidOperation, ValueError, TypeError):
+        return None
+    return value if value.is_finite() and value > 0 else None
+
+
+class MotionWorker:
+    def __init__(self, *, store: JobStore, media: TenantMedia, runner, workdir_root: Path,
+                 enabled: bool = False, credit_cap_usd: float = 0,
+                 cost_guard: MotionSpendGuard | None = None):
+        self.store, self.media, self.runner = store, media, runner
+        self.root = Path(workdir_root)
+        self.enabled = enabled
+        self.credit_cap_usd = credit_cap_usd
+        self.cost_guard = cost_guard
+
+    def execute(self, job_id: str) -> str:
+        jid = canonical_uuid(job_id)
+        cap = _valid_amount(self.credit_cap_usd)
+        if not self.enabled or cap is None:
+            raise MotionError("Premium motion worker disabled")
+        if not isinstance(self.cost_guard, MotionSpendGuard):
+            raise MotionError("GPU cost ceiling must be reviewed before any claim")
+        maximum_cost = self.cost_guard.minimum_reservation_usd()
+        runner_limit = getattr(self.runner, "timeout_seconds", None)
+        if (type(runner_limit) is not int or
+            runner_limit > self.cost_guard.max_billable_seconds or
+            maximum_cost > cap):
+            raise MotionError("GPU runtime exceeds reserved spending ceiling")
+        claim = self.store.claim(jid)  # Must be atomic DB lease + existing reserved quota.
+        if claim is None:
+            return "NOT_CLAIMED"
+        token = canonical_uuid(claim["attempt_token"])  # DB-owned fenced claim, no traversal.
+        spec = claim["spec"]
+        if not isinstance(spec, MotionSpec) or spec.job_id != jid:
+            raise MotionError("Invalid authoritative job claim")
+        reservation = _valid_amount(claim.get("reserved_usd"))
+        if (reservation is None or reservation > cap or reservation < maximum_cost
+            or claim.get("review_status") != "APPROVED"):
+            raise MotionError("Existing ledger reservation cannot cover worst-case GPU spend")
+        workdir = None
+        # Once the runner is invoked, even an exception may follow a charged
+        # GPU subprocess. A retry/refund must wait for durable reconciliation.
+        generation_attempted = False
+        try:
+            grant = self.media.grant(spec.shop_id, spec.source_asset_id) if spec.source_asset_id else None
+            validate_source(spec, grant)
+            if self.root.is_symlink():
+                raise MotionError("Private job root must not be a symlink")
+            root = self.root.resolve(strict=True)
+            if not root.is_dir():
+                raise MotionError("Private job root is missing")
+            job_dir = root / jid
+            if job_dir.is_symlink():
+                raise MotionError("Symlinked job directory rejected")
+            job_dir.mkdir(mode=0o700, exist_ok=True)
+            if not job_dir.is_dir():
+                raise MotionError("Invalid job directory")
+            workdir = job_dir / token
+            workdir.mkdir(mode=0o700, exist_ok=False)
+            source = self.media.stage(spec.shop_id, spec.source_asset_id, workdir) if grant else None
+            started = monotonic()
+            generation_attempted = True
+            output = self.runner.run(spec, source_file=source, workdir=workdir)
+            model_elapsed = max(0.0, monotonic() - started)
+            if model_elapsed > self.cost_guard.max_billable_seconds:
+                # An unexpectedly costly operation must never be auto retried.
+                if not self.store.mark_unknown(jid, token, "GPU_RUNTIME_OVER_CAP"):
+                    raise ReconciliationRequired("GPU overrun reconciliation required")
+                return "UNKNOWN"
+            inferred_cost = self.cost_guard.estimated_spend_for_observed_inference_usd(
+                model_elapsed
+            )
+            if not Path(output).resolve().is_relative_to(workdir.resolve()):
+                raise MotionError("Generated output escaped private job directory")
+            info = validate_clip(output)
+            info.update({"motion_job_id": jid, "shop_id": spec.shop_id,
+                         "source_asset_id": spec.source_asset_id, "provider": "hunyuan-video-1.5",
+                         "prompt_version": spec.prompt_version, "seed": spec.seed,
+                         "license_status": "PENDING_FINAL_REVIEW", "quality_review_required": True,
+                         "reserved_usd": str(reservation),
+                         "compute_seconds_measured": round(model_elapsed, 3),
+                         "estimated_observed_compute_usd": str(inferred_cost),
+                         "maximum_compute_budget_usd": str(maximum_cost)})
+            # An upload timeout may happen AFTER private bytes were accepted.
+            # Never declare refundable FAILED or start inference again.
+            try:
+                receipt = self.media.upload_private(spec.shop_id, jid, token, output, info)
+            except Exception:
+                if not self.store.mark_unknown(jid, token, "PRIVATE_UPLOAD_UNCERTAIN"):
+                    raise ReconciliationRequired("Private upload reconciliation required")
+                return "UNKNOWN"
+            expected_path = f"{spec.shop_id}/renders/{jid}/{token}.mp4"
+            # Same exact, lease-scoped tenant-private path required by Part3 importer.
+            # A matching prefix is insufficient: disallow wrong lease, bucket or owner.
+            receipt_ok = (
+                isinstance(receipt, dict)
+                and receipt.get("shop_id") == spec.shop_id
+                and receipt.get("job_id") == jid
+                and receipt.get("attempt_token") == token
+                and receipt.get("bucket") == "retailgrowth-media"
+                and receipt.get("path") == expected_path
+                and receipt.get("private") is True
+            )
+            if not receipt_ok:
+                if not self.store.mark_unknown(jid, token, "PRIVATE_RECEIPT_INVALID"):
+                    raise ReconciliationRequired("Private output receipt reconciliation required")
+                return "UNKNOWN"
+        except ReconciliationRequired:
+            # Store cannot persist UNKNOWN; fail closed rather than falsifying
+            # billability or allowing another costly provider invocation.
+            raise
+        except Exception:
+            # A subprocess can have spent money before failing, timing out, or
+            # producing an invalid MP4. Such attempts MUST NOT be recorded as
+            # refundable FAILED or replayed by a queue worker automatically.
+            # Validation and staging failures before launch are safely FAILED.
+            if generation_attempted:
+                try:
+                    persisted = self.store.mark_unknown(jid, token, "GPU_ATTEMPT_UNCERTAIN")
+                except Exception as exc:
+                    raise ReconciliationRequired(
+                        "GPU attempt requires manual reconciliation"
+                    ) from exc
+                if not persisted:
+                    raise ReconciliationRequired(
+                        "GPU attempt requires manual reconciliation"
+                    )
+                return "UNKNOWN"
+            if not self.store.fail(jid, token, "PRE_GPU_VALIDATION_FAILURE"):
+                raise MotionError("Pre-GPU failure state cannot be recorded")
+            return "FAILED"
+        finally:
+            if workdir is not None and workdir.is_dir() and not workdir.is_symlink():
+                # No source photo or motion clip left on warm/idle worker disk.
+                # Only sanitized DB receipts survive; ephemeral worker runtime
+                # must also enforce automatic disk disposal on termination.
+                shutil.rmtree(workdir, ignore_errors=True)
+        # Finalization is outside the generic failure handler: a private output
+        # was already uploaded and its status/charges must be reconciled.
+        try:
+            completed = self.store.complete(jid, token, receipt)
+        except Exception:
+            # DB timeout may mean the completion transaction actually committed.
+            completed = False
+        if not completed:
+            if not self.store.mark_unknown(jid, token, "FINALIZE_UNCERTAIN"):
+                raise MotionError("Finalization unknown; manual ledger reconciliation required")
+            return "UNKNOWN"
+        return "SUCCEEDED"
~~~~

## tests/ai/test_feature5_artifact_lock.py

~~~~diff
@@ -0,0 +1,140 @@
+"""Feature #5 model artifact integrity negative tests; no GPU or external weights."""
+import hashlib
+import json
+import sys
+import tempfile
+import unittest
+from pathlib import Path
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT))
+
+from feature5_motion.artifact_lock import (
+    ArtifactLock, construct_manifest, MAX_FILE_BYTES,
+)
+from feature5_motion.contracts import MotionError
+from feature5_motion.seal_artifacts import create_candidate
+
+
+class TestHunyuanModelArtifactLock(unittest.TestCase):
+    def setUp(self):
+        self.tmp = tempfile.TemporaryDirectory(prefix="feature5-artifact-fixture-")
+        self.addCleanup(self.tmp.cleanup)
+        self.base = Path(self.tmp.name)
+        self.checkout = self.base / "checkout"
+        self.weights = self.base / "licensed-weights"
+        (self.checkout / "lib").mkdir(parents=True)
+        (self.weights / "model").mkdir(parents=True)
+        (self.checkout / "generate.py").write_text("print('synthetic stub, not official inference')\n")
+        (self.checkout / "lib" / "pipeline.py").write_bytes(b"synthetic code bytes")
+        (self.weights / "model" / "shard.bin").write_bytes(b"synthetic test weight bytes")
+        self.lock = self.base / "reviewed-manifest.json"
+
+    def seal(self):
+        candidate = construct_manifest(self.checkout, self.weights)
+        self.lock.write_bytes(candidate)
+        return ArtifactLock(self.lock, hashlib.sha256(candidate).hexdigest())
+
+    def test_operator_candidate_file_is_exclusive_and_unapproved(self):
+        out = self.base / "operator.lock.json"
+        reviewed_sha = create_candidate(
+            checkout=self.checkout, weights=self.weights, destination=out,
+        )
+        self.assertEqual(reviewed_sha, hashlib.sha256(out.read_bytes()).hexdigest())
+        self.assertEqual(out.stat().st_mode & 0o077, 0)
+        self.assertEqual(ArtifactLock(out, reviewed_sha).verify(
+            checkout=self.checkout, weights=self.weights), reviewed_sha)
+        with self.assertRaises(FileExistsError):
+            create_candidate(checkout=self.checkout, weights=self.weights,
+                             destination=out)
+        self.assertEqual(hashlib.sha256(out.read_bytes()).hexdigest(), reviewed_sha)
+
+    def test_reviewed_exact_manifest_checks_code_and_weights(self):
+        approved = self.seal()
+        self.assertEqual(approved.verify(checkout=self.checkout, weights=self.weights),
+                         hashlib.sha256(self.lock.read_bytes()).hexdigest())
+        manifest = json.loads(self.lock.read_bytes())
+        self.assertEqual(manifest["version"], "feature5-artifacts-v1")
+        self.assertEqual({r["scope"] for r in manifest["files"]}, {"checkout", "weights"})
+
+    def test_same_bytes_different_tenant_checkout_is_no_change(self):
+        lock = self.seal()
+        self.assertEqual(len(lock.verify(checkout=self.checkout, weights=self.weights)), 64)
+
+    def test_mutated_weight_or_runtime_code_fails(self):
+        for relative, parent in (("model/shard.bin", self.weights),
+                                 ("lib/pipeline.py", self.checkout),
+                                 ("generate.py", self.checkout)):
+            with self.subTest(relative=relative):
+                lock = self.seal()
+                target = parent / relative
+                old = target.read_bytes()
+                target.write_bytes(old + b"tampered")
+                with self.assertRaises(MotionError):
+                    lock.verify(checkout=self.checkout, weights=self.weights)
+                target.write_bytes(old)
+
+    def test_extra_or_removed_artifact_detected(self):
+        lock = self.seal()
+        extra = self.weights / "injected.pkl"
+        extra.write_bytes(b"poison")
+        with self.assertRaises(MotionError):
+            lock.verify(checkout=self.checkout, weights=self.weights)
+        extra.unlink()
+        original = self.weights / "model" / "shard.bin"
+        original.unlink()
+        with self.assertRaises(MotionError):
+            lock.verify(checkout=self.checkout, weights=self.weights)
+
+    def test_self_declared_modified_manifest_without_reviewed_digest_rejected(self):
+        approved = self.seal()
+        parsed = json.loads(self.lock.read_bytes())
+        parsed["files"][0]["sha256"] = "a" * 64
+        self.lock.write_text(json.dumps(parsed))
+        with self.assertRaisesRegex(MotionError, "differs from reviewed"):
+            approved.verify(checkout=self.checkout, weights=self.weights)
+
+    def test_forgeries_duplicates_traversal_and_invalid_hash(self):
+        for bad in ("../escape.bin", "/etc/secret", "code\\injection.py", "one//two", "./bad", "a/.."):
+            with self.subTest(bad=bad):
+                baseline = json.loads(construct_manifest(self.checkout, self.weights))
+                baseline["files"][0]["path"] = bad
+                raw = json.dumps(baseline, sort_keys=True, separators=(",", ":")).encode()
+                self.lock.write_bytes(raw)
+                with self.assertRaises(MotionError):
+                    ArtifactLock(self.lock, hashlib.sha256(raw).hexdigest()).verify(
+                        checkout=self.checkout, weights=self.weights)
+        baseline = json.loads(construct_manifest(self.checkout, self.weights))
+        baseline["files"].append(dict(baseline["files"][0]))
+        raw = json.dumps(baseline, sort_keys=True, separators=(",", ":")).encode()
+        self.lock.write_bytes(raw)
+        with self.assertRaisesRegex(MotionError, "Duplicate"):
+            ArtifactLock(self.lock, hashlib.sha256(raw).hexdigest()).verify(
+                checkout=self.checkout, weights=self.weights)
+
+    def test_symlinks_and_dirty_git_checkout_fail_closed(self):
+        lock = self.seal()
+        weight = self.weights / "model" / "linked.bin"
+        weight.symlink_to(self.weights / "model" / "shard.bin")
+        with self.assertRaises(MotionError):
+            lock.verify(checkout=self.checkout, weights=self.weights)
+        weight.unlink()
+        link_dir = self.weights / "extra"
+        link_dir.symlink_to(self.weights / "model", target_is_directory=True)
+        with self.assertRaises(MotionError):
+            lock.verify(checkout=self.checkout, weights=self.weights)
+        link_dir.unlink()
+        (self.checkout / ".git").mkdir()
+        with self.assertRaisesRegex(MotionError, "Git metadata"):
+            construct_manifest(self.checkout, self.weights)
+
+    def test_oversized_sparse_shard_rejected_before_hash(self):
+        giant = self.weights / "model" / "huge.bin"
+        with giant.open("wb") as handle:
+            handle.truncate(MAX_FILE_BYTES + 1)
+        with self.assertRaisesRegex(MotionError, "size outside"):
+            construct_manifest(self.checkout, self.weights)
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

## tests/ai/test_feature5_azure_gpu_preflight.py

~~~~diff
@@ -0,0 +1,123 @@
+"""CPU-only, read-only Azure DEV GPU inventory policy tests."""
+import sys
+import unittest
+from pathlib import Path
+from unittest.mock import patch, Mock
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT))
+from feature5_motion.azure_gpu_preflight import assess_azure_a100_preflight
+from feature5_motion.azure_gpu_readonly_cli import _read_az, inspect_current_dev
+from feature5_motion.contracts import MotionError
+
+SUB = "00000000-0000-4000-8000-000000000001"
+RG = {"name": "rg-retailgrowth-dev", "location": "centralindia",
+      "tags": {"app": "retailgrowthai", "environment": "dev"}}
+ACCOUNT = {"id": SUB, "state": "Enabled"}
+SUPPORTED = [{"name": "Consumption-GPU-NC24-A100"}]
+ENVS = [{"name": "rgai-f5-gpu-canary-eastus", "location": "eastus",
+         "provisioningState": "Succeeded",
+         "tags": {"app": "RetailGrowthAI", "environment": "dev", "feature": "feature5"},
+         "properties": {"workloadProfiles": [
+             {"name": "Consumption", "workloadProfileType": "Consumption"}
+         ]}}]
+QUOTA = {"rgai-f5-gpu-canary-eastus": [
+    {"name": {"value": "Managed Environment Consumption NCA100 GPUs"},
+     "limit": 1, "currentValue": 0}]}
+
+
+def check(**kwargs):
+    params = dict(account=ACCOUNT, resource_group=RG,
+                  supported_profiles=SUPPORTED, environments=ENVS,
+                  usage_by_environment=QUOTA, expected_subscription_id=SUB)
+    params.update(kwargs)
+    return assess_azure_a100_preflight(**params)
+
+
+class TestAzureGPUReadOnlyPreflight(unittest.TestCase):
+    def test_matching_dev_identity_a100_profile_and_one_quota_are_inventory_only(self):
+        result = check()
+        self.assertEqual(result.status, "INSPECTION_PASS_ONLY")
+        self.assertEqual(result.eligible_environment, "rgai-f5-gpu-canary-eastus")
+        self.assertIn("No GPU has been created", " ".join(result.reasons))
+
+    def test_wrong_subscription_or_prod_group_never_proceed(self):
+        for params in ({"account": {"id": SUB[:-1]+"2", "state": "Enabled"}},
+                       {"account": {"id": SUB, "state": "Disabled"}},
+                       {"resource_group": {"name": "rg-retailgrowth-prod",
+                                           "location": "centralindia", "tags": RG["tags"]}},
+                       {"resource_group": {"name": RG["name"], "location": "centralindia",
+                                           "tags": {"app": "retailgrowthai", "environment": "prod"}}}):
+            with self.subTest(params=params), self.assertRaises(MotionError):
+                check(**params)
+
+    def test_t4_only_central_india_does_not_count_as_a100(self):
+        self.assertEqual(check(supported_profiles=[{"name": "Consumption-GPU-T4"}]).status, "BLOCKED")
+        e = [{"name": "rgai-centralindia", "location": "centralindia",
+              "provisioningState": "Succeeded", "properties": {"workloadProfiles": [
+                  {"workloadProfileType": "Consumption-GPU-T4"}]}}]
+        # A T4-only environment in India does not supply the required
+        # East US A100 environment; region-supported quota inspection still
+        # needs a new, empty East US workload-profiles environment.
+        self.assertEqual(check(environments=e).status, "ENVIRONMENT_REQUIRED")
+
+    def test_no_env_or_duplicates_or_exhausted_quota_block(self):
+        self.assertEqual(check(environments=[]).status, "ENVIRONMENT_REQUIRED")
+        self.assertEqual(check(environments=ENVS + ENVS).status, "BLOCKED")
+        self.assertEqual(check(usage_by_environment={}).status, "BLOCKED")
+        exhausted = {"rgai-f5-gpu-canary-eastus": [
+            {"name": {"value": "Managed Environment Consumption NCA100 GPUs"},
+             "limit": 1, "currentValue": 1}]}
+        self.assertEqual(check(usage_by_environment=exhausted).status, "BLOCKED")
+
+    def test_wrong_env_tags_or_paid_gpu_profile_cannot_pass(self):
+        foreign = __import__("copy").deepcopy(ENVS)
+        foreign[0]["tags"]["environment"] = "prod"
+        self.assertEqual(check(environments=foreign).status, "BLOCKED")
+        paid = __import__("copy").deepcopy(ENVS)
+        paid[0]["properties"]["workloadProfiles"].append(
+            {"name": "A100", "workloadProfileType": "Consumption-GPU-NC24-A100"})
+        self.assertEqual(check(environments=paid).status, "BLOCKED")
+
+    def test_nonpositive_or_invalid_quota_blocks(self):
+        for value in ("nan", "junk", -1, 1):
+            usage = {"rgai-f5-gpu-canary-eastus": [
+                {"name": {"value": "Managed Environment Consumption NCA100 GPUs"},
+                 "limit": 1, "currentValue": value}]}
+            self.assertEqual(check(usage_by_environment=usage).status, "BLOCKED")
+
+    def test_readonly_cli_disallows_create_or_delete_invocations(self):
+        with patch("feature5_motion.azure_gpu_readonly_cli.subprocess.run") as run:
+            for operation in (("containerapp", "job", "create"),
+                              ("group", "delete"),
+                              ("containerapp", "env", "update"),
+                              ("account", "set")):
+                with self.subTest(operation=operation), self.assertRaises(MotionError):
+                    _read_az(*operation)
+            run.assert_not_called()
+
+    def test_cli_inventory_uses_only_five_allowed_az_calls(self):
+        docs = [ACCOUNT, RG, SUPPORTED, ENVS, QUOTA["rgai-f5-gpu-canary-eastus"]]
+        calls = []
+        def fake_run(cmd, **kwargs):
+            calls.append(cmd)
+            return Mock(stdout=__import__("json").dumps(docs[len(calls)-1]))
+        with patch("feature5_motion.azure_gpu_readonly_cli.subprocess.run", side_effect=fake_run):
+            result = inspect_current_dev(expected_subscription_id=SUB)
+        self.assertEqual(result.status, "INSPECTION_PASS_ONLY")
+        self.assertEqual(len(calls), 5)
+        self.assertTrue(all(c[0] == "az" and
+                            not any(t in ("create", "start", "update", "delete", "apply", "deploy")
+                                    for t in c) for c in calls))
+
+    def test_cli_account_mismatch_stops_before_resource_queries(self):
+        bad = {"id": "00000000-0000-4000-8000-000000000002", "state": "Enabled"}
+        with patch("feature5_motion.azure_gpu_readonly_cli.subprocess.run",
+                   return_value=Mock(stdout=__import__("json").dumps(bad))) as runner:
+            with self.assertRaises(MotionError):
+                inspect_current_dev(expected_subscription_id=SUB)
+            runner.assert_called_once()
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

## tests/ai/test_feature5_azure_pricing.py

~~~~diff
@@ -0,0 +1,87 @@
+"""Azure official price snapshot parser unit tests; no API calls in CI."""
+import sys
+import unittest
+from pathlib import Path
+from decimal import Decimal
+sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
+from feature5_motion.contracts import MotionError
+from feature5_motion.azure_pricing import extract_rates, estimate_execution_usd, MotionSpendGuard
+
+
+def row(region, meter, price, unit):
+    return {"serviceName": "Azure Container Apps", "armRegionName": region,
+            "meterName": meter, "retailPrice": price, "unitOfMeasure": unit,
+            "currencyCode": "USD", "type": "Consumption",
+            "effectiveStartDate": "2026-04-01T00:00:00Z",
+            "isPrimaryMeterRegion": True}
+
+
+class TestAzureRetailPriceVerification(unittest.TestCase):
+    def setUp(self):
+        self.items = [
+            row("eastus", "Standard NC A100 v4 GPU Usage", 0.000529, "1 Second"),
+            row("eastus", "Standard vCPU Active Usage", 0.000024, "1 Second"),
+            row("eastus", "Standard Memory Active Usage", 0.000003, "1 GiB Second"),
+        ]
+
+    def test_official_eastus_a100_meter(self):
+        rates = extract_rates({"BillingCurrency": "USD", "Items": self.items},
+                              region="eastus", gpu="A100")
+        self.assertEqual(rates.gpu_per_second_usd, Decimal("0.000529"))
+        self.assertEqual(estimate_execution_usd(rates, billable_seconds=600,
+                         vcpus=4, gib_memory=16), Decimal("0.403800"))
+
+    def test_unavailable_gpu_must_not_be_inferred_from_other_region(self):
+        with self.assertRaises(MotionError):
+            extract_rates({"BillingCurrency": "USD", "Items": self.items},
+                          region="centralindia", gpu="A100")
+
+    def test_zero_nan_duplicate_and_nonprimary_prices_fail(self):
+        for price in (0, "-1", float("nan"), float("inf"), True):
+            damaged = [dict(item) for item in self.items]
+            damaged[0]["retailPrice"] = price
+            with self.subTest(price=price), self.assertRaises(MotionError):
+                extract_rates({"BillingCurrency": "USD", "Items": damaged},
+                              region="eastus", gpu="A100")
+        with self.assertRaises(MotionError):
+            extract_rates({"BillingCurrency": "USD", "Items": self.items + [self.items[0]]},
+                          region="eastus", gpu="A100")
+        bad = [dict(item) for item in self.items]
+        bad[0]["isPrimaryMeterRegion"] = False
+        with self.assertRaises(MotionError):
+            extract_rates({"BillingCurrency": "USD", "Items": bad},
+                          region="eastus", gpu="A100")
+
+    def test_maximum_inference_cost_includes_time_and_reserve_buffer(self):
+        rates = extract_rates({"BillingCurrency": "USD", "Items": self.items},
+                              region="eastus", gpu="A100")
+        guard = MotionSpendGuard(
+            rates, max_billable_seconds=600, vcpus=4, gib_memory=16,
+            ancillary_allowance_usd=Decimal("0.0500"),
+        )
+        self.assertEqual(guard.minimum_reservation_usd(), Decimal("0.4538"))
+
+    def test_invalid_maximum_runtime_and_allowance_fail_closed(self):
+        rates = extract_rates({"BillingCurrency": "USD", "Items": self.items},
+                              region="eastus", gpu="A100")
+        for seconds in (0, 1801, True):
+            with self.subTest(seconds=seconds), self.assertRaises(MotionError):
+                MotionSpendGuard(rates, seconds, 4, 16, Decimal("0.01")).minimum_reservation_usd()
+        for extra in (float("nan"), -1, float("inf")):
+            with self.subTest(extra=extra), self.assertRaises(MotionError):
+                MotionSpendGuard(rates, 600, 4, 16, extra).minimum_reservation_usd()
+
+    def test_bad_capacity_and_currency_rejected(self):
+        for sec in (0, 3601, True):
+            rates = extract_rates({"BillingCurrency": "USD", "Items": self.items},
+                                  region="eastus", gpu="A100")
+            with self.assertRaises(MotionError):
+                estimate_execution_usd(rates, billable_seconds=sec,
+                                       vcpus=4, gib_memory=16)
+        with self.assertRaises(MotionError):
+            extract_rates({"BillingCurrency": "INR", "Items": self.items},
+                          region="eastus", gpu="A100")
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

## tests/ai/test_feature5_cost_routing.py

~~~~diff
@@ -0,0 +1,90 @@
+"""Feature5 cheapest honest media path: CPU first, GPU never implicitly."""
+from decimal import Decimal
+import sys
+import unittest
+from pathlib import Path
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT))
+from feature5_motion.azure_pricing import MotionSpendGuard, VerifiedAzureRates
+from feature5_motion.cost_routing import plan_lowest_cost_delivery
+from feature5_motion.contracts import MotionError
+
+
+def quote():
+    rates = VerifiedAzureRates(
+        "eastus", "A100", Decimal("0.000529"), Decimal("0.000024"),
+        Decimal("0.000003"), "2026-10-26T00:00:00Z",
+    )
+    return MotionSpendGuard(
+        rates, max_billable_seconds=600, vcpus=4, gib_memory=16,
+        ancillary_allowance_usd=Decimal("0.05"),
+    )
+
+
+class TestCostAwareDelivery(unittest.TestCase):
+    def test_existing_free_media_preferred_even_when_gpu_budget_exists(self):
+        selected = plan_lowest_cost_delivery(
+            requires_realistic_ai_motion=False, existing_media_approved=True,
+            allow_paid_gpu=True, max_premium_usd="100", guard=quote())
+        self.assertEqual(selected.route, "EXISTING_FFMPEG")
+        self.assertIsNone(selected.reserved_quote_usd)
+
+    def test_realistic_walking_model_not_faked_with_ffmpeg_stills(self):
+        selected = plan_lowest_cost_delivery(
+            requires_realistic_ai_motion=True, existing_media_approved=True)
+        self.assertEqual(selected.route, "DEFER")
+        self.assertEqual(selected.max_premium_usd, Decimal(0))
+
+    def test_zero_default_and_unapproved_spend_never_route_to_gpu(self):
+        for kwargs in (
+            {},
+            {"max_premium_usd": "999", "allow_paid_gpu": False},
+            {"max_premium_usd": "999", "allow_paid_gpu": True},
+        ):
+            with self.subTest(kwargs=kwargs):
+                selected = plan_lowest_cost_delivery(
+                    requires_realistic_ai_motion=True,
+                    existing_media_approved=True, **kwargs)
+                self.assertEqual(selected.route, "DEFER")
+
+    def test_quote_above_cap_deferred_without_gpu_call(self):
+        expected = quote().minimum_reservation_usd()
+        self.assertGreater(expected, Decimal("0.4"))
+        selected = plan_lowest_cost_delivery(
+            requires_realistic_ai_motion=True, existing_media_approved=True,
+            allow_paid_gpu=True, max_premium_usd="0.20", guard=quote())
+        self.assertEqual(selected.route, "DEFER")
+        self.assertEqual(selected.reserved_quote_usd, expected)
+
+    def test_explicit_gpu_permission_and_budget_only_unlock_preflight(self):
+        expected = quote().minimum_reservation_usd()
+        selected = plan_lowest_cost_delivery(
+            requires_realistic_ai_motion=True, existing_media_approved=False,
+            allow_paid_gpu=True, max_premium_usd=str(expected), guard=quote())
+        self.assertEqual(selected.route, "GPU_BUDGET_ELIGIBLE")
+        self.assertEqual(selected.reserved_quote_usd, expected)
+        self.assertIn("licence", selected.reason)
+        # GPU_BUDGET_ELIGIBLE is not a paid launch: the DB/rights/license gate still blocks by default.
+
+    def test_fails_closed_on_negative_nan_bool_and_invalid_intent(self):
+        for bad in (-1, "NaN", "Infinity", True, None, "unknown"):
+            with self.subTest(bad=bad):
+                with self.assertRaises(MotionError):
+                    plan_lowest_cost_delivery(
+                        requires_realistic_ai_motion=True,
+                        existing_media_approved=True, max_premium_usd=bad)
+        with self.assertRaises(MotionError):
+            plan_lowest_cost_delivery(requires_realistic_ai_motion=1, existing_media_approved=True)
+        with self.assertRaises(MotionError):
+            plan_lowest_cost_delivery(
+                requires_realistic_ai_motion=True, existing_media_approved=True, allow_paid_gpu="yes")
+
+    def test_unlicensed_stills_cannot_use_free_existing_ffmpeg(self):
+        result = plan_lowest_cost_delivery(
+            requires_realistic_ai_motion=False, existing_media_approved=False)
+        self.assertEqual(result.route, "DEFER")
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

## tests/ai/test_feature5_demo_fashion.py

~~~~diff
@@ -0,0 +1,46 @@
+"""Feature #5 deterministic genuine-Hunyuan sample specification; CPU-only tests."""
+import sys
+from pathlib import Path
+import unittest
+from uuid import uuid4
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT))
+from feature5_motion.demo_fashion import (
+    FASHION_PROMPT, FASHION_BRIEF_ID, fashion_motion_spec,
+)
+from feature5_motion.contracts import MotionError
+
+
+class TestHunyuanSampleBrief(unittest.TestCase):
+    def test_one_five_second_portrait_text_to_video_sample(self):
+        shop, job = str(uuid4()), str(uuid4())
+        spec = fashion_motion_spec(shop_id=shop, job_id=job)
+        self.assertEqual(spec.job_id, job)
+        self.assertEqual(spec.shop_id, shop)
+        self.assertEqual(spec.mode, "text")
+        self.assertIsNone(spec.source_asset_id)
+        self.assertEqual(spec.resolution, "480p")
+        self.assertEqual(spec.aspect_ratio, "9:16")
+        self.assertEqual(spec.fps, 24)
+        self.assertEqual(spec.duration_seconds, 5)
+        self.assertEqual(spec.seed, 20261026)
+        self.assertEqual(spec.prompt, FASHION_PROMPT)
+        self.assertIn("red", FASHION_PROMPT)
+        self.assertIn("boutique", FASHION_PROMPT)
+        self.assertTrue(FASHION_BRIEF_ID.startswith("fashion-"))
+
+    def test_no_invalid_or_client_supplied_tenant_identifiers(self):
+        for data in ({"shop_id": "forged", "job_id": str(uuid4())},
+                     {"shop_id": str(uuid4()), "job_id": "../../bad"}):
+            with self.assertRaises(MotionError):
+                fashion_motion_spec(**data)
+
+    def test_prompt_is_bounded_and_avoids_generated_sale_claim(self):
+        self.assertTrue(1 <= len(FASHION_PROMPT) <= 1500)
+        self.assertNotIn("20% OFF", FASHION_PROMPT)
+        self.assertIn("no watermarks", FASHION_PROMPT)
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

## tests/ai/test_feature5_empty_azure_env.py

~~~~diff
@@ -0,0 +1,74 @@
+"""Offline checks for one-resource, zero-active-compute Azure DEV plan."""
+import json
+import sys
+import tempfile
+import unittest
+from pathlib import Path
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT))
+from feature5_motion.empty_env_template import (
+    TARGET_ENV, TARGET_RG, TEMPLATE, validate_template, validate_what_if,
+)
+from feature5_motion.contracts import MotionError
+
+SUB = "00000000-0000-4000-8000-000000000003"
+RID = f"/subscriptions/{SUB}/resourceGroups/{TARGET_RG}/providers/Microsoft.App/managedEnvironments/{TARGET_ENV}"
+
+
+class TestFeature5ZeroComputeARM(unittest.TestCase):
+    def test_source_contains_only_unused_v2_consumption_environment(self):
+        plan = validate_template()
+        self.assertEqual(len(plan["resources"]), 1)
+        resource = plan["resources"][0]
+        self.assertEqual(resource["type"], "Microsoft.App/managedEnvironments")
+        self.assertEqual(resource["location"], "eastus")
+        self.assertEqual(resource["tags"]["environment"], "dev")
+        self.assertEqual(resource["properties"]["appLogsConfiguration"], {"destination": "none"})
+        self.assertEqual(resource["properties"]["workloadProfiles"], [
+            {"name": "Consumption", "workloadProfileType": "Consumption"}])
+        self.assertEqual(resource["name"], TARGET_ENV)
+        self.assertNotIn("Microsoft.ContainerRegistry", json.dumps(plan))
+        self.assertNotIn("LogAnalytics", json.dumps(plan))
+
+    def test_billing_addons_or_prod_edits_are_rejected(self):
+        original = validate_template()
+        cases = []
+        a = json.loads(json.dumps(original))
+        a["resources"].append({"type": "Microsoft.Compute/virtualMachines"})
+        cases.append(a)
+        for key, value in [
+            ("location", "centralindia"),
+            ("properties", {"workloadProfiles": [
+                {"name": "gpu", "workloadProfileType": "Consumption-GPU-NC24-A100"}]}),
+            ("properties", {"appLogsConfiguration": {"destination": "log-analytics"}}),
+            ("tags", {"environment": "prod"}),
+        ]:
+            a = json.loads(json.dumps(original))
+            a["resources"][0][key] = value
+            cases.append(a)
+        with tempfile.TemporaryDirectory() as d:
+            source = Path(d) / "changed.json"
+            for case in cases:
+                with self.subTest(case=case["resources"]):
+                    source.write_text(json.dumps(case), encoding="utf-8")
+                    with self.assertRaises(MotionError):
+                        validate_template(source)
+
+    def test_what_if_accepts_exact_new_resource_only(self):
+        validate_what_if({"changes": [{"resourceId": RID, "changeType": "Create"}]}, SUB)
+        for bad in (
+            {"changes": []},
+            {"changes": [{"resourceId": RID, "changeType": "Modify"}]},
+            {"changes": [{"resourceId": RID, "changeType": "Delete"}]},
+            {"changes": [{"resourceId": RID, "changeType": "Ignore"}]},
+            {"changes": [{"resourceId": RID + "-other", "changeType": "Create"}]},
+            {"changes": [{"resourceId": RID, "changeType": "Create"},
+                         {"resourceId": RID + "2", "changeType": "Create"}]},
+        ):
+            with self.subTest(change=bad), self.assertRaises(MotionError):
+                validate_what_if(bad, SUB)
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

## tests/ai/test_feature5_external_gpu_budget.py

~~~~diff
@@ -0,0 +1,158 @@
+"""Fail-closed CPU-only tests; NO GPU, Azure, third-party payment or network."""
+from datetime import datetime, timezone, timedelta
+from hashlib import sha256
+from pathlib import Path
+import copy
+import json
+import tempfile
+import unittest
+
+from feature5_motion.external_gpu_budget import (
+    ExternalQuoteError, assess_external_gpu_quote, read_approved_external_quote,
+)
+
+
+NOW = datetime(2026, 10, 26, 13, 0, tzinfo=timezone.utc)
+
+
+def quote():
+    return {
+        "provider": "runpod", "sku": "RTX_4090_24GB", "gpu_count": 1,
+        "system_ram_gib": 48, "region": "us-east-1", "country": "US",
+        "billing_mode": "on_demand", "currency": "USD",
+        "compute_usd_per_hour": "0.89", "storage_usd_per_hour": "0.02",
+        "minimum_billable_seconds": 60,
+        "quoted_at": "2026-10-26T12:00:00Z",
+        "expires_at": "2026-10-26T23:00:00Z",
+    }
+
+
+def assess(q=None, **kwargs):
+    args = dict(max_seconds=600, provider_termination_after_seconds=3600,
+                ancillary_allowance_usd="0.05",
+                approved_ceiling_usd="1.10", now=NOW)
+    args.update(kwargs)
+    return assess_external_gpu_quote(quote() if q is None else q, **args)
+
+
+class TestExternalGpuBudget(unittest.TestCase):
+    def test_valid_quote_is_not_authorization(self):
+        result = assess()
+        self.assertEqual(str(result.cost_ceiling_usd), "0.9600")
+        self.assertEqual(result.status, "QUOTE_ONLY_NOT_EXECUTION_AUTHORIZATION")
+        self.assertEqual(result.max_seconds, 600)
+        self.assertEqual(result.provider_termination_after_seconds, 3600)
+
+    def test_low_cost_a40_quote_one_hour_provider_termination(self):
+        q = quote()
+        q["sku"] = "A40_48GB"
+        q["system_ram_gib"] = 50
+        q["compute_usd_per_hour"] = "0.59"
+        result = assess(q, approved_ceiling_usd="0.75")
+        self.assertEqual(str(result.cost_ceiling_usd), "0.6600")
+        self.assertEqual(result.status, "QUOTE_ONLY_NOT_EXECUTION_AUTHORIZATION")
+        with self.assertRaises(ExternalQuoteError):
+            assess(q, approved_ceiling_usd="0.65")
+
+    def test_minimum_billing_is_included(self):
+        q = quote()
+        q["minimum_billable_seconds"] = 900
+        self.assertEqual(str(assess(q, provider_termination_after_seconds=720,
+                                    approved_ceiling_usd="0.30").cost_ceiling_usd), "0.2775")
+
+    def test_expired_and_future_quotes_denied(self):
+        q = quote()
+        q["expires_at"] = "2026-10-26T12:30:00Z"
+        with self.assertRaises(ExternalQuoteError):
+            assess(q)
+        q = quote()
+        q["quoted_at"] = "2026-10-27T02:00:00Z"
+        with self.assertRaises(ExternalQuoteError):
+            assess(q)
+
+    def test_no_spot_or_unapproved_provider(self):
+        for key, value in (("billing_mode", "spot"), ("provider", "unknown"),
+                           ("provider", []), ("sku", ["RTX_4090_24GB"])):
+            with self.subTest(key=key, value=value):
+                q = quote()
+                q[key] = value
+                with self.assertRaises(ExternalQuoteError):
+                    assess(q)
+
+    def test_hardware_unknown_and_under_ram_denied(self):
+        for key, value in (("sku", "T4_16GB"), ("gpu_count", 2),
+                           ("system_ram_gib", 25), ("system_ram_gib", True)):
+            with self.subTest(key=key, value=value):
+                q = quote()
+                q[key] = value
+                with self.assertRaises(ExternalQuoteError):
+                    assess(q)
+
+    def test_cost_uncertainty_fails_closed(self):
+        for rate in ("NaN", "-1", "Infinity", "1001", None):
+            q = quote()
+            q["compute_usd_per_hour"] = rate
+            with self.subTest(rate=rate):
+                with self.assertRaises(ExternalQuoteError):
+                    assess(q)
+        with self.assertRaises(ExternalQuoteError):
+            assess(approved_ceiling_usd="0.15")
+        with self.assertRaises(ExternalQuoteError):
+            assess(max_seconds=1801)
+        with self.assertRaises(ExternalQuoteError):
+            assess(provider_termination_after_seconds=600)
+        with self.assertRaises(ExternalQuoteError):
+            assess(provider_termination_after_seconds=3601)
+
+    def test_price_region_currency_and_schema(self):
+        for key, value in (("region", ""), ("country", "USA"),
+                           ("currency", "EUR"), ("minimum_billable_seconds", -1),
+                           ("quoted_at", "not-a-date"), ("quoted_at", "2026-10-26T12:00:00+04:00")):
+            q = quote()
+            q[key] = value
+            with self.subTest(key=key):
+                with self.assertRaises(ExternalQuoteError):
+                    assess(q)
+        q = quote()
+        q["unexpected"] = 1
+        with self.assertRaises(ExternalQuoteError):
+            assess(q)
+
+    def test_quote_sha256_required_and_exact(self):
+        with tempfile.TemporaryDirectory() as folder:
+            f = Path(folder) / "account-quote.json"
+            data = json.dumps(quote(), sort_keys=True).encode("utf-8")
+            f.write_bytes(data)
+            digest = sha256(data).hexdigest()
+            self.assertEqual(read_approved_external_quote(f, approved_sha256=digest), quote())
+            with self.assertRaises(ExternalQuoteError):
+                read_approved_external_quote(f, approved_sha256="0" * 64)
+            with self.assertRaises(ExternalQuoteError):
+                read_approved_external_quote(f, approved_sha256="not-a-hash")
+            f.write_bytes(data + b" ")
+            with self.assertRaises(ExternalQuoteError):
+                read_approved_external_quote(f, approved_sha256=digest)
+
+    def test_duplicate_keys_rejected_even_with_correct_hash(self):
+        with tempfile.TemporaryDirectory() as folder:
+            f = Path(folder) / "bad.json"
+            f.write_text('{"provider":"runpod","provider":"vast"}')
+            with self.assertRaises(ExternalQuoteError):
+                read_approved_external_quote(
+                    f, approved_sha256=sha256(f.read_bytes()).hexdigest())
+
+    def test_symlink_quote_rejected(self):
+        with tempfile.TemporaryDirectory() as folder:
+            original = Path(folder) / "quote.json"
+            original.write_text(json.dumps(quote()))
+            link = Path(folder) / "link.json"
+            try:
+                link.symlink_to(original)
+            except (OSError, NotImplementedError):
+                self.skipTest("Local OS disallows symlinks")
+            with self.assertRaises(ExternalQuoteError):
+                read_approved_external_quote(link, approved_sha256=sha256(original.read_bytes()).hexdigest())
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

## tests/ai/test_feature5_interop.py

~~~~diff
@@ -0,0 +1,209 @@
+"""Feature5 interop tests: no hosted ledger, tenant data, Azure, or GPU."""
+import sys
+import unittest
+from pathlib import Path
+from unittest.mock import Mock
+from uuid import uuid4
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
+from feature5_motion.contracts import MotionError
+from feature5_motion.quality_review import VisualReview, review_template
+from feature5_motion.interop import (
+    ApprovedMotionClip, FEATURE4_VERSION, HUNYUAN_MODEL,
+    Part3MotionStoreAdapter, feature4_asset_entry, feature4_scene,
+    planned_motion_key, verified_claim_to_motion,
+)
+
+
+def uid():
+    return str(uuid4())
+
+
+class TestPart3Bridge(unittest.TestCase):
+    def setUp(self):
+        self.shop = uid()
+        self.job = uid()
+        self.source = uid()
+        self.token = uid()
+        self.reservation = uid()
+        self.row = {
+            "id": self.job, "shop_id": self.shop, "attempt_token": self.token,
+            "model_id": HUNYUAN_MODEL, "mode": "image",
+            "prompt": "Adult model walks through boutique", "source_asset_id": self.source,
+            "resolution": "480p", "seconds": 5, "status": "RUNNING",
+            "review_status": "APPROVED", "rights_approved": True,
+            "user_approved": True, "subscription_active": True,
+            "reserved_usd": "0.80", "reservation_id": self.reservation,
+            "idempotency_key": "a" * 64, "prompt_version": "feature5-v1",
+        }
+
+    def test_existing_ledger_authoritative_claim(self):
+        ledger = Mock()
+        ledger.claim_authorized_motion.return_value = self.row.copy()
+        adapter = Part3MotionStoreAdapter(ledger)
+        claim = adapter.claim(self.job)
+        self.assertEqual(claim["spec"].mode, "image")
+        self.assertEqual(str(claim["reserved_usd"]), "0.80")
+        self.assertEqual(claim["reservation_id"], self.reservation)
+        ledger.claim_authorized_motion.assert_called_once_with(self.job)
+        self.assertTrue(adapter.mark_unknown(self.job, self.token, "PRIVATE_UPLOAD_UNCERTAIN"))
+        ledger.unknown_motion.assert_called_once_with(self.job, self.token, "PRIVATE_UPLOAD_UNCERTAIN")
+        adapter.complete(self.job, self.token, {"private": True})
+        ledger.complete_motion.assert_called_once()
+
+    def test_quota_and_other_tenant_denied(self):
+        bads = [
+            {"status": "QUEUED"}, {"model_id": "wan2.7-i2v-2026-04-25"},
+            {"subscription_active": False}, {"user_approved": False},
+            {"rights_approved": False}, {"review_status": "DRAFT"},
+            {"reserved_usd": float("NaN")}, {"reserved_usd": "0"},
+            {"reserved_usd": True}, {"reserved_usd": "-1"},
+            {"resolution": "720P"}, {"seconds": 10},
+            {"attempt_token": "forged/lease"}, {"reservation_id": None},
+            {"idempotency_key": "bad"}, {"source_asset_id": "https://evil.invalid"},
+        ]
+        for changes in bads:
+            with self.subTest(changes=changes):
+                row = dict(self.row, **changes)
+                with self.assertRaises(MotionError):
+                    verified_claim_to_motion(row)
+
+    def test_foreign_job_from_ledger_denied(self):
+        ledger = Mock()
+        ledger.claim_authorized_motion.return_value = dict(self.row, id=uid())
+        with self.assertRaises(MotionError):
+            Part3MotionStoreAdapter(ledger).claim(self.job)
+
+    def test_duplicate_key_for_same_request_and_separate_tenants(self):
+        one = planned_motion_key(self.shop, uid(), self.source, "feature5-v1", "image", HUNYUAN_MODEL, approved_prompt_sha256="b" * 64)
+        # same inputs deterministic
+        day = uid()
+        a = planned_motion_key(self.shop, day, self.source, "feature5-v1", "image", HUNYUAN_MODEL, approved_prompt_sha256="b" * 64)
+        b = planned_motion_key(self.shop, day, self.source, "feature5-v1", "image", HUNYUAN_MODEL, approved_prompt_sha256="b" * 64)
+        c = planned_motion_key(uid(), day, self.source, "feature5-v1", "image", HUNYUAN_MODEL, approved_prompt_sha256="b" * 64)
+        self.assertNotEqual(one, a)
+        self.assertEqual(a, b)
+        self.assertNotEqual(a, c)
+        revised = planned_motion_key(self.shop, day, self.source, "feature5-v1",
+                                     "image", HUNYUAN_MODEL, approved_prompt_sha256="c" * 64)
+        reseeded = planned_motion_key(self.shop, day, self.source, "feature5-v1",
+                                      "image", HUNYUAN_MODEL, approved_prompt_sha256="b" * 64, seed=2)
+        self.assertNotEqual(a, revised)
+        self.assertNotEqual(a, reseeded)
+        with self.assertRaises(MotionError):
+            planned_motion_key(self.shop, day, self.source, "feature5-v1",
+                               "image", HUNYUAN_MODEL, approved_prompt_sha256="invalid")
+        with self.assertRaises(MotionError):
+            planned_motion_key(self.shop, day, self.source, "feature5-v1", "image", "unknown-model", approved_prompt_sha256="b" * 64)
+
+    def test_text_claim_rejects_image_attachment(self):
+        row = dict(self.row, mode="text", source_asset_id=None)
+        spec, _ = verified_claim_to_motion(row)
+        self.assertIsNone(spec.source_asset_id)
+        with self.assertRaises(MotionError):
+            verified_claim_to_motion(dict(row, source_asset_id=self.source))
+
+
+class TestFeature4Handoff(unittest.TestCase):
+    def setUp(self):
+        self.shop = uid()
+        self.job = uid()
+        self.token = uid()
+        self.clip = uid()
+        self.path = f"{self.shop}/renders/{self.job}/{self.token}.mp4"
+        self.rights = {"commercial_use": True, "license": "owned", "evidence": "Approved retailer-owned licensed footage", "source": "RetailGrowthAI generated motion"}
+        self.row = {
+            "job_id": self.job, "shop_id": self.shop, "clip_asset_id": self.clip,
+            "attempt_token": self.token, "storage_path": self.path,
+            "status": "SUCCEEDED", "provenance": HUNYUAN_MODEL,
+            "quality_status": "APPROVED", "output_codec": "h264",
+            "rights_approved": True, "duration_seconds": 5.0,
+        }
+        # Synthetic fixture only; a real approval must be loaded from audited DB.
+        self.clip_sha = "f" * 64
+        self.review = VisualReview(
+            shop_id=self.shop, job_id=self.job, source_asset_id=None,
+            output_asset_id=self.clip, reviewer_user_id=uid(),
+            reviewed_sha256=self.clip_sha,
+            checks={key: True for key in review_template()},
+            decision="APPROVED",
+            notes="Synthetic contract fixture, not a real assessment.",
+            ai_disclosure_approved=True,
+        )
+        self.review_kwargs = {
+            "review": self.review, "actual_media_sha256": self.clip_sha,
+            "reviewer_has_write_role": True,
+        }
+
+    def ready(self, **overrides):
+        return ApprovedMotionClip(**dict(self.row, **overrides))
+
+    def test_feature4_trusted_video_manifest(self):
+        asset_id, entry = feature4_asset_entry(
+            self.ready(), shop_id=self.shop, local_staged_path="clips/fashion.mp4",
+            rights=self.rights, **self.review_kwargs)
+        self.assertEqual(asset_id, self.clip)
+        self.assertEqual(FEATURE4_VERSION, "creative_reel_v1")
+        self.assertEqual(entry["source_feature"], "feature5")
+        self.assertEqual(entry["kind"], "video")
+        self.assertEqual(entry["path"], "clips/fashion.mp4")
+        scene = feature4_scene(asset_id, order=1, start_time=3,
+                               headline="Luxury Boutique")
+        self.assertEqual(scene["motion_status"], "ready")
+        self.assertEqual(scene["source_feature"], "feature5")
+        self.assertNotIn("text_overlay", scene)
+
+    def test_foreign_or_unreviewed_motion_denied(self):
+        for value in [
+            {"shop_id": uid()}, {"storage_path": self.path + ".bak"},
+            {"attempt_token": uid()}, {"status": "FAILED"},
+            {"quality_status": "PENDING"}, {"provenance": "synthetic-fixture"},
+            {"rights_approved": False}, {"output_codec": "av1"},
+            {"duration_seconds": 30},
+        ]:
+            with self.subTest(value=value), self.assertRaises(MotionError):
+                feature4_asset_entry(self.ready(**value), shop_id=self.shop,
+                                     local_staged_path="clips/fashion.mp4",
+                                     rights=self.rights, **self.review_kwargs)
+
+    def test_forged_or_missing_visual_review_never_publishes(self):
+        with self.assertRaises(MotionError):
+            feature4_asset_entry(self.ready(), shop_id=self.shop,
+                                 local_staged_path="clips/fashion.mp4", rights=self.rights)
+        for changes in [
+            {"actual_media_sha256": "a" * 64},
+            {"reviewer_has_write_role": False},
+            {"review": VisualReview(
+                shop_id=self.shop, job_id=uid(), source_asset_id=None,
+                output_asset_id=self.clip, reviewer_user_id=uid(),
+                reviewed_sha256=self.clip_sha,
+                checks={key: True for key in review_template()},
+                decision="APPROVED", notes="Mock mismatch only, not real review.",
+                ai_disclosure_approved=True)},
+            {"review": VisualReview(
+                shop_id=self.shop, job_id=self.job, source_asset_id=None,
+                output_asset_id=self.clip, reviewer_user_id=uid(),
+                reviewed_sha256=self.clip_sha,
+                checks=review_template(), decision="REJECTED",
+                notes="Garment fails quality inspection; reject.",
+                ai_disclosure_approved=True)},
+        ]:
+            with self.subTest(changes=tuple(changes)), self.assertRaises(MotionError):
+                feature4_asset_entry(
+                    self.ready(), shop_id=self.shop, local_staged_path="clips/fashion.mp4",
+                    rights=self.rights, **dict(self.review_kwargs, **changes))
+
+    def test_foreign_path_or_unlicensed_clips_denied(self):
+        for staged in ("/tmp/secret.mp4", "../escape.mp4", "http://host/video.mp4",
+                       "clips/../escape.mp4", "clips\\evil.mp4"):
+            with self.subTest(path=staged), self.assertRaises(MotionError):
+                feature4_asset_entry(self.ready(), shop_id=self.shop, local_staged_path=staged,
+                                     rights=self.rights, **self.review_kwargs)
+        with self.assertRaises(MotionError):
+            feature4_asset_entry(self.ready(), shop_id=self.shop,
+                                 local_staged_path="clips/fashion.mp4",
+                                 rights={"commercial_use": True, "license": "unreviewed", "source": "retailer", "evidence": "none"}, **self.review_kwargs)
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

## tests/ai/test_feature5_license_gate.py

~~~~diff
@@ -0,0 +1,72 @@
+"""Tencent Community License *policy* negative tests; NOT legal clearance."""
+import sys
+import unittest
+from pathlib import Path
+sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
+from feature5_motion.contracts import MotionError
+from feature5_motion.license_gate import EXCLUDED_COUNTRIES, HunyuanLicensePolicy
+
+
+def reviewed(**kwargs):
+    values = dict(
+        deployment_country="US", retailer_country="IN",
+        intended_publication_countries=("IN", "US"),
+        actual_provider_legal_name="RetailGrowthAI DEV Licensing Test",
+        tencent_no_endorsement_notice=True,
+        full_license_terms_available_to_users=True,
+        acceptable_use_and_local_law_checked=True,
+        commercial_media_rights_checked=True,
+        operator_terms_reviewed=True,
+        monthly_active_users_at_model_release=1000,
+        separate_tencent_license_if_required=False,
+    )
+    values.update(kwargs)
+    return HunyuanLicensePolicy(**values)
+
+
+class TestHunyuanLicenseGate(unittest.TestCase):
+    def test_mock_reviewed_india_and_us(self):
+        self.assertIsNone(reviewed().assert_allowed())
+
+    def test_all_eu_uk_korea_are_blocked_in_processing_retailer_and_publication(self):
+        for country in EXCLUDED_COUNTRIES:
+            for changed in (
+                {"deployment_country": country},
+                {"retailer_country": country},
+                {"intended_publication_countries": ("IN", country)},
+            ):
+                with self.subTest(country=country, field=list(changed)[0]):
+                    with self.assertRaises(MotionError):
+                        reviewed(**changed).assert_allowed()
+
+    def test_missing_compliance_disclosure_denied(self):
+        for key in (
+            "tencent_no_endorsement_notice", "full_license_terms_available_to_users",
+            "acceptable_use_and_local_law_checked",
+            "commercial_media_rights_checked", "operator_terms_reviewed",
+        ):
+            with self.subTest(field=key), self.assertRaises(MotionError):
+                reviewed(**{key: False}).assert_allowed()
+        with self.assertRaises(MotionError):
+            reviewed(actual_provider_legal_name="").assert_allowed()
+        with self.assertRaises(MotionError):
+            reviewed(intended_publication_countries=()).assert_allowed()
+
+    def test_large_licensee_requires_separate_license(self):
+        with self.assertRaises(MotionError):
+            reviewed(monthly_active_users_at_model_release=100_000_001).assert_allowed()
+        self.assertIsNone(reviewed(
+            monthly_active_users_at_model_release=100_000_001,
+            separate_tencent_license_if_required=True).assert_allowed())
+
+    def test_unknown_or_forged_country_and_mau(self):
+        for country in ("", "india", "U1", None, "gb"):
+            with self.subTest(country=country), self.assertRaises(MotionError):
+                reviewed(retailer_country=country).assert_allowed()
+        for mau in (-1, float("nan"), True, None):
+            with self.subTest(mau=mau), self.assertRaises(MotionError):
+                reviewed(monthly_active_users_at_model_release=mau).assert_allowed()
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

## tests/ai/test_feature5_motion.py

~~~~diff
@@ -0,0 +1,462 @@
+"""Feature #5 offline tests. No GPUs, model downloads, Azure or provider billing."""
+import json
+from decimal import Decimal
+from pathlib import Path
+import subprocess
+import sys
+import tempfile
+import unittest
+from unittest.mock import Mock, patch
+from uuid import uuid4
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT))
+
+from feature5_motion.contracts import AssetGrant, MotionSpec, MotionError, estimate_cost, validate_source
+from feature5_motion.runner import HunyuanLocalRunner
+from feature5_motion.worker import MotionWorker, validate_clip
+from feature5_motion.azure_pricing import VerifiedAzureRates, MotionSpendGuard
+
+
+def uid():
+    return str(uuid4())
+
+
+class TestMotionContracts(unittest.TestCase):
+    def setUp(self):
+        self.shop, self.job, self.asset = uid(), uid(), uid()
+
+    def spec(self, **kw):
+        args = dict(job_id=self.job, shop_id=self.shop, prompt="Adult model walking in a boutique", mode="text")
+        args.update(kw)
+        return MotionSpec(**args)
+
+    def grant(self, **kw):
+        args = dict(asset_id=self.asset, shop_id=self.shop, approved=True,
+                    private=True, commercial_rights=True, media_type="image/png", clean_layers=True)
+        args.update(kw)
+        return AssetGrant(**args)
+
+    def test_text_mode(self):
+        spec = self.spec()
+        validate_source(spec, None)
+        self.assertEqual(spec.duration_seconds, 5)
+
+    def test_image_and_poster_mode(self):
+        for mode in ("image", "poster"):
+            spec = self.spec(mode=mode, source_asset_id=self.asset)
+            validate_source(spec, self.grant())
+            self.assertEqual(spec.mode, mode)
+
+    def test_cross_tenant_and_unapproved_rejected(self):
+        spec = self.spec(mode="image", source_asset_id=self.asset)
+        for grant in (self.grant(shop_id=uid()), self.grant(approved=False),
+                      self.grant(private=False), self.grant(commercial_rights=False),
+                      self.grant(asset_id=uid()), self.grant(media_type="video/mp4")):
+            with self.assertRaises(MotionError):
+                validate_source(spec, grant)
+
+    def test_poster_requires_clean_visual(self):
+        with self.assertRaises(MotionError):
+            validate_source(self.spec(mode="poster", source_asset_id=self.asset),
+                            self.grant(clean_layers=False))
+
+    def test_invalid_mode_and_image(self):
+        for data in ({"mode": "video"}, {"mode": "image"},
+                     {"mode": "text", "source_asset_id": self.asset},
+                     {"mode": "image", "source_asset_id": "http://evil.invalid/a.png"}):
+            with self.assertRaises(MotionError):
+                self.spec(**data)
+
+    def test_bounded_generation_settings(self):
+        for changes in ({"duration_seconds": 30}, {"resolution": "1080p"},
+                        {"fps": 30}, {"aspect_ratio": "4:3"}, {"seed": -1},
+                        {"prompt": ""}, {"prompt": "x" * 1501},
+                        {"job_id": "../not-a-uuid"}, {"prompt_version": "unreviewed"}):
+            with self.assertRaises(MotionError):
+                self.spec(**changes)
+
+    def test_budget_includes_coldstart_storage_egress(self):
+        estimate = estimate_cost(gpu_usd_hour="1", cpu_usd_hour="0.2", gpu_seconds=120,
+                                 cold_start_seconds=60, cpu_seconds=60,
+                                 storage_gb="0.1", storage_usd_gb="0.02",
+                                 egress_gb="0.05", egress_usd_gb="0.10")
+        self.assertEqual(str(estimate.gpu_compute_usd), "0.0500")
+        self.assertEqual(str(estimate.total_usd), "0.0604")
+
+    def test_cost_negative_or_nan_rejected(self):
+        for cost in ("-2", "NaN", "Infinity", "abc"):
+            with self.assertRaises(MotionError):
+                estimate_cost(gpu_usd_hour=cost, cpu_usd_hour="0", gpu_seconds=5, cold_start_seconds=1)
+
+
+class TestGpuRunner(unittest.TestCase):
+    def setUp(self):
+        self.spec = MotionSpec(job_id=uid(), shop_id=uid(), prompt="Luxury boutique", mode="text")
+
+    def test_no_gpu_no_cost_gate(self):
+        with tempfile.TemporaryDirectory() as temp:
+            wd = Path(temp)
+            runner = HunyuanLocalRunner(checkout=wd, weights=wd)
+            with self.assertRaises(MotionError):
+                runner.run(self.spec, source_file=None, workdir=wd)
+
+    def test_approved_gate_still_requires_existing_model(self):
+        with tempfile.TemporaryDirectory() as temp:
+            wd = Path(temp)
+            runner = HunyuanLocalRunner(checkout=wd, weights=wd, enabled=True,
+                                        license_approved=True, gpu_budget_approved=True)
+            with self.assertRaises(MotionError):
+                runner.run(self.spec, source_file=None, workdir=wd)
+
+    def test_timeout_boundaries(self):
+        for seconds in (0, 29, 3601):
+            with self.assertRaises(MotionError):
+                HunyuanLocalRunner(checkout=Path("."), weights=Path("."), timeout_seconds=seconds)
+
+
+class TestMediaValidation(unittest.TestCase):
+    def test_valid_local_media_probe(self):
+        with tempfile.TemporaryDirectory() as temp:
+            clip = Path(temp) / "clip.mp4"
+            clip.write_bytes(b"synthetic-placeholder")
+            data = {"format": {"duration": "5.01"}, "streams": [
+                {"codec_type": "video", "codec_name": "h264", "width": 480,
+                 "height": 832, "r_frame_rate": "24/1"}]}
+            with patch("feature5_motion.worker.subprocess.run",
+                       return_value=Mock(stdout=json.dumps(data).encode())) as probe:
+                self.assertEqual(validate_clip(clip)["codec"], "h264")
+                self.assertIn("-protocol_whitelist", probe.call_args.args[0])
+                self.assertIn("file", probe.call_args.args[0])
+
+    def test_probe_invalid_codec_fps_duration(self):
+        with tempfile.TemporaryDirectory() as temp:
+            clip = Path(temp) / "clip.mp4"
+            clip.write_bytes(b"fixture")
+            for change in ({"duration": "25"}, {"codec_name": "vp9"}, {"r_frame_rate": "30/1"}):
+                stream = {"codec_type": "video", "codec_name": "h264",
+                          "width": 480, "height": 832, "r_frame_rate": "24/1"}
+                duration = change.pop("duration", "5")
+                stream.update(change)
+                with patch("feature5_motion.worker.subprocess.run", return_value=Mock(
+                    stdout=json.dumps({"format": {"duration": duration}, "streams": [stream]}).encode()
+                )):
+                    with self.assertRaises(MotionError):
+                        validate_clip(clip)
+
+    def test_invalid_or_untrusted_file_rejected(self):
+        with tempfile.TemporaryDirectory() as temp:
+            clip = Path(temp) / "clip.txt"
+            clip.write_bytes(b"not an mp4")
+            with self.assertRaises(MotionError):
+                validate_clip(clip)
+
+
+class TestMotionWorker(unittest.TestCase):
+    def setUp(self):
+        self.shop, self.job, self.asset, self.token = uid(), uid(), uid(), uid()
+        self.spec = MotionSpec(job_id=self.job, shop_id=self.shop, prompt="Adult model fashion walk",
+                               mode="image", source_asset_id=self.asset)
+        self.grant = AssetGrant(self.asset, self.shop, True, True, True, "image/png")
+        self.store = Mock()
+        self.media = Mock()
+        self.runner = Mock()
+        self.runner.timeout_seconds = 30
+        rates = VerifiedAzureRates("eastus", "A100", Decimal("0.000529"),
+                                   Decimal("0.000024"), Decimal("0.000003"),
+                                   "2026-04-01T00:00:00Z")
+        self.guard = MotionSpendGuard(
+            rates, max_billable_seconds=30, vcpus=4, gib_memory=16,
+            ancillary_allowance_usd=Decimal("0.005"),
+        )
+        self.store.claim.return_value = {"attempt_token": self.token, "spec": self.spec,
+                                         "reserved_usd": 0.1, "review_status": "APPROVED"}
+        self.store.complete.return_value = True
+        self.store.fail.return_value = True
+        self.store.mark_unknown.return_value = True
+        self.media.grant.return_value = self.grant
+        self.media.upload_private.return_value = {
+            "shop_id": self.shop, "job_id": self.job, "attempt_token": self.token,
+            "bucket": "retailgrowth-media",
+            "path": f"{self.shop}/renders/{self.job}/{self.token}.mp4", "private": True,
+        }
+
+    def test_no_claim_no_generation(self):
+        with tempfile.TemporaryDirectory() as temp:
+            self.store.claim.return_value = None
+            worker = MotionWorker(store=self.store, media=self.media, runner=self.runner,
+                                  workdir_root=Path(temp), enabled=True, credit_cap_usd=1, cost_guard=self.guard)
+            self.assertEqual(worker.execute(self.job), "NOT_CLAIMED")
+            self.runner.run.assert_not_called()
+
+    def test_no_budget_or_approval_fails_closed(self):
+        with tempfile.TemporaryDirectory() as temp:
+            worker = MotionWorker(store=self.store, media=self.media, runner=self.runner,
+                                  workdir_root=Path(temp), enabled=False, credit_cap_usd=1, cost_guard=self.guard)
+            with self.assertRaises(MotionError):
+                worker.execute(self.job)
+            self.store.claim.assert_not_called()
+            worker.enabled = True
+            self.store.claim.return_value["review_status"] = "DRAFT"
+            with self.assertRaises(MotionError):
+                worker.execute(self.job)
+            self.runner.run.assert_not_called()
+
+    def test_foreign_asset_does_not_start_gpu(self):
+        with tempfile.TemporaryDirectory() as temp:
+            self.media.grant.return_value = AssetGrant(self.asset, uid(), True, True, True, "image/png")
+            worker = MotionWorker(store=self.store, media=self.media, runner=self.runner,
+                                  workdir_root=Path(temp), enabled=True, credit_cap_usd=1, cost_guard=self.guard)
+            self.assertEqual(worker.execute(self.job), "FAILED")
+            self.runner.run.assert_not_called()
+            self.media.upload_private.assert_not_called()
+            self.store.fail.assert_called_once()
+
+    def test_successful_mock_contract_no_real_inference(self):
+        with tempfile.TemporaryDirectory() as temp:
+            self.media.stage.side_effect = lambda shop, asset, wd: wd / "source.png"
+            def fake_run(spec, *, source_file, workdir):
+                out = workdir / "motion.mp4"
+                out.write_bytes(b"mock-not-real-media")
+                return out
+            self.runner.run.side_effect = fake_run
+            worker = MotionWorker(store=self.store, media=self.media, runner=self.runner,
+                                  workdir_root=Path(temp), enabled=True, credit_cap_usd=1, cost_guard=self.guard)
+            with patch("feature5_motion.worker.validate_clip", return_value={
+                "codec": "h264", "duration_seconds": 5, "fps": 24}):
+                self.assertEqual(worker.execute(self.job), "SUCCEEDED")
+            self.store.complete.assert_called_once()
+            metadata = self.media.upload_private.call_args.args[4]
+            self.assertTrue(metadata["quality_review_required"])
+            self.assertEqual(metadata["source_asset_id"], self.asset)
+            self.assertEqual(metadata["reserved_usd"], "0.1")
+            self.assertGreaterEqual(metadata["compute_seconds_measured"], 0)
+            self.assertIn("estimated_observed_compute_usd", metadata)
+            self.assertIn("maximum_compute_budget_usd", metadata)
+            self.assertFalse((Path(temp) / self.job / self.token).exists(),
+                             "private original and clip must be deleted after import")
+
+    def test_atomic_completion_failure_is_unknown_not_refund(self):
+        with tempfile.TemporaryDirectory() as temp:
+            self.media.stage.side_effect = lambda shop, asset, wd: wd / "source.png"
+            self.runner.run.side_effect = lambda spec, *, source_file, workdir: workdir / "motion.mp4"
+            self.store.complete.return_value = False
+            worker = MotionWorker(store=self.store, media=self.media, runner=self.runner,
+                                  workdir_root=Path(temp), enabled=True, credit_cap_usd=1, cost_guard=self.guard)
+            with patch("feature5_motion.worker.validate_clip", return_value={"codec": "h264"}):
+                self.assertEqual(worker.execute(self.job), "UNKNOWN")
+            self.store.mark_unknown.assert_called_once()
+            self.store.fail.assert_not_called()
+
+    def test_db_completion_timeout_after_upload_is_unknown(self):
+        with tempfile.TemporaryDirectory() as temp:
+            self.media.stage.side_effect = lambda shop, asset, wd: wd / "source.png"
+            self.runner.run.side_effect = lambda spec, *, source_file, workdir: workdir / "motion.mp4"
+            self.store.complete.side_effect = TimeoutError("unknown database commit")
+            worker = MotionWorker(store=self.store, media=self.media, runner=self.runner,
+                                  workdir_root=Path(temp), enabled=True, credit_cap_usd=1, cost_guard=self.guard)
+            with patch("feature5_motion.worker.validate_clip", return_value={"codec": "h264"}):
+                self.assertEqual(worker.execute(self.job), "UNKNOWN")
+            self.store.mark_unknown.assert_called_once_with(self.job, self.token, "FINALIZE_UNCERTAIN")
+            self.store.fail.assert_not_called()
+            self.runner.run.assert_called_once()
+
+    def test_non_private_receipt_rejected(self):
+        with tempfile.TemporaryDirectory() as temp:
+            self.runner.run.side_effect = lambda spec, *, source_file, workdir: workdir / "motion.mp4"
+            self.media.upload_private.return_value = {"shop_id": uid(), "job_id": self.job}
+            worker = MotionWorker(store=self.store, media=self.media, runner=self.runner,
+                                  workdir_root=Path(temp), enabled=True, credit_cap_usd=1, cost_guard=self.guard)
+            with patch("feature5_motion.worker.validate_clip", return_value={"codec": "h264"}):
+                self.assertEqual(worker.execute(self.job), "UNKNOWN")
+            self.store.complete.assert_not_called()
+            self.store.fail.assert_not_called()
+            self.store.mark_unknown.assert_called_once()
+
+    def test_wrong_private_path_or_lease_is_unknown_not_success(self):
+        with tempfile.TemporaryDirectory() as temp:
+            expected = f"{self.shop}/renders/{self.job}/{self.token}.mp4"
+            variations = [
+                {"path": expected + ".backup"},
+                {"path": f"{self.shop}/renders/{self.job}/{uid()}.mp4"},
+                {"attempt_token": uid()},
+                {"bucket": "public"},
+                {"private": False},
+            ]
+            for overrides in variations:
+                self.store.reset_mock()
+                self.store.claim.return_value = {"attempt_token": self.token, "spec": self.spec,
+                                                 "reserved_usd": 0.1, "review_status": "APPROVED"}
+                self.store.mark_unknown.return_value = True
+                receipt = {"shop_id": self.shop, "job_id": self.job, "attempt_token": self.token,
+                           "bucket": "retailgrowth-media", "path": expected, "private": True}
+                receipt.update(overrides)
+                self.media.upload_private.return_value = receipt
+                self.runner.run.side_effect = lambda spec, *, source_file, workdir: workdir / "motion.mp4"
+                worker = MotionWorker(store=self.store, media=self.media, runner=self.runner,
+                                      workdir_root=Path(temp), enabled=True, credit_cap_usd=1, cost_guard=self.guard)
+                with patch("feature5_motion.worker.validate_clip", return_value={"codec": "h264"}):
+                    self.assertEqual(worker.execute(self.job), "UNKNOWN")
+                self.store.complete.assert_not_called()
+                self.store.fail.assert_not_called()
+                self.store.mark_unknown.assert_called_once()
+
+    def test_upload_uncertainty_never_causes_retry_or_refund(self):
+        with tempfile.TemporaryDirectory() as temp:
+            self.runner.run.side_effect = lambda spec, *, source_file, workdir: workdir / "motion.mp4"
+            self.media.upload_private.side_effect = TimeoutError("sensitive vendor information")
+            worker = MotionWorker(store=self.store, media=self.media, runner=self.runner,
+                                  workdir_root=Path(temp), enabled=True, credit_cap_usd=1, cost_guard=self.guard)
+            with patch("feature5_motion.worker.validate_clip", return_value={"codec": "h264"}):
+                self.assertEqual(worker.execute(self.job), "UNKNOWN")
+            self.store.complete.assert_not_called()
+            self.store.fail.assert_not_called()
+            self.store.mark_unknown.assert_called_once_with(
+                self.job, self.token, "PRIVATE_UPLOAD_UNCERTAIN")
+            self.assertFalse((Path(temp) / self.job / self.token).exists())
+
+    def test_gpu_subprocess_timeout_never_becomes_refundable_failure(self):
+        with tempfile.TemporaryDirectory() as temp:
+            self.runner.run.side_effect = TimeoutError("paid GPU timeout")
+            worker = MotionWorker(
+                store=self.store, media=self.media, runner=self.runner,
+                workdir_root=Path(temp), enabled=True, credit_cap_usd=1,
+                cost_guard=self.guard,
+            )
+            self.assertEqual(worker.execute(self.job), "UNKNOWN")
+            self.store.mark_unknown.assert_called_once_with(
+                self.job, self.token, "GPU_ATTEMPT_UNCERTAIN")
+            self.store.fail.assert_not_called()
+            self.store.complete.assert_not_called()
+            self.media.upload_private.assert_not_called()
+
+    def test_invalid_output_after_gpu_never_refunds_or_retries(self):
+        with tempfile.TemporaryDirectory() as temp:
+            self.runner.run.side_effect = lambda spec, *, source_file, workdir: workdir / "missing.mp4"
+            worker = MotionWorker(
+                store=self.store, media=self.media, runner=self.runner,
+                workdir_root=Path(temp), enabled=True, credit_cap_usd=1,
+                cost_guard=self.guard,
+            )
+            with patch("feature5_motion.worker.validate_clip",
+                       side_effect=MotionError("Invalid encoded video")):
+                self.assertEqual(worker.execute(self.job), "UNKNOWN")
+            self.store.mark_unknown.assert_called_once_with(
+                self.job, self.token, "GPU_ATTEMPT_UNCERTAIN")
+            self.store.fail.assert_not_called()
+            self.media.upload_private.assert_not_called()
+
+    def test_pre_gpu_stage_exception_uses_failure_without_gpu_spend(self):
+        with tempfile.TemporaryDirectory() as temp:
+            self.media.stage.side_effect = MotionError("Rejected private staging")
+            worker = MotionWorker(
+                store=self.store, media=self.media, runner=self.runner,
+                workdir_root=Path(temp), enabled=True, credit_cap_usd=1,
+                cost_guard=self.guard,
+            )
+            self.assertEqual(worker.execute(self.job), "FAILED")
+            self.runner.run.assert_not_called()
+            self.store.fail.assert_called_once_with(
+                self.job, self.token, "PRE_GPU_VALIDATION_FAILURE")
+            self.store.mark_unknown.assert_not_called()
+
+    def test_unknown_db_persistence_failure_never_downgrades_to_failed(self):
+        from feature5_motion.worker import ReconciliationRequired
+        with tempfile.TemporaryDirectory() as temp:
+            self.runner.run.side_effect = TimeoutError("GPU status unknown")
+            self.store.mark_unknown.return_value = False
+            worker = MotionWorker(
+                store=self.store, media=self.media, runner=self.runner,
+                workdir_root=Path(temp), enabled=True, credit_cap_usd=1,
+                cost_guard=self.guard,
+            )
+            with self.assertRaises(ReconciliationRequired):
+                worker.execute(self.job)
+            self.store.fail.assert_not_called()
+            self.store.complete.assert_not_called()
+
+    def test_nonfinite_budget_must_not_authorize_inference(self):
+        for cap in (float("nan"), float("inf"), float("-inf"), True, "not-money", 0):
+            with tempfile.TemporaryDirectory() as temp:
+                self.store.reset_mock()
+                worker = MotionWorker(store=self.store, media=self.media, runner=self.runner,
+                                      workdir_root=Path(temp), enabled=True, credit_cap_usd=cap, cost_guard=self.guard)
+                with self.assertRaises(MotionError):
+                    worker.execute(self.job)
+                self.store.claim.assert_not_called()
+                self.runner.run.assert_not_called()
+
+    def test_missing_gpu_cost_ceiling_fails_before_claim(self):
+        with tempfile.TemporaryDirectory() as temp:
+            worker = MotionWorker(store=self.store, media=self.media, runner=self.runner,
+                                  workdir_root=Path(temp), enabled=True, credit_cap_usd=1)
+            with self.assertRaisesRegex(MotionError, "cost ceiling"):
+                worker.execute(self.job)
+            self.store.claim.assert_not_called()
+            self.runner.run.assert_not_called()
+
+    def test_insufficient_reservation_cannot_start_gpu(self):
+        with tempfile.TemporaryDirectory() as temp:
+            self.store.claim.return_value["reserved_usd"] = "0.001"
+            worker = MotionWorker(store=self.store, media=self.media, runner=self.runner,
+                                  workdir_root=Path(temp), enabled=True, credit_cap_usd=1,
+                                  cost_guard=self.guard)
+            with self.assertRaisesRegex(MotionError, "worst-case GPU spend"):
+                worker.execute(self.job)
+            self.runner.run.assert_not_called()
+
+    def test_runner_timeout_above_approved_spend_denied(self):
+        with tempfile.TemporaryDirectory() as temp:
+            self.runner.timeout_seconds = 1800
+            worker = MotionWorker(store=self.store, media=self.media, runner=self.runner,
+                                  workdir_root=Path(temp), enabled=True, credit_cap_usd=1,
+                                  cost_guard=self.guard)
+            with self.assertRaisesRegex(MotionError, "spending ceiling"):
+                worker.execute(self.job)
+            self.store.claim.assert_not_called()
+            self.runner.run.assert_not_called()
+
+    def test_elapsed_gpu_runtime_over_cap_requires_unknown_reconciliation(self):
+        with tempfile.TemporaryDirectory() as temp:
+            self.runner.run.side_effect = lambda spec, *, source_file, workdir: workdir / "motion.mp4"
+            worker = MotionWorker(
+                store=self.store, media=self.media, runner=self.runner,
+                workdir_root=Path(temp), enabled=True, credit_cap_usd=1,
+                cost_guard=self.guard,
+            )
+            with patch("feature5_motion.worker.monotonic", side_effect=[100.0, 131.0]):
+                self.assertEqual(worker.execute(self.job), "UNKNOWN")
+            self.store.mark_unknown.assert_called_once_with(
+                self.job, self.token, "GPU_RUNTIME_OVER_CAP")
+            self.store.fail.assert_not_called()
+            self.media.upload_private.assert_not_called()
+
+    def test_failed_unknown_persistence_never_downgrades_to_refundable_failed(self):
+        from feature5_motion.worker import ReconciliationRequired
+        with tempfile.TemporaryDirectory() as temp:
+            self.runner.run.side_effect = lambda spec, *, source_file, workdir: workdir / "motion.mp4"
+            self.store.mark_unknown.return_value = False
+            worker = MotionWorker(
+                store=self.store, media=self.media, runner=self.runner,
+                workdir_root=Path(temp), enabled=True, credit_cap_usd=1,
+                cost_guard=self.guard,
+            )
+            with patch("feature5_motion.worker.monotonic", side_effect=[100.0, 131.0]):
+                with self.assertRaises(ReconciliationRequired):
+                    worker.execute(self.job)
+            self.store.fail.assert_not_called()
+            self.store.complete.assert_not_called()
+
+    def test_nonfinite_db_reservation_denied(self):
+        for bad in (float("nan"), float("inf"), True, -1, "invalid"):
+            with tempfile.TemporaryDirectory() as temp:
+                self.store.claim.return_value["reserved_usd"] = bad
+                worker = MotionWorker(store=self.store, media=self.media, runner=self.runner,
+                                      workdir_root=Path(temp), enabled=True, credit_cap_usd=1, cost_guard=self.guard)
+                with self.assertRaises(MotionError):
+                    worker.execute(self.job)
+                self.runner.run.assert_not_called()
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

## tests/ai/test_feature5_quality_review.py

~~~~diff
@@ -0,0 +1,80 @@
+"""Human visual review gate contract; no actual AI video asserted."""
+import sys
+import unittest
+from pathlib import Path
+from uuid import uuid4
+sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
+from feature5_motion.contracts import MotionError
+from feature5_motion.quality_review import VisualReview, review_template, CATEGORIES
+
+
+def uid():
+    return str(uuid4())
+
+
+class TestQualityApproval(unittest.TestCase):
+    def setUp(self):
+        self.shop = uid()
+        self.hash = "e" * 64
+        self.row = {
+            "shop_id": self.shop, "job_id": uid(), "source_asset_id": uid(),
+            "output_asset_id": uid(), "reviewer_user_id": uid(),
+            "reviewed_sha256": self.hash,
+            "checks": {name: True for name in CATEGORIES},
+            "decision": "APPROVED",
+            "notes": "Reviewer compared garment and source; no defects detected.",
+            "ai_disclosure_approved": True,
+        }
+
+    def test_blank_template_does_not_auto_approve(self):
+        self.assertTrue(all(value is False for value in review_template().values()))
+        record = VisualReview(**dict(self.row, checks=review_template()))
+        with self.assertRaises(MotionError):
+            record.approved_for_feature4(
+                authoritative_shop_id=self.shop, actual_media_sha256=self.hash,
+                reviewer_has_write_role=True)
+
+    def test_review_can_authorize_only_exact_private_clip(self):
+        r = VisualReview(**self.row)
+        self.assertTrue(r.approved_for_feature4(
+            authoritative_shop_id=self.shop, actual_media_sha256=self.hash,
+            reviewer_has_write_role=True))
+        with self.assertRaises(MotionError):
+            r.approved_for_feature4(
+                authoritative_shop_id=uid(), actual_media_sha256=self.hash,
+                reviewer_has_write_role=True)
+        with self.assertRaises(MotionError):
+            r.approved_for_feature4(
+                authoritative_shop_id=self.shop, actual_media_sha256="0" * 64,
+                reviewer_has_write_role=True)
+        with self.assertRaises(MotionError):
+            r.approved_for_feature4(
+                authoritative_shop_id=self.shop, actual_media_sha256=self.hash,
+                reviewer_has_write_role=False)
+
+    def test_bad_motion_and_unreviewed_disclosure_rejected(self):
+        for change in (
+            {"decision": "REJECTED"},
+            {"ai_disclosure_approved": False},
+            {"checks": dict(self.row["checks"], garment_pattern=False)},
+            {"checks": dict(self.row["checks"], face_consistency=False)},
+            {"checks": dict(self.row["checks"], temporal_consistency=False)},
+        ):
+            r = VisualReview(**dict(self.row, **change))
+            with self.assertRaises(MotionError):
+                r.approved_for_feature4(
+                    authoritative_shop_id=self.shop, actual_media_sha256=self.hash,
+                    reviewer_has_write_role=True)
+
+    def test_missing_checks_and_unsafe_review_structure(self):
+        for values in ({}, {"garment_color": True}, dict(self.row["checks"], lip_sync="ignored")):
+            with self.assertRaises(MotionError):
+                VisualReview(**dict(self.row, checks=values))
+        with self.assertRaises(MotionError):
+            VisualReview(**dict(self.row, reviewed_sha256="arbitrary"))
+        with self.assertRaises(MotionError):
+            VisualReview(**dict(self.row, notes="ok"))
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

## tests/ai/test_feature5_real_ffmpeg_media.py

~~~~diff
@@ -0,0 +1,123 @@
+"""Real FFmpeg media integration checks (synthetic images, NOT Hunyuan inference).
+
+Generates and probes genuine H.264 MP4 bytes on CI hosts with FFmpeg. These
+checks verify the machine-readable handoff profile but NOT fashion/visual QA
+or Feature4's separate unmerged rendering implementation.
+"""
+from __future__ import annotations
+
+import shutil
+import subprocess
+import sys
+import tempfile
+import unittest
+from pathlib import Path
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT))
+from feature5_motion.contracts import MotionError
+from feature5_motion.worker import validate_clip
+from feature5_motion.visual_review_artifacts import prepare_visual_review, TIMESTAMPS
+from feature5_motion.acceptance import export_pending_review
+
+
+@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
+                     "FFmpeg and ffprobe executable binaries are required")
+class TestFeature5RealFFmpegMedia(unittest.TestCase):
+    def setUp(self):
+        self.temp = tempfile.TemporaryDirectory(prefix="feature5-machine-media-")
+        self.addCleanup(self.temp.cleanup)
+        self.root = Path(self.temp.name)
+
+    def make_clip(self, name: str, *, fps: int = 24, seconds: int = 5) -> Path:
+        target = self.root / name
+        cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
+               "-f", "lavfi", "-i", f"color=c=navy:s=480x832:r={fps}",
+               "-t", str(seconds), "-c:v", "libx264", "-preset", "ultrafast",
+               "-pix_fmt", "yuv420p", "-an", "-movflags", "+faststart",
+               "-y", str(target)]
+        proc = subprocess.run(cmd, capture_output=True, timeout=45)
+        if proc.returncode != 0:
+            self.fail("Expected CI FFmpeg binary with H.264 libx264 encoder")
+        self.assertGreater(target.stat().st_size, 1024)
+        return target
+
+    def test_genuine_five_second_clip_meets_private_motion_profile(self):
+        actual = self.make_clip("genuine-synthetic.mp4")
+        result = validate_clip(actual)
+        self.assertEqual((result["width"], result["height"]), (480, 832))
+        self.assertEqual(result["codec"], "h264")
+        self.assertEqual(result["fps"], 24)
+        self.assertGreater(result["bytes"], 1024)
+        self.assertTrue(4.5 <= result["duration_seconds"] <= 5.5)
+
+    def test_real_mp4_produces_six_review_frames_and_immutable_hash(self):
+        from hashlib import sha256
+        from PIL import Image
+        clip = self.make_clip("review-clip.mp4")
+        destination = self.root / "review"
+        result = prepare_visual_review(clip, destination)
+        self.assertEqual(result["status"], "PENDING_HUMAN_REVIEW")
+        self.assertEqual(len(result["frames"]), len(TIMESTAMPS))
+        self.assertEqual(result["clip_sha256"], sha256(clip.read_bytes()).hexdigest())
+        self.assertEqual(len(result["clip_sha256"]), 64)
+        self.assertTrue((destination / "review-manifest.json").is_file())
+        for frame in result["frames"]:
+            self.assertTrue((destination / frame["file"]).is_file())
+            self.assertEqual(len(frame["sha256"]), 64)
+        with Image.open(destination / "contact-sheet.png") as sheet:
+            self.assertEqual(sheet.size, (750, 954))
+        with self.assertRaises(MotionError):
+            prepare_visual_review(clip, destination)
+
+    def test_reviewer_materials_fail_closed_for_bad_duration(self):
+        clip = self.make_clip("not-reviewable.mp4", seconds=4)
+        output = self.root / "reject-review"
+        with self.assertRaises(MotionError):
+            prepare_visual_review(clip, output)
+        self.assertFalse(output.exists())
+
+    def test_real_synthetic_clip_preserved_as_pending_private_human_review(self):
+        import hashlib
+        clip = self.make_clip("export-test.mp4")
+        root = self.root / "private-review-evidence"
+        record = export_pending_review(
+            clip, root, mode="text", approved_model_manifest_sha256="b" * 64,
+        )
+        self.assertEqual(record["status"], "PENDING_HUMAN_REVIEW")
+        self.assertIsNone(record["reference_sha256"])
+        self.assertEqual(record["clip_sha256"], hashlib.sha256(clip.read_bytes()).hexdigest())
+        self.assertTrue((root / "clip.mp4").is_file())
+        self.assertTrue((root / "review" / "contact-sheet.png").is_file())
+        self.assertTrue((root / "acceptance-pending.json").is_file())
+        with self.assertRaises(MotionError):
+            export_pending_review(clip, root, mode="text",
+                                  approved_model_manifest_sha256="b" * 64)
+
+    def test_real_image_reference_export_is_private_and_reviewable(self):
+        import hashlib
+        from PIL import Image
+        clip = self.make_clip("i2v-synthetic.mp4")
+        reference = self.root / "fashion-source.png"
+        Image.new("RGB", (480, 832), color="red").save(reference)
+        evidence = self.root / "i2v-evidence"
+        record = export_pending_review(
+            clip, evidence, mode="image", source_image=reference,
+            approved_model_manifest_sha256="b" * 64)
+        self.assertEqual(record["reference_sha256"],
+                         hashlib.sha256(reference.read_bytes()).hexdigest())
+        self.assertTrue((evidence / "reference.png").is_file())
+        self.assertEqual(validate_clip(evidence / "clip.mp4")["fps"], 24)
+        self.assertEqual(record["status"], "PENDING_HUMAN_REVIEW")
+
+    def test_real_wrong_fps_and_duration_fail_closed(self):
+        bad_fps = self.make_clip("fps-30.mp4", fps=30)
+        with self.assertRaises(MotionError):
+            validate_clip(bad_fps)
+        bad_length = self.make_clip("short-4-seconds.mp4", seconds=4)
+        with self.assertRaises(MotionError):
+            validate_clip(bad_length)
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

## tests/ai/test_feature5_runner_cli.py

~~~~diff
@@ -0,0 +1,189 @@
+"""Official Tencent generate.py argument contract tests. No GPU or vendor calls."""
+from pathlib import Path
+import subprocess
+import sys
+import tempfile
+import unittest
+from unittest.mock import Mock, patch
+from uuid import uuid4
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT))
+from feature5_motion.contracts import MotionError, MotionSpec
+from feature5_motion.runner import HunyuanLocalRunner, git_blob_sha1, verify_official_script, OFFICIAL_GENERATE_BLOB
+from feature5_motion.license_gate import HunyuanLicensePolicy
+from feature5_motion.artifact_lock import ArtifactLock
+
+
+def uid():
+    return str(uuid4())
+
+
+class TestOfficialHunyuanCLI(unittest.TestCase):
+    def setUp(self):
+        self.temp = tempfile.TemporaryDirectory()
+        self.addCleanup(self.temp.cleanup)
+        self.root = Path(self.temp.name)
+        self.checkout = self.root / "pinned-checkout"
+        self.weights = self.root / "installed-weights"
+        self.workdir = self.root / "private-job"
+        for p in (self.checkout, self.weights, self.workdir):
+            p.mkdir()
+        (self.checkout / "generate.py").write_text("# stub - never executed\n")
+        # Synthetic operator approval fixture: NOT an actual Tencent approval.
+        policy = HunyuanLicensePolicy(
+            deployment_country="US", retailer_country="IN",
+            intended_publication_countries=("IN",),
+            actual_provider_legal_name="RetailGrowthAI DEV Test",
+            tencent_no_endorsement_notice=True,
+            full_license_terms_available_to_users=True,
+            acceptable_use_and_local_law_checked=True,
+            commercial_media_rights_checked=True,
+            operator_terms_reviewed=True, monthly_active_users_at_model_release=0,
+        )
+        self.runner = HunyuanLocalRunner(
+            checkout=self.checkout, weights=self.weights, enabled=True,
+            license_approved=True, gpu_budget_approved=True, timeout_seconds=30,
+            license_policy=policy,
+            artifact_lock=ArtifactLock(self.root / "reviewed-artifact-lock.json", "a" * 64),
+        )
+        # CPU-only mock test: never discover or rent actual GPU hardware.
+        self.gpu_preflight = patch.object(HunyuanLocalRunner, "_require_supported_gpu")
+        self.gpu_preflight.start()
+        self.addCleanup(self.gpu_preflight.stop)
+        # Fixture generate.py is deliberately not the vendor's 19KB source.
+        # These argument tests patch integrity; independent integrity tests
+        # below assert that the real gate rejects stub/tampered code.
+        self.pinned_script = patch("feature5_motion.runner.verify_official_script")
+        self.pinned_script.start()
+        self.addCleanup(self.pinned_script.stop)
+        self.verified_weights = patch.object(ArtifactLock, "verify", return_value="a" * 64)
+        self.verified_weights.start()
+        self.addCleanup(self.verified_weights.stop)
+
+    def spec(self, mode="text"):
+        return MotionSpec(job_id=uid(), shop_id=uid(), prompt="Adult model in boutique",
+                          mode=mode, source_asset_id=uid() if mode != "text" else None)
+
+    def _fake_launch(self, popen):
+        def launch(*args, **kwargs):
+            # Only create the fixture after the runner passes its no-overwrite check.
+            (self.workdir / "motion.mp4").write_bytes(b"MOCK OUTPUT NOT REAL AI MEDIA")
+            proc = Mock()
+            proc.communicate.return_value = (None, None)
+            proc.returncode = 0
+            return proc
+        popen.side_effect = launch
+
+    def test_text_mode_does_not_pass_image_path(self):
+        with patch("feature5_motion.runner.subprocess.Popen") as popen:
+            self._fake_launch(popen)
+            output = self.runner.run(self.spec(), source_file=None, workdir=self.workdir)
+            args = popen.call_args.args[0]
+            self.assertNotIn("--image_path", args)
+            self.assertEqual(args[args.index("--video_length") + 1], "121")
+            self.assertEqual(args[args.index("--resolution") + 1], "480p")
+            self.assertEqual(args[args.index("--sr") + 1], "false")
+            self.assertEqual(args[args.index("--rewrite") + 1], "false")
+            self.assertEqual(popen.call_args.kwargs["env"]["HF_HUB_OFFLINE"], "1")
+            self.assertEqual(popen.call_args.kwargs["stdout"], subprocess.DEVNULL)
+            self.assertEqual(output, self.workdir / "motion.mp4")
+
+    def test_image_mode_passes_validated_staged_frame(self):
+        from PIL import Image
+        source = self.workdir / "reference.png"
+        Image.new("RGB", (480, 832), color="red").save(source)
+        with patch("feature5_motion.runner.subprocess.Popen") as popen:
+            self._fake_launch(popen)
+            self.runner.run(self.spec("image"), source_file=source, workdir=self.workdir)
+            args = popen.call_args.args[0]
+            self.assertEqual(args[args.index("--image_path") + 1], str(source))
+
+    def test_corrupt_image_is_rejected_before_spending_gpu(self):
+        source = self.workdir / "reference.png"
+        source.write_bytes(b"\\x89PNG\\r\\n\\x1a\\n" + b"invalid-encoded-content")
+        with patch("feature5_motion.runner.subprocess.Popen") as popen:
+            with self.assertRaises(MotionError):
+                self.runner.run(self.spec("poster"), source_file=source, workdir=self.workdir)
+            popen.assert_not_called()
+
+    def test_gpu_timeout_terminates_process_group(self):
+        proc = Mock(pid=4321)
+        proc.communicate.side_effect = [subprocess.TimeoutExpired(cmd="generate.py", timeout=30), (None, None)]
+        with patch("feature5_motion.runner.subprocess.Popen", return_value=proc), patch(
+            "feature5_motion.runner.os.killpg"
+        ) as kill:
+            with self.assertRaisesRegex(MotionError, "timeout"):
+                self.runner.run(self.spec(), source_file=None, workdir=self.workdir)
+            kill.assert_called_once()
+
+    def test_no_legal_context_blocks_before_any_gpu_call(self):
+        self.runner.license_policy = None
+        with patch("feature5_motion.runner.subprocess.Popen") as popen:
+            with self.assertRaisesRegex(MotionError, "license activation"):
+                self.runner.run(self.spec(), source_file=None, workdir=self.workdir)
+            popen.assert_not_called()
+
+    def test_missing_model_weight_lock_blocks_paid_gpu(self):
+        self.runner.artifact_lock = None
+        with patch("feature5_motion.runner.subprocess.Popen") as popen:
+            with self.assertRaisesRegex(MotionError, "weights manifest"):
+                self.runner.run(self.spec(), source_file=None, workdir=self.workdir)
+            popen.assert_not_called()
+
+    def test_rejected_model_manifest_blocks_gpu_before_cuda(self):
+        with patch.object(ArtifactLock, "verify", side_effect=MotionError("Unreviewed shard digest")):
+            with patch("feature5_motion.runner.subprocess.Popen") as popen:
+                with self.assertRaisesRegex(MotionError, "shard digest"):
+                    self.runner.run(self.spec(), source_file=None, workdir=self.workdir)
+                popen.assert_not_called()
+
+    def test_unsupported_cuda_hardware_cannot_launch(self):
+        with patch.object(self.runner, "_require_supported_gpu",
+                          side_effect=MotionError("Approved CUDA BF16 GPU is unavailable")):
+            with patch("feature5_motion.runner.subprocess.Popen") as popen:
+                with self.assertRaisesRegex(MotionError, "BF16"):
+                    self.runner.run(self.spec(), source_file=None, workdir=self.workdir)
+                popen.assert_not_called()
+
+    def test_reject_output_overwrite_before_launch(self):
+        (self.workdir / "motion.mp4").write_bytes(b"already generated")
+        with patch("feature5_motion.runner.subprocess.Popen") as popen:
+            with self.assertRaises(MotionError):
+                self.runner.run(self.spec(), source_file=None, workdir=self.workdir)
+            popen.assert_not_called()
+
+
+class TestOfficialScriptPin(unittest.TestCase):
+    def test_git_blob_header_uses_single_nul_and_content_bytes(self):
+        from hashlib import sha1
+        with tempfile.TemporaryDirectory() as directory:
+            source = Path(directory) / "generate.py"
+            source.write_bytes(b"print('ok')\n")
+            blob = b"blob 12\0" + b"print('ok')\n"
+            self.assertEqual(git_blob_sha1(source), sha1(blob).hexdigest())
+            self.assertNotEqual(git_blob_sha1(source), OFFICIAL_GENERATE_BLOB)
+
+    def test_unpinned_or_tampered_source_rejected_before_gpu(self):
+        with tempfile.TemporaryDirectory() as directory:
+            script = Path(directory) / "generate.py"
+            script.write_text("# untrusted test fixture, never execute\\n")
+            with self.assertRaisesRegex(MotionError, "not pinned Tencent source"):
+                verify_official_script(script)
+            script.write_text("# tampered with arbitrary bytes\\n")
+            with self.assertRaises(MotionError):
+                verify_official_script(script)
+
+    def test_symlinked_runtime_entrypoint_denied(self):
+        with tempfile.TemporaryDirectory() as directory:
+            folder = Path(directory)
+            target = folder / "target.py"
+            target.write_text("# fixture")
+            link = folder / "generate.py"
+            link.symlink_to(target)
+            with self.assertRaisesRegex(MotionError, "Untrusted local model script"):
+                verify_official_script(link)
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

## tests/gpu/test_feature5_local_acceptance.py

~~~~diff
@@ -0,0 +1,153 @@
+"""Optional genuine HunyuanVideo 1.5 local GPU acceptance: MANUAL ONLY.
+
+No model downloads, provisioning or CI auto-execution. Requires explicit operator
+flags for paid compute, licensing, an installed pinned checkout and local weights.
+Passing ffprobe DOES NOT establish human/garment/likeness quality approval.
+"""
+from pathlib import Path
+import os
+import json
+from decimal import Decimal, InvalidOperation
+import shutil
+import sys
+import tempfile
+import unittest
+from uuid import uuid4
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT))
+from feature5_motion import MotionSpec, validate_clip
+from feature5_motion.runner import HunyuanLocalRunner
+from feature5_motion.license_gate import HunyuanLicensePolicy
+from feature5_motion.artifact_lock import ArtifactLock
+from feature5_motion.acceptance import export_pending_review
+from feature5_motion.azure_pricing import extract_rates, MotionSpendGuard
+from feature5_motion.demo_fashion import fashion_motion_spec
+
+APPROVED = (
+    os.environ.get("RETAIL_FEATURE5_REAL_GPU_TEST", "").lower() == "true"
+    and os.environ.get("RETAIL_FEATURE5_GPU_COST_APPROVED", "").lower() == "true"
+    and os.environ.get("RETAIL_FEATURE5_LICENSE_APPROVED", "").lower() == "true"
+    and bool(os.environ.get("RETAIL_FEATURE5_PINNED_CHECKOUT"))
+    and bool(os.environ.get("RETAIL_FEATURE5_PINNED_WEIGHTS"))
+    and os.environ.get("RETAIL_FEATURE5_TENCENT_TERMS_REVIEWED") == "true"
+    and bool(os.environ.get("RETAIL_FEATURE5_PROVIDER_LEGAL_NAME"))
+    and bool(os.environ.get("RETAIL_FEATURE5_PUBLICATION_COUNTRIES"))
+    and bool(os.environ.get("RETAIL_FEATURE5_ARTIFACT_LOCK_PATH"))
+    and bool(os.environ.get("RETAIL_FEATURE5_APPROVED_LOCK_SHA256"))
+    and bool(os.environ.get("RETAIL_FEATURE5_MANUAL_EVIDENCE_ROOT"))
+    and os.environ.get("RETAIL_FEATURE5_ACCEPTANCE_MODE") in ("text", "image")
+    and bool(os.environ.get("RETAIL_FEATURE5_AZURE_PRICE_SNAPSHOT"))
+    and bool(os.environ.get("RETAIL_FEATURE5_MAX_TOTAL_GPU_USD"))
+    and bool(os.environ.get("RETAIL_FEATURE5_MAX_BILLABLE_SECONDS"))
+)
+
+
+@unittest.skipUnless(APPROVED, "Real licensed GPU inference was not explicitly authorized")
+class TestHunyuanLocalGPU(unittest.TestCase):
+    def setUp(self):
+        self.temp = tempfile.TemporaryDirectory(prefix="feature5-real-gpu-")
+        self.addCleanup(self.temp.cleanup)
+        self.folder = Path(self.temp.name)
+        self.evidence_root = Path(os.environ["RETAIL_FEATURE5_MANUAL_EVIDENCE_ROOT"])
+        if (self.evidence_root.is_symlink() or not self.evidence_root.resolve(strict=True).is_dir()
+            or self.evidence_root.stat().st_mode & 0o077):
+            self.fail("Real GPU evidence directory must be existing, private mode 0700")
+        # Requires operator-reviewed country, actual legal provider name,
+        # notices and rights in addition to owner spend consent.
+        # Env flags are not a substitute for genuine legal verification.
+        countries = tuple(
+            code.strip() for code in os.environ["RETAIL_FEATURE5_PUBLICATION_COUNTRIES"].split(",")
+        )
+        policy = HunyuanLicensePolicy(
+            deployment_country=os.environ.get("RETAIL_FEATURE5_DEPLOYMENT_COUNTRY", ""),
+            retailer_country=os.environ.get("RETAIL_FEATURE5_RETAILER_COUNTRY", ""),
+            intended_publication_countries=countries,
+            actual_provider_legal_name=os.environ["RETAIL_FEATURE5_PROVIDER_LEGAL_NAME"],
+            tencent_no_endorsement_notice=True,
+            full_license_terms_available_to_users=True,
+            acceptable_use_and_local_law_checked=True,
+            commercial_media_rights_checked=True,
+            operator_terms_reviewed=True,
+            monthly_active_users_at_model_release=int(os.environ.get("RETAIL_FEATURE5_RELEASE_MAU", "-1")),
+            separate_tencent_license_if_required=os.environ.get("RETAIL_FEATURE5_EXTRA_TENCENT_LICENSE") == "true",
+        )
+        policy.assert_allowed()
+        # One and only one optional paid inference: do not run both T2V
+        # and I2V from a single unittest discover invocation. Check a
+        # verified Azure retail snapshot and preauthorized overall cost cap
+        # BEFORE either GPU or model-weight preflight.
+        try:
+            snapshot = Path(os.environ["RETAIL_FEATURE5_AZURE_PRICE_SNAPSHOT"])
+            if snapshot.is_symlink() or not snapshot.is_file() or snapshot.stat().st_size > 1_000_000:
+                self.fail("Reviewed Azure price snapshot required")
+            region = os.environ.get("RETAIL_FEATURE5_GPU_REGION", "")
+            rate = extract_rates(json.loads(snapshot.read_text()), region=region, gpu="A100")
+            seconds = int(os.environ["RETAIL_FEATURE5_MAX_BILLABLE_SECONDS"])
+            self.guard = MotionSpendGuard(
+                rate, max_billable_seconds=seconds,
+                vcpus=int(os.environ.get("RETAIL_FEATURE5_GPU_VCPUS", "4")),
+                gib_memory=int(os.environ.get("RETAIL_FEATURE5_GPU_MEMORY_GIB", "16")),
+                ancillary_allowance_usd=Decimal(os.environ.get("RETAIL_FEATURE5_ANCILLARY_USD", "0.05")),
+            )
+            quoted = self.guard.minimum_reservation_usd()
+            approved_cap = Decimal(os.environ["RETAIL_FEATURE5_MAX_TOTAL_GPU_USD"])
+            if not approved_cap.is_finite() or approved_cap <= 0 or quoted > approved_cap:
+                self.fail("One-shot GPU maximum quote exceeds operator-approved USD cap")
+        except (ValueError, TypeError, InvalidOperation, KeyError, OSError) as exc:
+            self.fail("Reviewed GPU pricing inputs invalid: " + type(exc).__name__)
+        self.runner = HunyuanLocalRunner(
+            checkout=Path(os.environ["RETAIL_FEATURE5_PINNED_CHECKOUT"]),
+            weights=Path(os.environ["RETAIL_FEATURE5_PINNED_WEIGHTS"]),
+            enabled=True, license_approved=True,
+            gpu_budget_approved=True, timeout_seconds=seconds,
+            license_policy=policy,
+            artifact_lock=ArtifactLock(
+                Path(os.environ["RETAIL_FEATURE5_ARTIFACT_LOCK_PATH"]),
+                os.environ["RETAIL_FEATURE5_APPROVED_LOCK_SHA256"],
+            ),
+        )
+
+    @unittest.skipUnless(os.environ.get("RETAIL_FEATURE5_ACCEPTANCE_MODE") == "text",
+                         "One-shot GPU demo explicitly selected image instead of text")
+    def test_text_to_video_real_gpu(self):
+        spec = fashion_motion_spec(job_id=str(uuid4()), shop_id=str(uuid4()))
+        out = self.runner.run(spec, source_file=None, workdir=self.folder)
+        metadata = validate_clip(out)
+        self.assertEqual(metadata["codec"], "h264")
+        self.assertTrue(4.5 <= metadata["duration_seconds"] <= 5.5)
+        # Preserve the actual clip + six-frame human reviewer materials OUTSIDE
+        # the temporary job directory, never automatically approve visual QA.
+        exported = export_pending_review(
+            out, self.evidence_root / ("t2v-" + str(uuid4())),
+            mode="text",
+            approved_model_manifest_sha256=os.environ["RETAIL_FEATURE5_APPROVED_LOCK_SHA256"],
+        )
+        self.assertEqual(exported["status"], "PENDING_HUMAN_REVIEW")
+
+    @unittest.skipUnless(
+        os.environ.get("RETAIL_FEATURE5_ACCEPTANCE_MODE") == "image"
+        and os.environ.get("RETAIL_FEATURE5_RIGHTS_APPROVED_IMAGE"),
+        "Image mode not explicitly selected with licensed image",
+    )
+    def test_image_to_video_real_gpu(self):
+        source = Path(os.environ["RETAIL_FEATURE5_RIGHTS_APPROVED_IMAGE"])
+        if not source.is_file() or source.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
+            self.fail("Authorized local image path is not a readable image")
+        original = self.folder / ("source" + source.suffix.lower())
+        shutil.copyfile(source, original)
+        spec = MotionSpec(job_id=str(uuid4()), shop_id=str(uuid4()),
+                          prompt="Adult fashion model walking slowly, preserving garment details",
+                          mode="image", source_asset_id=str(uuid4()))
+        out = self.runner.run(spec, source_file=original, workdir=self.folder)
+        self.assertEqual(validate_clip(out)["codec"], "h264")
+        exported = export_pending_review(
+            out, self.evidence_root / ("i2v-" + str(uuid4())),
+            mode="image", source_image=original,
+            approved_model_manifest_sha256=os.environ["RETAIL_FEATURE5_APPROVED_LOCK_SHA256"],
+        )
+        self.assertEqual(exported["status"], "PENDING_HUMAN_REVIEW")
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

