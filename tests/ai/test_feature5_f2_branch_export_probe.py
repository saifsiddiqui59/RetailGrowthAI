"""Feature5 original-F2 branch probe: synthetic subprocess doubles only.

These tests do NOT execute PR #551. The actual operator CLI must use the
reviewed pinned commit and real Node stdout before any original-source claim.
"""
from __future__ import annotations

import json
from pathlib import Path
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from feature5_motion.f2_branch_export_probe import (
    PINNED_F2_HEAD, REL_EXPORTER, DURATIONS,
    verify_separate_feature2_checkout, probe_original_feature2_branch, main,
)
from feature5_motion.wan22_motion_adapter import WanCompatibilityError
from test_feature5_feature2_storyboard_bridge import make_packet


class SyntheticOriginalBranchProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        exporter = self.root / REL_EXPORTER
        exporter.parent.mkdir(parents=True)
        exporter.write_text("// test-only fake; never a reviewed MIT exporter", encoding="utf-8")
        self.git_head = PINNED_F2_HEAD
        self.git_dirty = ""
        self.git_calls = []
        self.node_calls = []
        self.node_tamper = False
        self.node_dirty_after_duration = None

    def fake_subprocess(self, argv, **kwargs):
        if argv[0] == "git":
            self.git_calls.append(tuple(argv[3:]))
            query = tuple(argv[3:])
            if query == ("rev-parse", "--show-toplevel"):
                out = str(self.root) + "\n"
            elif query == ("rev-parse", "HEAD"):
                out = self.git_head + "\n"
            elif query == ("status", "--porcelain", "--untracked-files=all"):
                out = self.git_dirty
            elif query == ("ls-files", "--error-unmatch", "--", REL_EXPORTER.as_posix()):
                out = REL_EXPORTER.as_posix() + "\n"
            else:
                return CompletedProcess(argv, 1, stdout="", stderr="unrecognized fake Git")
            return CompletedProcess(argv, 0, stdout=out, stderr="")
        self.assertEqual(argv[0], "node")
        self.assertEqual(Path(argv[1]), self.root / REL_EXPORTER)
        self.assertEqual(kwargs["cwd"], str(self.root))
        self.assertNotIn("AZURE_STORAGE_ACCOUNT_KEY", kwargs["env"])
        self.assertNotIn("SUPABASE_SERVICE_ROLE_KEY", kwargs["env"])
        self.assertEqual(kwargs["env"]["RETAILGROWTH_GPU_ENABLED"], "false")
        duration = int(argv[2])
        self.node_calls.append(duration)
        if duration == self.node_dirty_after_duration:
            self.git_dirty = "?? ai-agents/creative-director/upstream/untracked-shadow.js\n"
        output = make_packet(duration)
        if self.node_tamper:
            output["review"]["signed_customer_approval"] = True
        return CompletedProcess(argv, 0, stdout=json.dumps(output).encode(), stderr=b"")

    def test_prepared_three_duration_probe_and_negative_mutations_do_not_grant_authority(self):
        with patch("feature5_motion.f2_branch_export_probe.subprocess.run",
                   side_effect=self.fake_subprocess):
            report = probe_original_feature2_branch(self.root)
        self.assertEqual(self.node_calls, list(DURATIONS))
        self.assertEqual(report["negative_tamper_cases_denied"], 7)
        self.assertEqual([x["segment_count"] for x in report["durations"]], [3, 6, 12])
        self.assertTrue(all(len(x["raw_original_stdout_sha256"]) == 64
                            for x in report["durations"]))
        self.assertEqual(report["feature2_original_git_commit"], PINNED_F2_HEAD)
        self.assertFalse(report["feature2_merged_to_main_proven"])
        self.assertFalse(report["licensed_media_approved"])
        self.assertFalse(report["production_model_output_proven"])
        self.assertFalse(report["can_submit_provider"])
        self.assertFalse(report["can_publish"])
        self.assertFalse(report["gpu_started"])
        self.assertIn("AWAITING_COORDINATOR_INTEGRATION", report["status"])

    def test_fail_closed_on_wrong_revision_dirty_tree_and_mismatched_git_root(self):
        cases = (
            ("other SHA", "0"*40, ""),
            ("dirty original file", PINNED_F2_HEAD, " M ai-agents/creative-director/director.js\n"),
            ("untracked module overlay", PINNED_F2_HEAD, "?? ai-agents/creative-director/upstream/evil.js\n"),
        )
        for name, sha, dirty in cases:
            with self.subTest(name=name):
                self.git_head = sha
                self.git_dirty = dirty
                self.node_calls.clear()
                with patch("feature5_motion.f2_branch_export_probe.subprocess.run",
                           side_effect=self.fake_subprocess), self.assertRaises(WanCompatibilityError):
                    verify_separate_feature2_checkout(self.root)
                self.assertEqual(self.node_calls, [])
        with self.assertRaises(WanCompatibilityError):
            verify_separate_feature2_checkout(self.root / "absent")
        (self.root / REL_EXPORTER).unlink()
        with self.assertRaises(WanCompatibilityError):
            verify_separate_feature2_checkout(self.root)

    def test_original_checkout_drift_during_node_is_denied_before_success(self):
        self.node_dirty_after_duration = 30
        with patch("feature5_motion.f2_branch_export_probe.subprocess.run",
                   side_effect=self.fake_subprocess), self.assertRaisesRegex(
                       WanCompatibilityError, "untracked"):
            probe_original_feature2_branch(self.root)
        self.assertEqual(self.node_calls, [15, 30])
        self.assertIn(
            ("status", "--porcelain", "--untracked-files=all"), self.git_calls
        )

    def test_clean_original_is_rechecked_after_each_duration_and_at_report(self):
        with patch("feature5_motion.f2_branch_export_probe.subprocess.run",
                   side_effect=self.fake_subprocess):
            probe_original_feature2_branch(self.root)
        status_checks = [
            args for args in self.git_calls if args ==
            ("status", "--porcelain", "--untracked-files=all")
        ]
        # One initial check, three after Node and one final before receipt.
        self.assertEqual(len(status_checks), 5)

    def test_invalid_original_stdout_never_yields_partial_success(self):
        self.node_tamper = True
        with patch("feature5_motion.f2_branch_export_probe.subprocess.run",
                   side_effect=self.fake_subprocess), self.assertRaises(WanCompatibilityError):
            probe_original_feature2_branch(self.root)
        self.assertEqual(self.node_calls, [15])

    def test_cli_denial_has_no_success_json_or_traceback(self):
        self.git_head = "a"*40
        with patch("feature5_motion.f2_branch_export_probe.subprocess.run",
                   side_effect=self.fake_subprocess), patch(
                   "feature5_motion.f2_branch_export_probe.argparse.ArgumentParser.exit",
                   side_effect=SystemExit(2)), self.assertRaises(SystemExit):
            main(["--feature2-root", str(self.root)])
        self.assertEqual(self.node_calls, [])


if __name__ == "__main__":
    unittest.main()
