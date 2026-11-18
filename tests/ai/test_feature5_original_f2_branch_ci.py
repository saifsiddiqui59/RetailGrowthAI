"""Run ACTUAL pinned Feature2 #551 Node source in Feature5 branch CI, GPU OFF.

This is an explicitly bounded read-only fetch of a reviewed commit from this
same public repository, NOT a copied implementation, mocked stdout, or merge.
Outside GitHub Actions' Feature5 branch CI this test does not use the network.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest

from feature5_motion.f2_branch_export_probe import (
    DURATIONS, PINNED_F2_HEAD, REPORT_SCHEMA, probe_original_feature2_branch,
)

REVIEWED_SOURCE = "https://github.com/saifsiddiqui59/RetailGrowthAI.git"
SOURCE_REF = "refs/pull/551/head"
ORIGINAL_CHECK_ENABLED = (
    os.environ.get("GITHUB_ACTIONS") == "true"
    and os.environ.get("GITHUB_REF", "").startswith(
        "refs/heads/feat/feature5-")
)


@unittest.skipUnless(
    ORIGINAL_CHECK_ENABLED,
    "Original F2 source read-only fetch is scoped to Feature5 branch CI only",
)
class OriginalFeature2BranchSourceCITests(unittest.TestCase):
    def test_actual_pinned_f2_node_15_30_60_and_negative_tamper(self):
        self.assertIsNotNone(shutil.which("git"),
                             "Exact reviewed original source requires Git")
        self.assertIsNotNone(shutil.which("node"),
                             "Actual original MIT Creative Director requires Node")
        with TemporaryDirectory(prefix="rgai-f5-real-f2-") as td:
            source=Path(td)
            # Fetch PR #551's current advertised source only; never fetch
            # remote branches by an operator-controlled name or alter this
            # Feature5 CI checkout. The next check pins its ACTUAL SHA.
            operations = (
                (["git", "init", "--quiet", str(source)], 20),
                (["git", "-C", str(source), "fetch", "--no-tags",
                  "--depth=1", "--quiet", REVIEWED_SOURCE, SOURCE_REF], 120),
                (["git", "-C", str(source), "checkout", "--detach",
                  "--quiet", "FETCH_HEAD"], 30),
            )
            for args, limit in operations:
                result=subprocess.run(
                    args, capture_output=True, check=False,
                    timeout=limit,
                )
                self.assertEqual(
                    result.returncode, 0,
                    "Read-only original F2 checkout failed at " +
                    args[2 if args[1] == "-C" else 1] +
                    "; cannot claim actual producer evidence",
                )
            head=subprocess.run(
                ["git", "-C", str(source), "rev-parse", "HEAD"],
                capture_output=True, text=True, check=True, timeout=15,
            ).stdout.strip()
            self.assertEqual(
                head, PINNED_F2_HEAD,
                "Feature2 PR #551 advanced: review/pin its new original SHA "
                "before accepting cross-feature integration",
            )
            # Existing F5 source probe executes ORIGINAL unmodified Node
            # module and pinned synthetic fixtures at all 3 durations.
            # The seven tamper tests must all be denied by the real F5 gate.
            proof=probe_original_feature2_branch(source)
            self.assertEqual(proof["schema"], REPORT_SCHEMA)
            self.assertEqual(proof["feature2_original_git_commit"], head)
            self.assertEqual(
                [row["duration_seconds"] for row in proof["durations"]],
                list(DURATIONS),
            )
            self.assertEqual(
                [row["segment_count"] for row in proof["durations"]],
                [3, 6, 12],
            )
            self.assertEqual(proof["negative_tamper_cases_denied"], 7)
            self.assertTrue(proof["original_source_branch_checked"])
            for field in (
                "feature2_merged_to_main_proven",
                "licensed_media_approved",
                "production_model_output_proven",
                "can_submit_provider", "can_publish", "gpu_started",
            ):
                self.assertIs(proof[field], False, field)
            self.assertEqual(
                proof["status"],
                "ORIGINAL_OFFLINE_BRANCH_ONLY_AWAITING_COORDINATOR_INTEGRATION",
            )
            self.assertTrue(all(
                len(row["raw_original_stdout_sha256"]) == 64
                and len(row["qualified_source_packet_sha256"]) == 64
                for row in proof["durations"]
            ))
            # GitHub step summary documents exact original-byte verification
            # for the coordinator. No copyrighted scripts/media/prompt text,
            # provider credentials or private customer records are emitted.
            summary=os.environ.get("GITHUB_STEP_SUMMARY")
            if summary:
                with open(summary, "a", encoding="utf-8") as stream:
                    stream.write(
                        "\n### Feature5 original Feature2 #551 source check (GPU OFF)\n"
                        f"- Reviewed exact original commit: `{head}`\n"
                        "- Actual Node durations: 15, 30, 60 seconds\n"
                        "- Original SHA/segment proofs:\n"
                    )
                    for row in proof["durations"]:
                        stream.write(
                            f"  - {row['duration_seconds']} s: "
                            f"{row['segment_count']} segments, stdout SHA256 "
                            f"`{row['raw_original_stdout_sha256']}`\n"
                        )
                    stream.write(
                        "- Seven independently tampered packets denied; "
                        "**no inference, media approval or release authority**.\n"
                        "- F5-02 source CI pass does not merge Feature2/F5.\n"
                    )


if __name__ == "__main__":
    unittest.main()
