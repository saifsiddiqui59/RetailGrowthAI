"""Review-only SQL contract guards, not a database migration acceptance test."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "ai-agents" / "sql" / "feature2_voicestudio_jobs_REVIEW_ONLY.sql"


def source():
    return SOURCE.read_text(encoding="utf-8").lower()


def test_private_job_plan_schema_reuses_existing_shop_campaign_membership():
    sql = source()
    assert "review only" in sql
    assert "not applied to dev or prod" in sql
    assert "public.shops(id)" in sql
    assert "public.campaigns(id)" in sql
    assert "public.shop_memberships" in sql
    assert "public.feature2_voicestudio_plans" in sql
    assert "public.feature2_voicestudio_jobs" in sql
    assert "alter table public.feature2_voicestudio_plans enable row level security" in sql
    assert "alter table public.feature2_voicestudio_jobs enable row level security" in sql
    assert "status in ('draft','ready')" in sql


def test_four_rpcs_are_invoker_only_and_revoke_public_execution():
    sql = source()
    for rpc in ("plan", "claim", "register", "receipt"):
        name = "feature2_voicestudio_" + rpc
        creation = re.search(
            rf"create function public\.{name}\([\s\S]*?end; \$\$;",
            sql,
        )
        assert creation is not None, name
        assert "security invoker" in creation.group()
        assert "security definer" not in creation.group()
        assert f"revoke all on function public.{name}(" in sql
        assert f"grant execute on function public.{name}(" in sql
    assert sql.count("to service_role;") >= 5
    assert "grant execute on function public.feature2_voicestudio_claim" in sql
    assert "on conflict (shop_id,campaign_id,request_id) do nothing" in sql
    assert "claim_expires_at>now()" in sql


def test_sql_does_not_pretend_reviewed_audio_is_published():
    sql = source()
    assert "needs_review" in sql
    assert "'publish_approved',false" in sql
    assert "commercial_model_review_id is not null" in sql
    assert "source_review_receipt_id is not null" in sql
    assert "p_actor_id" in sql
    assert "m.active is true and m.role in ('owner','editor')" in sql
    assert "gen_random_uuid()" in sql
    assert "retailgrowth-media" in sql
    assert "voiceover_script" in sql
    assert "provider'='kokoro-onnx'" not in sql
    assert "grant insert on public.feature2_voicestudio_jobs to authenticated" not in sql
    assert "for all to authenticated" not in sql


def test_commercial_model_registry_is_owner_only_and_revocation_checked():
    sql = source()
    assert sql.count("create table public.feature2_voicestudio_model_reviews") == 1
    assert sql.count("create table public.feature2_voicestudio_plans") == 1
    assert sql.count("create function public.feature2_voicestudio_plan(") == 1
    assert sql.count("commit;") == 1
    assert "references public.feature2_voicestudio_model_reviews(id)" in sql
    assert "revoke all on public.feature2_voicestudio_model_reviews from public, anon, authenticated, service_role" in sql
    assert "grant select on public.feature2_voicestudio_model_reviews to service_role" in sql
    assert "grant insert on public.feature2_voicestudio_model_reviews" not in sql
    assert "weights_commercial_allowed boolean not null default false" in sql
    assert "tokenizer_commercial_allowed boolean not null default false" in sql
    assert "dependencies_commercial_allowed boolean not null default false" in sql
    assert "agpl_compliance_reviewed boolean not null default false" in sql
    assert sql.count("from public.feature2_voicestudio_model_reviews lic") == 4
    assert sql.count("lic.revoked_at is null") == 4
    assert sql.count("lic.weights_commercial_allowed is true") == 4
    assert sql.count("lic.tokenizer_commercial_allowed is true") == 4
    assert sql.count("lic.dependencies_commercial_allowed is true") == 4
    assert sql.count("lic.agpl_compliance_reviewed is true") == 4
