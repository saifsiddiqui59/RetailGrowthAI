#!/usr/bin/env python3
"""F4-12: fail closed if npm resolves a different HyperFrames dependency tree.

GitHub Actions produced the exact reviewed npm v3 lockfile from producer 0.8.185.
This lock is now committed in the Feature4 branch and verified byte-for-byte
BEFORE npm ci installs package scripts. This is not commercial license clearance,
Azure runtime packaging or media quality proof.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse

PINNED_SHA256 = "2b4016fde9514ac2771660a3a1e81389ee3b1237c72db6acfa1fc540494948a6"
PRODUCER_VERSION = "0.8.185"
PUPPETEER_VERSION = "25.16.0"
LOCK_PACKAGES = 138
ALLOWED_REGISTRY = "registry.npmjs.org"
BASE_DIRECTORY = "node_modules/"
SRI = re.compile(r"^(?:sha512|sha384|sha256)-[a-zA-Z0-9+/=]+$")


class DependencyLockError(ValueError):
    pass


def verify_lock(path):
    lock_path = Path(path)
    raw = lock_path.read_bytes()
    if not 1024 <= len(raw) <= 200_000:
        raise DependencyLockError("Unexpected npm lockfile size")
    sha = hashlib.sha256(raw).hexdigest()
    if sha != PINNED_SHA256:
        raise DependencyLockError("Dependency graph drifted from previously audited SHA256")
    try:
        lock = json.loads(raw)
    except (UnicodeError, ValueError) as exc:
        raise DependencyLockError("Invalid npm lockfile JSON") from exc
    if type(lock) is not dict or lock.get("lockfileVersion") != 3:
        raise DependencyLockError("Expected npm lockfile v3")
    packages = lock.get("packages")
    if type(packages) is not dict or len(packages) != LOCK_PACKAGES:
        raise DependencyLockError("Unexpected npm dependency count")
    root = packages.get("")
    if (type(root) is not dict or
            root.get("name") != "@retailgrowthai/feature4-render-adapter" or
            root.get("dependencies") != {"@hyperframes/producer": PRODUCER_VERSION}):
        raise DependencyLockError("Package root is not the reviewed Feature4 producer")
    for package, version in (
        ("node_modules/@hyperframes/producer", PRODUCER_VERSION),
        ("node_modules/puppeteer", PUPPETEER_VERSION),
        ("node_modules/puppeteer-core", PUPPETEER_VERSION),
    ):
        if packages.get(package, {}).get("version") != version:
            raise DependencyLockError("Pinned runtime package changed")
    licenses = Counter()
    missing = []
    for name, pkg in packages.items():
        if not name:
            continue
        if type(name) is not str or not name.startswith(BASE_DIRECTORY) or type(pkg) is not dict:
            raise DependencyLockError("Unexpected dependency entry")
        uri = pkg.get("resolved")
        if (type(uri) is not str or urlparse(uri).scheme != "https" or
                urlparse(uri).hostname != ALLOWED_REGISTRY):
            raise DependencyLockError("Unapproved remote or local npm dependency")
        if type(pkg.get("integrity")) is not str or not SRI.fullmatch(pkg["integrity"]):
            raise DependencyLockError("Package without verified npm SRI")
        license_id = pkg.get("license")
        if type(license_id) is not str or not license_id:
            missing.append(name)
            licenses["NOT_DECLARED_IN_NPM_LOCK"] += 1
        else:
            licenses[license_id] += 1
    if len(missing) != 6 or not all(name.startswith("node_modules/@hyperframes/") for name in missing):
        raise DependencyLockError("Unreviewed missing-license package population")
    return {
        "kind": "FEATURE4_FROZEN_NPM_RESOLUTION_CHECK_NOT_LEGAL_CLEARANCE",
        "sha256": sha,
        "npm_lockfile_version": 3,
        "package_entries_including_root": len(packages),
        "producer": PRODUCER_VERSION,
        "puppeteer": PUPPETEER_VERSION,
        "allowed_registry": ALLOWED_REGISTRY,
        "lockfile_committed_to_repository": True,
        "transitive_license_review_complete": False,
        "legal_signoff_for_commercial_saas": False,
        "license_counts": dict(sorted(licenses.items())),
        "license_metadata_missing": missing,
        "warning": (
            "Missing npm license fields do not establish unlicensed code; "
            "upstream package licenses and all transitive notices must be inspected. "
            "LGPL libvips, Chromium, FFmpeg builds and redistribution are separate obligations."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description="Freeze Feature4 resolution before npm ci")
    parser.add_argument("--lock", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    try:
        result = verify_lock(args.lock)
        report = Path(args.report)
        if report.suffix != ".json":
            raise DependencyLockError("Expected local JSON report path")
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    except (OSError, DependencyLockError) as exc:
        parser.exit(2, "Feature4 npm dependency gate rejected: " + str(exc) + "\n")
    print("PASS: complete reviewed npm lock SHA256; npm ci can install exact tree")


if __name__ == "__main__":
    main()
