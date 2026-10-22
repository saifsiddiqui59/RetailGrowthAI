"""Worker cannot claim or complete records without narrow backend authorization."""
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from admin_store import AdminStore

SID, UID, AID = (str(uuid4()) for _ in range(3))


def test_revoked_membership_and_unlicensed_assets_rejected():
    admin = AdminStore("https://safe.supabase.co", "server-secret", transport=lambda *_args, **_kwargs: None)
    row = {"shop_id": SID, "created_by": UID, "media_asset_ids": [AID]}
    admin.request = lambda path, **kwargs: [] if path == "shop_memberships" else []
    assert not admin.still_authorized(row)
    admin.request = lambda path, **kwargs: (
        [{"role": "EDITOR"}] if path == "shop_memberships" else
        [{"id": AID, "shop_id": SID, "license_name": None}]
    )
    assert not admin.still_authorized(row)
    admin.request = lambda path, **kwargs: (
        [{"role": "EDITOR"}] if path == "shop_memberships" else
        [{"id": AID, "shop_id": str(uuid4()), "license_name": "owned"}]
    )
    assert not admin.still_authorized(row)


def test_admin_requires_https_and_secret():
    for origin, secret in (("http://unsafe.test", "secret"), ("https://safe.supabase.co", "")):
        try:
            AdminStore(origin, secret)
            assert False, "must reject"
        except ValueError:
            pass
