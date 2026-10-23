"""Offline checks for exact publishing approval and media preflight."""
import importlib.util
from pathlib import Path
import sys
from datetime import datetime, timedelta, timezone
import pytest

path=Path(__file__).resolve().parents[2]/"azure-functions/campaign-api/social_publish_policy.py"
spec=importlib.util.spec_from_file_location("social_publish_policy",path)
p=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=p
spec.loader.exec_module(p)
SHOP="10000000-0000-4000-8000-000000000001"
OTHER="10000000-0000-4000-8000-000000000002"
DAY="30000000-0000-4000-8000-000000000001"
ACCOUNT="20000000-0000-4000-8000-000000000001"
MEDIA="40000000-0000-4000-8000-000000000001"
USER="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
NOW=datetime(2026,10,23,12,tzinfo=timezone.utc)
PROBE=dict(container="mp4",video_codec="h264",pixel_format="yuv420p",
           width=1080,height=1920,duration_seconds=30)

def fixture(provider="instagram"):
    job=dict(shop_id=SHOP,social_account_id=ACCOUNT,campaign_day_id=DAY,
        provider=provider,approved_by=USER,approved_at=NOW,
        status="APPROVED",caption="Reviewed approved message",
        media_asset_id=MEDIA if provider in ("instagram","youtube") else None,
        scheduled_at=NOW+timedelta(days=1),timezone="Asia/Kolkata",revision=1,
        quota_reserved=True)
    job["approved_content_sha256"]=p.approved_digest(
        shop_id=SHOP,day_id=DAY,account_id=ACCOUNT,platform=provider,
        caption=job["caption"],media_asset_id=job["media_asset_id"],
        scheduled_at=job["scheduled_at"],timezone_name=job["timezone"],revision=1)
    a=dict(id=ACCOUNT,shop_id=SHOP,provider=provider,connection_status="CONNECTED",
           granted_scopes=["content_publish"])
    m=dict(shop_id=SHOP,user_id=USER,active=True,role="EDITOR")
    e=dict(shop_id=SHOP,status="TRIAL",valid_until=NOW+timedelta(days=5))
    media=dict(shop_id=SHOP,id=MEDIA,rights_reviewed=True,probe=PROBE)
    return dict(job=job,shop_id=SHOP,account=a,membership=m,
        entitlement=e,media=media,now_utc=NOW,required_scopes={"content_publish"})

def test_approved_reel_requires_verified_provenance_and_exact_digest():
    assert p.check_approval(**fixture())
    assert p.check_approval(**fixture("youtube"))

@pytest.mark.parametrize("path,new_value", [
    ("shop_id",OTHER),("job.shop_id",OTHER),("account.shop_id",OTHER),
    ("membership.active",False),("membership.role","VIEWER"),
    ("account.connection_status","DISCONNECTED"),
    ("job.status","DRAFT"),("job.quota_reserved",False),
    ("entitlement.status","EXPIRED"),("entitlement.valid_until",NOW),
    ("job.caption","tampered"),("job.revision",2),
    ("job.scheduled_at",NOW+timedelta(days=2)),
    ("media.rights_reviewed",False),("media.shop_id",OTHER),
    ("media.probe.duration_seconds",120),("media.probe.video_codec","vp9"),
])
def test_guards_fail_closed(path,new_value):
    kw=fixture()
    keys=path.split(".")
    if path.startswith("media.probe."):
        kw["media"]["probe"]=dict(kw["media"]["probe"])
    current=kw
    for k in keys[:-1]:
        current=current[k]
    current[keys[-1]]=new_value
    with pytest.raises(p.PublishDenied):
        p.check_approval(**kw)

def test_text_adapters_cannot_claim_video():
    kw=fixture("linkedin")
    assert p.check_approval(**kw)
    kw["job"]["media_asset_id"]=MEDIA
    with pytest.raises(p.PublishDenied):
        p.check_approval(**kw)

def test_empty_scope_policy_denied_even_for_signed_in_member():
    kw=fixture()
    kw["required_scopes"]=set()
    with pytest.raises(p.PublishDenied):
        p.check_approval(**kw)
