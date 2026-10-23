"""Candidate plan policy denies privilege escalation and expired/free usage."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import pytest
from ai_agents.subscriptions import SubscriptionEntitlement, SubscriptionDenied, check_entitlement, LIMITS

now=datetime(2026,10,23,tzinfo=timezone.utc)
SHOP=str(uuid4())
OTHER=str(uuid4())

def active(**updates):
    args={"shop_id":SHOP, "plan_code":"TRIAL", "status":"TRIAL",
      "valid_from":now-timedelta(days=1), "valid_until":now+timedelta(days=6),
      "billing_period_from":now-timedelta(days=1),
      "billing_period_until":now+timedelta(days=6)}
    args.update(updates)
    return SubscriptionEntitlement(**args)

def authorize(entitlement=None, **kwargs):
    return check_entitlement(entitlement or active(),
       shop_id=kwargs.get("shop_id",SHOP),role=kwargs.get("role","OWNER"),
       operation=kwargs.get("operation","campaign"),consumed=kwargs.get("consumed",0),
       now=kwargs.get("now",now))

def test_trial_and_paid_tier_candidate_units():
    assert authorize()==2
    assert authorize(operation="render",consumed=1)==1
    assert authorize(active(plan_code="STARTER",status="ACTIVE"),consumed=10)==5
    assert authorize(active(plan_code="GROWTH",status="ACTIVE"),operation="render",consumed=44)==1
    assert not set(LIMITS) & {"FREE_UNLIMITED","ADMIN"}

@pytest.mark.parametrize("kwargs", [
    {"shop_id":OTHER}, {"role":"VIEWER"}, {"role":"ADMIN"}, {"role":"CASHIER"},
    {"operation":"publish"}, {"consumed":2}, {"consumed":-1}, {"consumed":1.5},
    {"now":now+timedelta(days=7)},
])
def test_denied_quota_or_tenant(kwargs):
    with pytest.raises(SubscriptionDenied):
        authorize(**kwargs)

@pytest.mark.parametrize("changes", [
    {"status":"EXPIRED"}, {"status":"SUSPENDED"}, {"plan_code":"ULTRA"},
    {"valid_until":now}, {"billing_period_until":now},
])
def test_expired_invalid_denied(changes):
    with pytest.raises(SubscriptionDenied):
        authorize(active(**changes))

def test_naive_timestamp_rejected():
    with pytest.raises(ValueError):
        authorize(active(valid_from=now.replace(tzinfo=None)))

def test_entitlement_does_not_claim_atomicity_or_billing():
    # Reservation must be performed inside a DB transaction; this pure function
    # can be used only after server-side membership and quota-row locks.
    assert authorize(active(plan_code="BUSINESS",status="ACTIVE"),consumed=199)==1
