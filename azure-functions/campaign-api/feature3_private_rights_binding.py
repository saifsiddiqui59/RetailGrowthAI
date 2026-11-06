"""F3-08 composition boundary for private PNG reads (not a mounted HTTP route).

Only backend-created dependencies belong here. The authority must query fresh
rights; browser-provided grants, historical rows and service-role JWTs are not
accepted as substitutes for verified user JWT + RLS reads.
"""
from __future__ import annotations

from feature3_current_output_rights import Feature3CurrentOutputRights, _SHA
from feature3_private_png_reader import Feature3RevocablePNGReader


def build_private_png_reader(*, tenant_store, verify_user_jwt,
                             authoritative_read, expected_output_sha256,
                             minimum_rights_revision, transport=None):
    """Bind trusted current-rights authority to the existing revocable reader.

    This does not provision credentials or enable an Azure endpoint. Caller
    must supply a backend-owned fresh rights lookup and a real JWT verifier.
    """
    # Validate immutable backend pins before constructing any privileged dependency.\n    # A missing or malformed pin must never fall back to an unpinned reader.\n    if (type(expected_output_sha256) is not str or\n            _SHA.fullmatch(expected_output_sha256) is None):\n        raise ValueError("Trusted immutable output SHA-256 required")\n    if (type(minimum_rights_revision) is not int or\n            minimum_rights_revision < 1):\n        raise ValueError("Trusted positive rights revision required")\n    if not callable(verify_user_jwt):
        raise ValueError("Verified user JWT adapter required")
    if not callable(authoritative_read):
        raise ValueError("Backend current rights lookup required")
    rights = Feature3CurrentOutputRights(
        authoritative_read=authoritative_read,
        expected_output_sha256=expected_output_sha256,
        minimum_rights_revision=minimum_rights_revision,
    )
    if expected_output_sha256 is None or minimum_rights_revision is None:
        raise ValueError("Trusted immutable output and revision pins required")
    return Feature3RevocablePNGReader(
        tenant_store=tenant_store,
        verify_user_jwt=verify_user_jwt,
        current_output_rights=rights,
        transport=transport,
    )
