"""Review source invariants of new shop-scoped atomic subscription migration."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SQL=(ROOT/"supabase/migrations/20261023134701_p1_subscription_quota.sql").read_text()

def test_new_migration_has_transaction_and_private_rls():
    assert SQL.lstrip().startswith("-- RetailGrowthAI-only")
    assert SQL.rstrip().endswith("commit;")
    for part in ("begin;", "create table public.shop_subscriptions",
      "create table public.shop_usage_reservations",
      "alter table public.shop_subscriptions enable row level security;",
      "alter table public.shop_usage_reservations enable row level security;",
      "revoke all on public.shop_subscriptions from public,anon,authenticated;",
      "revoke all on public.shop_usage_reservations from public,anon,authenticated;",
      "create policy subscription_owner_read",
      "create policy subscription_usage_owner_read",
      "security definer set search_path = ''"):
        assert part in SQL

def test_server_owned_trial_and_immutable_atomic_reservation():
    for part in ("create trigger shop_trial_after_insert",
      "values (new.id,'TRIAL','TRIAL'",
      "create trigger subscription_reserve_campaign",
      "create trigger subscription_reserve_render",
      "for update;", "primary key (shop_id,operation,job_id)",
      "and m.user_id=actor and m.active",
      "actor is distinct from (select auth.uid())",
      "raise exception 'SUBSCRIPTION_REQUIRED' using errcode='RG001'",
      "raise exception 'QUOTA_EXCEEDED' using errcode='RG002'",
      "sub.period_start", "if consumed>=max_units then",
      "status not in ('TRIAL','ACTIVE')"):
        assert part in SQL
    assert "user_metadata" not in SQL.lower()
    assert "drop table" not in SQL.lower()

def test_backend_never_returns_raw_error_or_authorizes_browser_plan_write():
    http=(ROOT/"azure-functions/campaign-api/http_api.py").read_text()
    tenant=(ROOT/"azure-functions/campaign-api/tenant_store.py").read_text()
    admin=(ROOT/"azure-functions/campaign-api/admin_store.py").read_text()
    assert 'return 429, {"error": "QUOTA_EXCEEDED"}' in http
    assert 'return 402, {"error": "SUBSCRIPTION_REQUIRED"}' in http
    assert '"RG001", "RG002"' in tenant
    assert '"RG001", "RG002"' in admin
    assert 'SubscriptionDenied(response_code)' in tenant
    assert 'SubscriptionDenied(response_code)' in admin
