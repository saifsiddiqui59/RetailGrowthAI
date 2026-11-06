"""F3-08 composition boundary for private PNG reads (not a mounted HTTP route).

Only backend-created dependencies belong here. The authority must query fresh
rights; browser-provided grants, historical rows and service-role JWTs are not
accepted as substitutes for verified user JWT + RLS reads.
"""
from __future__ import annotations

from feature3_current_output_rights import Feature3CurrentOutputRights
from feature3_private_png_reader import Feature3RevocablePNGReader


def build_private_png_reader(*, tenant_store, verify_user_jwt,
                             authoritative_read, expected_output_sha256,
                             minimum_rights_revision, transport=None):
    """Bind trusted current-rights authority to the existing revocable reader.

    This does not provision credentials or enable an Azure endpoint. Caller
    must supply a backend-owned fresh rights lookup and a real JWT verifier.
    """
    if not callable(verify_user_jwt):
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
