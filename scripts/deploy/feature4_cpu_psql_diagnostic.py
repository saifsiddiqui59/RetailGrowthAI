#!/usr/bin/env python3
"""Classify a protected DEV psql failure using only a fixed, redacted label.

Never prints the underlying stderr, a URI, SQL, password, or tenant ID.
This utility is diagnostic only; it cannot authorize migrations or Azure work.
"""
from __future__ import annotations

import sys
from pathlib import Path

MAX_BYTES = 32768


def classify(stderr: str) -> str:
    value = stderr.lower()
    if "password authentication failed" in value:
        return "PASSWORD_AUTHENTICATION_FAILED"
    if "tenant or user not found" in value or "user not found" in value:
        return "POOLER_USER_NOT_FOUND"
    if "no pg_hba.conf entry" in value or "permission denied for schema" in value:
        return "DATABASE_ACCESS_DENIED"
    if "permission denied" in value:
        return "DATABASE_PERMISSION_DENIED"
    if "could not translate host name" in value or "name or service not known" in value:
        return "HOSTNAME_RESOLUTION"
    if "certificate verify failed" in value or "ssl error" in value or "tls" in value:
        return "TLS_CONNECTION_FAILURE"
    if "timeout" in value or "timed out" in value:
        return "NETWORK_TIMEOUT"
    if "connection refused" in value or "network is unreachable" in value:
        return "DATABASE_NETWORK_UNREACHABLE"
    if "relation" in value and "does not exist" in value:
        return "SCHEMA_OBJECT_NOT_FOUND"
    if "syntax error" in value:
        return "READONLY_SQL_SYNTAX_FAILURE"
    if "invalid connection option" in value or "invalid uri" in value:
        return "INVALID_LIBPQ_URI"
    return "DATABASE_CONNECTION_OR_SQL_UNCLASSIFIED"


def main(argv=None) -> int:
    items = sys.argv[1:] if argv is None else argv
    if len(items) != 1:
        print("BLOCKED: DATABASE_CHECK_DIAGNOSTIC=INVALID_INVOCATION")
        return 3
    path = Path(items[0])
    try:
        # Stderr could contain tokens or adversarial text: never print it.
        raw = path.read_bytes()[:MAX_BYTES]
        category = classify(raw.decode("utf-8", errors="replace"))
    except (OSError, ValueError):
        category = "PRIVATE_DIAGNOSTIC_UNAVAILABLE"
    finally:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
    print("BLOCKED: DATABASE_CHECK_DIAGNOSTIC=" + category)
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
