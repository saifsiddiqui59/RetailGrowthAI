"""Return only allowlisted ARM resource *type* descriptions, never IDs or names.

For diagnostics after a fail-closed ARM what-if. This does NOT decide whether
a change is permitted. Unknown/missing resource IDs must still BLOCK release.
"""
from __future__ import annotations

import re

_ALLOWED = frozenset({
    "microsoft.web/sites",
    "microsoft.web/sites/config",
    "microsoft.web/serverfarms",
    "microsoft.storage/storageaccounts",
    "microsoft.storage/storageaccounts/blobservices",
    "microsoft.storage/storageaccounts/blobservices/containers",
})
_NAME = re.compile(r"^[a-z][a-z0-9.]{1,79}$")
_TYPE = re.compile(r"^[a-z][a-z0-9]{1,79}$")


def classify_resource_type(value) -> str:
    """Never return untrusted resource IDs, names, tokens, or long strings."""
    if not isinstance(value, str) or not value:
        return "missing-id"
    if len(value) > 2048:
        return "oversized-id"
    marker = "/providers/"
    # ARM IDs may contain a preceding provider in extension resources.
    parts = value.lower().rsplit(marker, 1)
    if len(parts) != 2:
        return "missing-provider"
    chunks = parts[1].split("/")
    if len(chunks) < 3 or len(chunks) % 2 != 1:
        return "malformed-provider-shape"
    if not _NAME.fullmatch(chunks[0]):
        return "malformed-provider-namespace"
    if not all(_TYPE.fullmatch(t) for t in chunks[1::2]):
        return "malformed-resource-type"
    if not all(name and len(name) <= 160 for name in chunks[2::2]):
        return "malformed-resource-name"
    typ = "/".join((chunks[0], *chunks[1::2]))
    return typ if typ in _ALLOWED else "unrecognized-resource-type"
