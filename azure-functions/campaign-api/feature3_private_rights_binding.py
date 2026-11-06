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
    # Validate trusted pins before constructing any privileged dependency.
    # Missing or malformed pins must never permit an unpinned reader.
    if (type(expected_output_sha256) is not str or
            _SHA.fullmatch(expected_output_sha256) is None):
        raise ValueError("Trusted immutable output SHA-256 required")
    if (type(minimum_rights_revision) is not int or
            minimum_rights_revision < 1):
        raise ValueError("Trusted positive rights revision required")
    if not callable(verify_user_jwt):
        raise ValueError("Verified user JWT adapter required")
    if not callable(authoritative_read):
        raise ValueError("Backend current rights lookup required")
    rights = Feature3CurrentOutputRights(
        authoritative_read=authoritative_read,
        expected_output_sha256=expected_output_sha256,
        minimum_rights_revision=minimum_rights_revision,
    )
    return Feature3RevocablePNGReader(
        tenant_store=tenant_store,
        verify_user_jwt=verify_user_jwt,
        current_output_rights=rights,
        transport=transport,
    )


def build_scoped_private_png_reader(*, shop_id, job_id, tenant_store,
                                    verify_user_jwt, authoritative_read,
                                    trusted_output_pins, transport=None):
    """Construct a per-output reader from fresh backend-owned immutable pins.

    The lookup is server-owned and must not accept request-provided approval
    metadata. Failure to obtain a complete, exact snapshot denies construction.
    A new reader is required for each output; pins are never reused across
    shops or jobs. The reader still rechecks current rights during byte IO.
    """
    from uuid import UUID

    def canonical(value):
        if type(value) is not str:
            return False
        try:
            return UUID(value).version == 4 and str(UUID(value)) == value
        except (ValueError, AttributeError):
            return False

    if not canonical(shop_id) or not canonical(job_id):
        raise ValueError("Canonical scoped shop/job UUID required")
    if not callable(trusted_output_pins):
        raise ValueError("Backend output pin lookup required")
    try:
        pins = trusted_output_pins(shop_id, job_id)
    except Exception:
        raise ValueError("Trusted output pins unavailable") from None
    if (type(pins) is not dict or
            set(pins) != {"shop_id", "job_id", "output_sha256",
                          "rights_revision"} or
            type(pins["shop_id"]) is not str or
            type(pins["job_id"]) is not str or
            pins["shop_id"] != shop_id or pins["job_id"] != job_id):
        raise ValueError("Trusted output pins mismatch")
    # A digest/revision pin is not a shop/job authorization grant. Bind
    # the fresh authority to the exact output scope before reading bytes.
    if not callable(authoritative_read):
        raise ValueError("Backend current rights lookup required")

    def scoped_authoritative_read(request_shop, request_job, asset_id):
        if (type(request_shop) is not str or type(request_job) is not str or
                request_shop != shop_id or request_job != job_id or
                type(asset_id) is not str):
            return None
        # Recheck backend-owned pins for every authorization, including the
        # post-byte check. A replaced output invalidates an existing reader.
        try:
            fresh = trusted_output_pins(shop_id, job_id)
        except Exception:
            return None
        if (type(fresh) is not dict or set(fresh) != set(pins) or
                any(type(fresh[k]) is not type(pins[k]) or
                    fresh[k] != pins[k] for k in pins)):
            return None
        return authoritative_read(request_shop, request_job, asset_id)

    return build_private_png_reader(
        tenant_store=tenant_store, verify_user_jwt=verify_user_jwt,
        authoritative_read=scoped_authoritative_read,
        expected_output_sha256=pins["output_sha256"],
        minimum_rights_revision=pins["rights_revision"],
        transport=transport,
    )
