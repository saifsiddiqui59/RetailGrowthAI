#!/usr/bin/env python3
"""Offline release/rollback artifact gate. Never uploads or changes cloud resources.

Both artifacts MUST be reviewed Functions ZIPs; a first release needs a distinct,
explicit approval. Fingerprints are printed without exposing config or secret data.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path

PACKAGE = Path(__file__).with_name("package.py")


def verify_pair(candidate: Path, previous: Path | None, first_release: bool) -> tuple[str, str | None]:
    if first_release == bool(previous):
        raise ValueError("Provide EITHER explicitly approved first release OR a previous validated ZIP")
    spec = importlib.util.spec_from_file_location("rgai_release_package", PACKAGE)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    mod.verify_zip(candidate)
    candidate_digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    previous_digest = None
    if previous is not None:
        if candidate.resolve() == previous.resolve():
            raise ValueError("Rollback ZIP must be a separately retained known-good release")
        mod.verify_zip(previous)
        previous_digest = hashlib.sha256(previous.read_bytes()).hexdigest()
        if previous_digest == candidate_digest:
            raise ValueError("Candidate and rollback ZIP must represent different releases")
    return candidate_digest, previous_digest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--previous", type=Path)
    group.add_argument("--first-release-approved", action="store_true")
    args = parser.parse_args()
    try:
        digest, prior = verify_pair(args.candidate, args.previous, args.first_release_approved)
    except (OSError, ValueError, AssertionError) as exc:
        print("BLOCKED: invalid deployment/rollback artifact:", exc)
        return 3
    print("VALID candidate SHA256:", digest)
    if prior:
        print("VALID retained rollback SHA256:", prior)
    else:
        print("FIRST RELEASE: no previous application ZIP; database rollback is NOT automatic")
    print("NO DEPLOYMENT performed. Confirm backup, app settings and IAM separately.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
