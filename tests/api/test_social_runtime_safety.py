"""Part 2 OAuth and scheduling security tests; no provider traffic."""
import importlib.util
from pathlib import Path
from datetime import datetime, timedelta, timezone
import sys
import pytest
ROOT = Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + ".py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m

oauth = load("social_oauth")
schedule = load("social_scheduling")
SHOP = "10000000-0000-4000-8000-000000000001"
OTHER_SHOP = "10000000-0000-4000-8000-000000000002"
USER = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
ACCOUNT = "20000000-0000-4000-8000-000000000001"
NOW = datetime(2027, 1, 1, 12, tzinfo=timezone.utc)


def test_oauth_nonce_callback_identity_and_replay():
    start = oauth.new_oauth_state(now=NOW)
    assert start.expires_at == NOW + timedelta(minutes=10)
    params = dict(supplied_state=start.state, stored_state_digest=start.state_digest,
        expires_at=start.expires_at, consumed_at=None,
        expected_shop_id=SHOP, signed_in_shop_id=SHOP,
        expected_user_id=USER, signed_in_user_id=USER, now=NOW)
    assert oauth.verify_oauth_callback(**params)
    for overrides in ({"signed_in_shop_id": OTHER_SHOP},
                      {"supplied_state": "forged"},
                      {"consumed_at": NOW},
                      {"now": NOW + timedelta(minutes=11)}):
        with pytest.raises(oauth.OAuthDenied):
            oauth.verify_oauth_callback(**(params | overrides))
    with pytest.raises(oauth.OAuthDenied):
        oauth.exact_https_redirect("https://evil.example/callback", "https://retail.example/callback")


def test_aes_gcm_bound_to_shop_provider_and_account():
    vault = oauth.TokenVault(b"k" * 32, 1)
    sealed = vault.seal(shop_id=SHOP, provider="linkedin", account_id=ACCOUNT, token="sensitive-test-token")
    assert b"sensitive" not in sealed
    assert vault.open(shop_id=SHOP, provider="linkedin", account_id=ACCOUNT, ciphertext=sealed) == "sensitive-test-token"
    for shop, provider, data in ((OTHER_SHOP, "linkedin", sealed),
                                 (SHOP, "facebook", sealed),
                                 (SHOP, "linkedin", sealed[:-1] + b"x")):
        with pytest.raises(oauth.OAuthDenied):
            vault.open(shop_id=shop, provider=provider, account_id=ACCOUNT, ciphertext=data)


def test_wall_clock_dst_gap_and_overlap_are_explicit():
    with pytest.raises(schedule.ScheduleDenied):
        schedule.schedule_utc(day="2027-03-28",clock="02:30",
            zone="Europe/Berlin",now_utc=NOW)
    with pytest.raises(schedule.ScheduleDenied):
        schedule.schedule_utc(day="2027-10-31",clock="02:30",
            zone="Europe/Berlin",now_utc=NOW)
    earlier = schedule.schedule_utc(day="2027-10-31",clock="02:30",
        zone="Europe/Berlin",now_utc=NOW,fold=0)
    later = schedule.schedule_utc(day="2027-10-31",clock="02:30",
        zone="Europe/Berlin",now_utc=NOW,fold=1)
    assert (later-earlier).total_seconds() == 3600


def test_no_dispatch_without_approval_quota_or_account():
    gates = dict(job_status="APPROVED",scheduled_at=NOW,now_utc=NOW,
        approved_digest_matches=True,account_connected=True,membership_active=True,
        render_approved=True,quota_reserved=True,provider_access_approved=True)
    assert schedule.dispatch_eligibility(**gates)
    for gate in ("approved_digest_matches","account_connected","membership_active",
                 "render_approved","quota_reserved","provider_access_approved"):
        assert not schedule.dispatch_eligibility(**(gates | {gate:False}))
    assert schedule.failure_transition(attempts=1, ambiguous=True, retryable=True) == ("RECONCILE", None)
    assert schedule.failure_transition(attempts=5, ambiguous=False, retryable=True) == ("FAILED", None)
