-- READ-ONLY Feature4 pre-migration inventory. Verify connection targets
-- the dedicated RetailGrowthAI DEV project jeearzffnjbvghwjjjrf, not PROD.
-- A FALSE matched result means STOP; never auto-fix permissions or apply SQL.
-- Success is schema readiness, NOT security review or deployment approval.
with checks(label, expected_present, observed_present) as (
  values
    ('required table public.shops', true, pg_catalog.to_regclass('public.shops') is not null),
    ('required table public.campaigns', true, pg_catalog.to_regclass('public.campaigns') is not null),
    ('required table public.campaign_days', true, pg_catalog.to_regclass('public.campaign_days') is not null),
    ('required table public.media_assets', true, pg_catalog.to_regclass('public.media_assets') is not null),
    ('required table public.shop_memberships', true, pg_catalog.to_regclass('public.shop_memberships') is not null),
    ('required table public.shop_subscriptions', true, pg_catalog.to_regclass('public.shop_subscriptions') is not null),
    ('required table public.shop_usage_reservations', true, pg_catalog.to_regclass('public.shop_usage_reservations') is not null),
    ('required table storage.objects', true, pg_catalog.to_regclass('storage.objects') is not null),
    ('unapplied public.feature4_creative_plans', false, pg_catalog.to_regclass('public.feature4_creative_plans') is not null),
    ('unapplied public.feature4_cpu_render_jobs', false, pg_catalog.to_regclass('public.feature4_cpu_render_jobs') is not null),
    ('unapplied retail_private.feature4_cpu_outbox', false, pg_catalog.to_regclass('retail_private.feature4_cpu_outbox') is not null),
    ('unapplied retail_private.feature4_cpu_poison_receipts', false, pg_catalog.to_regclass('retail_private.feature4_cpu_poison_receipts') is not null),
    ('required routine retail_private.python_json_v1(jsonb)', true, pg_catalog.to_regprocedure('retail_private.python_json_v1(jsonb)') is not null),
    ('required routine retail_private.has_role(uuid,text[])', true, pg_catalog.to_regprocedure('retail_private.has_role(uuid,text[])') is not null),
    ('required routine extensions.digest(bytea,text)', true, pg_catalog.to_regprocedure('extensions.digest(bytea,text)') is not null),
    ('unapplied routine public.feature4_review_cpu_plan(uuid,text)', false, pg_catalog.to_regprocedure('public.feature4_review_cpu_plan(uuid,text)') is not null),
    ('unapplied routine public.feature4_submit_cpu_render(uuid,text)', false, pg_catalog.to_regprocedure('public.feature4_submit_cpu_render(uuid,text)') is not null),
    ('unapplied routine public.feature4_claim_cpu_render(uuid)', false, pg_catalog.to_regprocedure('public.feature4_claim_cpu_render(uuid)') is not null),
    ('unapplied routine public.feature4_complete_cpu_render(uuid,uuid,text,text)', false, pg_catalog.to_regprocedure('public.feature4_complete_cpu_render(uuid,uuid,text,text)') is not null),
    ('unapplied routine public.feature4_record_cpu_poison(text,uuid)', false, pg_catalog.to_regprocedure('public.feature4_record_cpu_poison(text,uuid)') is not null),
    ('media GENERATED source constraint',true, exists (select 1 from pg_catalog.pg_constraint c where c.conrelid='public.media_assets'::regclass and c.conname='media_assets_source_check' and pg_catalog.pg_get_constraintdef(c.oid) like '%GENERATED%')),
    ('quota render operation constraint',true, exists (select 1 from pg_catalog.pg_constraint c where c.conrelid='public.shop_usage_reservations'::regclass and c.conname='shop_usage_reservations_operation_check' and pg_catalog.pg_get_constraintdef(c.oid) like '%render%'))
)
select label,expected_present,observed_present,
       expected_present is not distinct from observed_present as matched
from checks
order by label;
