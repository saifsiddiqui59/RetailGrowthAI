"""F3-08 backend-owned current output rights boundary (source only).

The independent provider must query current authoritative rights on EVERY call.
No UI assertion, media row, fixture or historical approval is a grant. This
adapter is not an Azure route and does not supply a service credential.
"""
from __future__ import annotations

import re
from uuid import UUID

_SHA = re.compile(r"^[0-9a-f]{64}$")
_FIELDS = frozenset({
    "shop_id", "job_id", "asset_id", "output_sha256", "rights_revision",
    "output_registered", "source_rights_current", "customer_approval_current",
    "rights_revoked", "job_succeeded", "private_storage",
})


def _uuid4(value):
    if type(value) is not str:
        return False
    try:
        return UUID(value).version == 4 and str(UUID(value)) == value
    except (ValueError, AttributeError):
        return False


class Feature3CurrentOutputRights:
    """Fail-closed callable for Feature3RevocablePNGReader.current_output_rights.

    authoritative_read(shop, job, asset) must be a backend-controlled, current
    rights lookup. It must not be sourced from a request or a client JWT claim.
    A fresh lookup is required on each invocation, including after byte IO.
    """

    def __init__(self, *, authoritative_read):
        if not callable(authoritative_read):
            raise ValueError("Independent current-rights read required")
        self._read = authoritative_read

    def __call__(self, shop_id, job_id, asset_id):
        if not all(_uuid4(v) for v in (shop_id, job_id, asset_id)):
            return False
        try:
            row = self._read(shop_id, job_id, asset_id)
        except Exception:
            return False
        if type(row) is not dict or set(row) != _FIELDS:
            return False
        if any(row.get(k) != v for k, v in (
            ("shop_id", shop_id), ("job_id", job_id), ("asset_id", asset_id)
        )):
            return False
        digest = row.get("output_sha256")
        revision = row.get("rights_revision")
        if (type(digest) is not str or _SHA.fullmatch(digest) is None or
                type(revision) is not int or revision < 1):
            return False
        return all(row.get(k) is True for k in (
            "output_registered", "source_rights_current",
            "customer_approval_current", "job_succeeded", "private_storage"
        )) and row.get("rights_revoked") is False
