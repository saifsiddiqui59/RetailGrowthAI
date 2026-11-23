#!/usr/bin/env python3
"""Offline import/index acceptance of the EXACT SHA-verified F4 native worker ZIP.

This runs no Azure queue, Supabase network, billing, rendering or production
function: imports the worker module in a separate Python -S process with only
packaged dependencies, first OFF (0 functions), then ON (exactly 3 private).
Never use customer tokens or service-role credentials in this test.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from verify_feature4_cpu_release import ReleaseIntegrityError, verify_release

EXPECTED = (
    "feature4_cpu_dispatch_timer",
    "feature4_cpu_poison_message",
    "feature4_cpu_render_message",
)

class ProbeFailed(ValueError):
    pass


def _program(enabled: bool) -> str:
    expected = list(EXPECTED) if enabled else []
    return (
        "import function_app\n"
        + "actual = sorted(fn.get_function_name() for fn in "
        "function_app.app.get_functions())\n"
        + "assert actual == " + repr(expected) + ", 'unapproved function index'\n"
    )


def probe(path: Path) -> None:
    if sys.version_info[:2] != (3, 11):
        raise ProbeFailed("Python 3.11 is required for sealed F4 indexing")
    # verify_release validates all paths, inodes, member permissions and SHA256
    # before any extracted Python byte can execute.
    verify_release(path)
    with TemporaryDirectory(prefix="rgai-f4cpu-probe-") as directory:
        root = Path(directory)
        with ZipFile(path, "r") as archive:
            archive.extractall(root)
        packages = root / ".python_packages" / "lib" / "site-packages"
        if not packages.is_dir():
            raise ProbeFailed("Missing bundled Python runtime dependencies")
        for enabled in (False, True):
            # -S avoids venv and user site-packages; only ZIP payload imports.
            # Exclude all cloud credentials and service-specific environment
            # variables, even when this script runs on a protected DEV runner.
            env = {
                "PATH": os.environ.get("PATH", "/usr/bin"),
                "PYTHONPATH": os.pathsep.join((str(root), str(packages))),
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONNOUSERSITE": "1",
                "RETAIL_FEATURE4_CPU_WORKER_ENABLED": "true" if enabled else "false",
            }
            try:
                result = subprocess.run(
                    [sys.executable, "-S", "-c", _program(enabled)],
                    cwd=root, env=env, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, timeout=120, check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise ProbeFailed("Isolated packaged CPU worker index unavailable") from exc
            if result.returncode != 0:
                raise ProbeFailed("Sealed CPU function startup/index mismatch")
    print("PASS: sealed CPU ZIP independently indexed exactly 0 OFF / 3 ON functions")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, required=True)
    args = parser.parse_args()
    try:
        probe(args.zip)
    except (ProbeFailed, ReleaseIntegrityError, OSError, ValueError) as exc:
        # Fixed non-identifying failure category; no stderr/stdout secrets.
        print("BLOCKED: native F4 ZIP offline import/index validation failed",
              file=sys.stderr)
        raise SystemExit(3) from exc


if __name__ == "__main__":
    main()
