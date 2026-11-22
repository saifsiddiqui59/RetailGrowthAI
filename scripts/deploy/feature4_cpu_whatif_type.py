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
_RESOURCE_NAME = re.compile(r"^[a-z0-9._-]{1,160}$")


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
    # An invalid *name* is never printed. The fixed known provider/type
    # may still be reported to narrow an ARM Ignore diagnostic. The separate
    # what-if resource-id allowlist MUST continue to reject this change.
    irregular_name = not all(_RESOURCE_NAME.fullmatch(name) for name in chunks[2::2])
    typ = "/".join((chunks[0], *chunks[1::2]))
    if typ not in _ALLOWED:
        return "unrecognized-resource-type"
    return typ + "-irregular-name" if irregular_name else typ
