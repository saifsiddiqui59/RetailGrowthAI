"""Feature5 real-CPU native media test runner for existing FFmpeg CI job.

Deliberately FAILS rather than skips if FFmpeg, ffprobe, Pillow or any of
the four required F5 tests are unavailable. No GPU, ComfyUI, cloud, model
download, Azure, hosted Postgres, or customer media operations occur here.

Coordinator-owned FFmpeg workflow (already has FFmpeg + Pillow) can run:
  python3 -m feature5_motion.ci_native_media
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

REQUIRED_TEST_MODULE = "test_feature5_wan22_real_cpu_private_intake.py"
REQUIRED_TEST_METHODS = frozenset({
    "test_real_nonstatic_native_mp4_is_only_pending_not_ai_or_approved",
    "test_real_static_native_mp4_is_rejected_by_motion_screening",
    "test_real_native_shaped_mp4_with_audio_is_denied_before_screening",
    "test_real_single_flash_only_is_rejected_not_motion",
})
ROOT = Path(__file__).resolve().parents[1]


def _test_names(suite):
    names = []
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            names.extend(_test_names(item))
        else:
            names.append(item._testMethodName)
    return names


def validate_media_environment(*, find_executable=shutil.which, python=sys.executable):
    """Require actual decoding tools; never substitute mock FFmpeg for success."""
    for executable in ("ffmpeg", "ffprobe"):
        resolved = find_executable(executable)
        if not resolved or not os.path.isabs(resolved):
            raise RuntimeError("Required native media executable unavailable: " + executable)
        try:
            version = subprocess.run(
                [resolved, "-version"], capture_output=True,
                check=False, timeout=10,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise RuntimeError("Native media executable cannot run: " + executable) from exc
        if version.returncode or not version.stdout.startswith(
            executable.encode("ascii") + b" version "
        ):
            raise RuntimeError("Native media executable failed version check: " + executable)
    try:
        import PIL.Image  # noqa: F401; required by real frame-screening implementation
    except ImportError as exc:
        raise RuntimeError("Pillow is required by native media frame screening") from exc
    return True


def run_cpu_media_suite(*, stream=None):
    """Actual unittest execution, exactly four required tests, zero skips."""
    validate_media_environment()
    tests_dir = ROOT / "tests" / "ai"
    if not tests_dir.is_dir() or not (tests_dir / REQUIRED_TEST_MODULE).is_file():
        raise RuntimeError("Required original Feature5 native media tests missing")
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=str(tests_dir), pattern=REQUIRED_TEST_MODULE,
        top_level_dir=str(tests_dir),
    )
    names = _test_names(suite)
    if len(names) != 4 or set(names) != REQUIRED_TEST_METHODS:
        raise RuntimeError("Unexpected or incomplete native media acceptance tests")
    result = unittest.TextTestRunner(
        stream=stream or sys.stderr,
        verbosity=2,
        failfast=False,
    ).run(suite)
    if (result.testsRun != 4 or not result.wasSuccessful() or result.skipped or
        result.expectedFailures or result.unexpectedSuccesses):
        raise RuntimeError(
            "Native CPU media CI gate DENIED: all four tests must actually PASS; "
            "failed or skipped media is not acceptance"
        )
    return result.testsRun


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="GPU-off native MP4 acceptance gate: actual FFmpeg, 4 tests, zero skips")
    parser.parse_args(argv)
    try:
        count = run_cpu_media_suite()
    except (RuntimeError, OSError, ImportError, unittest.SkipTest) as exc:
        print("Feature5 real native-CPU media CI gate FAILED: " + str(exc), file=sys.stderr)
        return 2
    print(
        f"Feature5 real native-CPU media CI gate PASS: {count}/4 actual "
        "FFmpeg/ffprobe private-intake tests; 0 skipped; "
        "NOT genuine Wan inference or signed human approval"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
