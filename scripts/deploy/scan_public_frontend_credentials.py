#!/usr/bin/env python3
"""Fail-closed public frontend scan; never print matching credential bytes."""
import argparse
import base64
import json
import re
from pathlib import Path

# The exact standalone string in two existing browser token-rejection guards
# is not a secret. Only this expression is exempt, in JavaScript files only.
# Do not exempt other contexts or any prefix followed by credential bytes.
DEFENSIVE_PREFIX_CHECK = re.compile(rb"""\.startsWith\(\s*(["'])sb_secret_\1\s*\)""")
FORBIDDEN = (b"sb_secret_", b"RETAIL_SUPABASE_SERVICE_ROLE_KEY", b"RETAIL_FOUNDRY_API_KEY")
JWT = re.compile(rb"(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")

def contains_service_jwt(data):
    for match in JWT.finditer(data):
        try:
            payload = match.group().split(b".")[1]
            claims = json.loads(base64.urlsafe_b64decode(payload + b"=" * (-len(payload) % 4)))
        except (ValueError, UnicodeError):
            continue
        if isinstance(claims, dict) and claims.get("role") == "service_role":
            return True
    return False

def check_bytes(data, javascript=False):
    if contains_service_jwt(data):
        raise ValueError("SERVICE_ROLE_JWT_IN_PUBLIC_ARTIFACT")
    remaining = DEFENSIVE_PREFIX_CHECK.sub(b"", data) if javascript else data
    if any(marker in remaining for marker in FORBIDDEN):
        raise ValueError("PRIVILEGED_MARKER_IN_PUBLIC_ARTIFACT")

def scan(root):
    if not root.is_dir() or not (root / "index.html").is_file():
        raise ValueError("PUBLIC_ARTIFACT_MISSING")
    count = 0
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("UNEXPECTED_PUBLIC_ARTIFACT_SYMLINK")
        if path.is_file():
            check_bytes(path.read_bytes(), javascript=path.suffix in {".js", ".mjs"})
            count += 1
    if count < 2:
        raise ValueError("PUBLIC_ARTIFACT_EMPTY")
    return count

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dist", type=Path)
    args = parser.parse_args()
    try:
        count = scan(args.dist)
    except (OSError, ValueError):
        # Do not log offending source, filenames or secret values.
        raise SystemExit("PUBLIC_FRONTEND_CREDENTIAL_SCAN=FAIL") from None
    print(f"PUBLIC_FRONTEND_CREDENTIAL_SCAN=PASS files={count}")

if __name__ == "__main__":
    main()
