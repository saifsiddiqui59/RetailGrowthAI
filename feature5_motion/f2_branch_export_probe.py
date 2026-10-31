"""CPU-only probe of the ORIGINAL Feature2 Director exporter in a separate worktree.

This does not copy any Feature2 code, change branches, run AI inference, publish
media, grant rights or upgrade the 22-task F5 release ledger. Operator must
supply a local clean checkout at the reviewed exact Feature2 PR #551 SHA.
Neither the source fixture nor this proof grants customer/media approval.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

from .verify_feature2_export import MAX_INPUT_BYTES, qualify_export_bytes
from .wan22_motion_adapter import WanCompatibilityError

PINNED_F2_HEAD = "d80d6b50705323290c4b214bf2f006eacef1ef33"
REL_EXPORTER = Path("ai-agents/creative-director/export-feature4-feature5-fixture.js")
DURATIONS = (15, 30, 60)
REPORT_SCHEMA = "retailgrowth.feature5-f2-original-branch-probe.v1"


def _git(root: Path, *args: str) -> str:
    try:
        output = subprocess.run(
            ["git", "-C", str(root), *args], check=False,
            capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise WanCompatibilityError("Original Feature2 git provenance unavailable") from exc
    if output.returncode != 0 or type(output.stdout) is not str:
        raise WanCompatibilityError("Original Feature2 git provenance unavailable")
    return output.stdout.strip()


def verify_separate_feature2_checkout(path: str | Path) -> Path:
    """No fetch, checkout, branch mutation or untrusted preview fallback."""
    try:
        root = Path(path).resolve(strict=True)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise WanCompatibilityError("Original Feature2 separate checkout missing") from exc
    if not root.is_dir() or not (root / REL_EXPORTER).is_file():
        raise WanCompatibilityError("Original Feature2 exporter not present")
    if Path(_git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise WanCompatibilityError("Feature2 path must be the git checkout root")
    if _git(root, "rev-parse", "HEAD") != PINNED_F2_HEAD:
        raise WanCompatibilityError("Unverified Feature2 original exporter revision")
    # A clean pinned commit is essential: test code must not attest an edited
    # producer or an uncommitted poisoned dependency as the original exporter.
    # Untracked files can shadow a Node module or test fixture even while all
    # tracked files match HEAD. Require a fully clean, untracked-free worktree.
    if _git(root, "status", "--porcelain", "--untracked-files=all"):
        raise WanCompatibilityError("Modified or untracked Feature2 source cannot establish original provenance")
    if _git(root, "ls-files", "--error-unmatch", "--", REL_EXPORTER.as_posix()) != REL_EXPORTER.as_posix():
        raise WanCompatibilityError("Feature2 exporter is not a pinned tracked original")
    return root


def _original_output(root: Path, duration: int) -> bytes:
    # The reviewed original Node CLI uses only pinned MIT Director logic and
    # author-provided SYNTHETIC fixtures. It must never inherit cloud secrets.
    env = {"PATH": os.environ.get("PATH", ""), "NODE_ENV": "test",
           "RETAILGROWTH_GPU_ENABLED": "false"}
    try:
        result = subprocess.run(
            ["node", str(root / REL_EXPORTER), str(duration)],
            cwd=str(root), env=env, capture_output=True, check=False,
            timeout=45,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise WanCompatibilityError("Original Feature2 Node exporter unavailable") from exc
    if (result.returncode != 0 or type(result.stdout) is not bytes
            or not 0 < len(result.stdout) <= MAX_INPUT_BYTES):
        raise WanCompatibilityError("Original Feature2 Node export failed or exceeded limit")
    return result.stdout


def probe_original_feature2_branch(path: str | Path) -> dict:
    """Run original 15/30/60 source then explicit F5 fail-closed mutations.

    This is intentionally an unmerged *source* exercise. The output schema
    refuses real model or publish authority, even when all tests pass.
    """
    root = verify_separate_feature2_checkout(path)
    durations = []
    mutations_checked = 0
    for duration in DURATIONS:
        original = _original_output(root, duration)
        # The exporter can change tracked/untracked files while Node executes.
        # Never attest stdout against a source tree that ceased to match HEAD.
        verify_separate_feature2_checkout(root)
        proof = qualify_export_bytes(original, duration=duration)
        if (proof["duration_seconds"] != duration
                or proof["segment_count"] != duration // 5
                or proof["can_submit_provider"] is not False
                or proof["can_publish"] is not False
                or proof["approved_for_feature4"] is not False):
            raise WanCompatibilityError("Original Feature2 exporter is not a safe motion source")
        durations.append({
            "duration_seconds": duration, "segment_count": proof["segment_count"],
            "raw_original_stdout_sha256": sha256(original).hexdigest(),
            "qualified_source_packet_sha256": proof["original_packet_sha256"],
            "can_submit_provider": False, "can_publish": False,
        })
        if duration == 30:
            # Alter semantic identity and approvals WITHOUT changing the
            # Node exporter. Every changed original must fail F5 validation.
            try:
                packet = json.loads(original.decode("utf-8"))
                cases = (
                    lambda p: p["feature5"]["clip_requests"][1]["original_direction"].update(
                        next_shot_id="SPLICED"),
                    lambda p: p["feature5"]["clip_requests"][1]["original_direction"].update(
                        reference_facts_sha256="f" * 64),
                    lambda p: p["feature5"]["clip_requests"][1]["original_direction"].update(
                        product_sku="OTHER_RETAILER_SKU"),
                    lambda p: p["feature4"]["timeline"][1].update(
                        immutable_motion_prompt_sha256="e" * 64),
                    lambda p: p["review"].update(signed_customer_approval=True),
                    lambda p: p["feature5"].update(can_run_paid_motion=True),
                    lambda p: p["source_media"].update(approved_feature3_frame_present=True),
                )
            except (UnicodeError, ValueError, TypeError, KeyError, IndexError) as exc:
                raise WanCompatibilityError("Original Feature2 export unsuitable for tamper testing") from exc
            for change in cases:
                tampered = deepcopy(packet)
                try:
                    change(tampered)
                    modified = json.dumps(tampered, separators=(",", ":"), allow_nan=False).encode()
                    qualify_export_bytes(modified, duration=duration)
                except WanCompatibilityError:
                    mutations_checked += 1
                except (ValueError, TypeError, KeyError, IndexError) as exc:
                    raise WanCompatibilityError("Feature2 tamper test could not execute") from exc
                else:
                    raise WanCompatibilityError("Tampered original Feature2 source was accepted")
    if len(durations) != 3 or mutations_checked != 7:
        raise WanCompatibilityError("Original Feature2 branch coverage incomplete")
    # Check a last time after all mutations and before returning a report.
    verify_separate_feature2_checkout(root)
    return {
        "schema": REPORT_SCHEMA,
        "feature2_original_git_commit": PINNED_F2_HEAD,
        "original_source_branch_checked": True,
        "durations": durations,
        "negative_tamper_cases_denied": mutations_checked,
        "status": "ORIGINAL_OFFLINE_BRANCH_ONLY_AWAITING_COORDINATOR_INTEGRATION",
        "feature2_merged_to_main_proven": False,
        "licensed_media_approved": False,
        "production_model_output_proven": False,
        "can_submit_provider": False,
        "can_publish": False,
        "gpu_started": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="GPU-OFF original Feature2 #551 worktree export check, no cloud")
    parser.add_argument("--feature2-root", required=True,
                        help="Existing clean local checkout at the exact reviewed PR #551 SHA")
    args = parser.parse_args(argv)
    try:
        report = probe_original_feature2_branch(args.feature2_root)
    except WanCompatibilityError:
        parser.exit(2, "Original Feature2 source probe DENIED; no AI/GPU or approvals.\n")
    print(json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
