"""Normalize only the pinned RetailGrowthAI DEV Postgres URI in memory.

Do not print the secret. Existing DEV pooler configuration can contain
unescaped reserved password characters, so raw urlsplit() is insufficient.
"""
from __future__ import annotations

from urllib.parse import quote, unquote, urlsplit

PROJECT = "jeearzffnjbvghwjjjrf"
POOLER = "aws-0-ap-northeast-1.pooler.supabase.com"


class DevDatabaseUriError(ValueError):
    pass


def normalize_dev_url(raw: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise DevDatabaseUriError("Missing protected DEV database URI")
    value = raw.strip()
    # Preserve the older DEV Session Pooler secret format where a password
    # may include unescaped reserved URL characters. Match BOTH fixed ends.
    for scheme in ("postgresql", "postgres"):
        prefix = f"{scheme}://postgres.{PROJECT}:"
        suffix = f"@{POOLER}:5432/postgres"
        if value.startswith(prefix) and value.endswith(suffix):
            password = value[len(prefix):-len(suffix)]
            if not password or "YOUR-PASSWORD" in password or password in {"password", "changeme"}:
                raise DevDatabaseUriError("Placeholder or missing DEV password")
            encoded = quote(unquote(password), safe="")
            return prefix + encoded + suffix

    try:
        uri = urlsplit(value)
        hostname = uri.hostname
        port = uri.port
        username = uri.username
        password = uri.password
    except (ValueError, AttributeError) as exc:
        raise DevDatabaseUriError("Malformed DEV database URI") from exc
    if not (uri.scheme in {"postgresql", "postgres"}
            and uri.path == "/postgres"
            and not uri.query and not uri.fragment
            and hostname in {f"db.{PROJECT}.supabase.co", POOLER}
            and port in ({5432, 6543} if hostname == POOLER else {5432})
            and username == (f"postgres.{PROJECT}" if hostname == POOLER else "postgres")
            and password and "YOUR-PASSWORD" not in password
            and password not in {"password", "changeme"}):
        raise DevDatabaseUriError("Not the exact RetailGrowthAI DEV database URI")
    return value
