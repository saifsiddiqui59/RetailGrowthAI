"""Offline contract tests for Feature5's fail-on-skip real-FFmpeg CI runner.

These are MOCK UNIT TESTS of the runner; only explicitly invoking the
ci_native_media module with installed FFmpeg executes actual MP4 acceptance.
"""
from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from feature5_motion import ci_native_media


class NativeMediaRunnerContracts(unittest.TestCase):
    def test_discovers_exact_three_acceptance_test_methods(self):
        suite = unittest.TestLoader().discover(
            start_dir=str(ci_native_media.ROOT / "tests" / "ai"),
            pattern=ci_native_media.REQUIRED_TEST_MODULE,
            top_level_dir=str(ci_native_media.ROOT / "tests" / "ai"),
        )
        names = ci_native_media._test_names(suite)
        self.assertEqual(len(names), 4)
        self.assertEqual(set(names), ci_native_media.REQUIRED_TEST_METHODS)

    def test_missing_ffmpeg_must_fail_instead_of_skip(self):
        with self.assertRaisesRegex(RuntimeError, "ffmpeg"):
            ci_native_media.validate_media_environment(find_executable=lambda _: None)
        with patch("feature5_motion.ci_native_media.validate_media_environment",
                   side_effect=RuntimeError("ffprobe unavailable")):
            self.assertEqual(ci_native_media.main([]), 2)

    def test_success_requires_four_executed_and_no_skips(self):
        def completed(*, tests_run=4, skipped=None, successful=True,
                      expected_failures=None, unexpected_successes=None):
            return SimpleNamespace(
                testsRun=tests_run, skipped=skipped or [],
                expectedFailures=expected_failures or [],
                unexpectedSuccesses=unexpected_successes or [],
                wasSuccessful=lambda: successful,
            )
        # No encoding here: only checks that the runner correctly rejects
        # misleading pass/skip/xfail summaries.
        with patch("feature5_motion.ci_native_media.validate_media_environment",
                   return_value=True):
            with patch("feature5_motion.ci_native_media.unittest.TextTestRunner") as runner:
                runner.return_value.run.return_value = completed()
                self.assertEqual(ci_native_media.run_cpu_media_suite(), 4)
                for invalid in (
                    completed(tests_run=3),
                    completed(skipped=[("test", "ffmpeg absent")]),
                    completed(successful=False),
                    completed(expected_failures=[("test", "expected failure")]),
                    completed(unexpected_successes=[("test",)]),
                ):
                    runner.return_value.run.return_value = invalid
                    with self.subTest(invalid=invalid), self.assertRaisesRegex(
                            RuntimeError, "DENIED"):
                        ci_native_media.run_cpu_media_suite()

    def test_entrypoint_never_claims_source_only_green_as_model_inference(self):
        with patch("feature5_motion.ci_native_media.run_cpu_media_suite", return_value=4):
            self.assertEqual(ci_native_media.main([]), 0)


if __name__ == "__main__":
    unittest.main()
