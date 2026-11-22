#!/usr/bin/env python3
"""Normalize a protected RetailGrowthAI DEV DB URI; never reveal a password.

Only exact DEV direct/session pooler endpoints are accepted. Legacy operator
secrets may contain an unescaped reserved password character. We normalize
the *password only* so psql sees the intended bytes, without loosening scope.
"""
from __future__ import annotations

import os
from pathlib import Path
import urllib.parse

PROJECT = "jeearzffnjbvghwjjjrf"
POOLER = "aws-0-ap-northeast-1.pooler.supabase.com"
SAFE_FILENAME = "f4cpu-private-dev-db-uri"


class ProjectUriError(ValueError):
    pass


def normalize_uri(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 8192:
        raise ProjectUriError("DEV DB URI missing or oversized")
    raw = value.strip()
    target = (
        (f"postgres.{PROJECT}", POOLER, (5432, 6543)),
        ("postgres", f"db.{PROJECT}.supabase.co", (5432,)),
    )
    for scheme in ("postgresql", "postgres"):
        for username, host, ports in target:
            prefix = f"{scheme}://{username}:"
            if not raw.startswith(prefix):
                continue
            sep = raw.rfind("@")
            if sep < len(prefix):
                raise ProjectUriError("Malformed DEV database connection")
            password = raw[len(prefix):sep]
            tail = raw[sep:]
            allowed = {
                f"@{host}:{port}/postgres{query}"
                for port in ports for query in ("", "?sslmode=require")
            }
            if tail not in allowed or not password or "YOUR-PASSWORD" in password:
                raise ProjectUriError("Wrong DEV database host or placeholder")
            normalized = urllib.parse.quote(urllib.parse.unquote(password), safe="")
            if not normalized:
                raise ProjectUriError("Blank DEV database password")
            return prefix + normalized + tail
    raise ProjectUriError("Wrong DEV database project")


def main() -> int:
    try:
        canonical = normalize_uri(os.environ.get("RETAIL_SUPABASE_DB_URL", ""))
        path = Path(os.environ["RUNNER_TEMP"]) / SAFE_FILENAME
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(path, flags, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as writer:
            writer.write(canonical)
        print("PASS: exact RetailGrowthAI DEV connection target verified privately")
        return 0
    except (ProjectUriError, OSError, KeyError):
        print("BLOCKED: exact DEV database secret validation or private storage failed")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
