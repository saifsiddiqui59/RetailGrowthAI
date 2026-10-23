"""Ensure the pending P2 OAuth release is never a silently hosted migration."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SQL=(ROOT/"supabase/part2/pending/20261023190100_p2_social_oauth_transactions.sql").read_text()
def test_p2_oauth_rpc_server_only_and_atomic():
    assert "update retail_private.social_oauth_states s" in SQL
    assert "and s.consumed_at is null" in SQL
    assert "grant execute on function public.p2_consume_oauth_state" in SQL
    assert "to service_role" in SQL
    assert "from public,anon,authenticated" in SQL
    assert "delete from retail_private.social_account_credentials" in SQL
    assert "status='RECONCILE'" in SQL
    assert "insert into retail_private.social_account_credentials" in SQL
def test_staging_only():
    assert not (ROOT/"supabase/migrations/20261023190100_p2_social_oauth_transactions.sql").exists()
