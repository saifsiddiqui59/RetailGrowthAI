"""Part 2 migration contract checks; actual RLS live checks still require disposable SQL CI."""
from pathlib import Path
M = (Path(__file__).resolve().parents[2]/"supabase/migrations/20261023190000_p2_social_foundation.sql").read_text()

def test_public_rows_read_only_for_authenticated_users():
    assert "grant select on public.social_accounts,public.social_publish_jobs,public.social_publish_audit" in M
    assert "grant all on public.social_accounts,public.social_publish_jobs,public.social_publish_audit\n  to service_role" in M
    assert "retail_private.has_role(shop_id,array['OWNER','EDITOR','VIEWER'])" in M
    assert M.count("enable row level security") == 7

def test_credential_ciphertext_stays_private_and_no_old_migration_rewrites():
    assert "retail_private.social_account_credentials" in M
    assert "access_token_ciphertext bytea" in M
    assert "refresh_token_ciphertext bytea" in M
    assert "revoke all on retail_private.social_account_credentials" in M
    assert "alter table public.shop_subscriptions" not in M
    assert "drop table" not in M.lower()

def test_publish_is_review_gated_and_idempotent():
    assert "approved_content_sha256" in M
    assert "unique(shop_id,social_account_id,idempotency_key)" in M
    assert "social_publish_quota_ledger" in M
    assert "check (status <> 'PUBLISHED' or remote_post_id is not null)" in M
