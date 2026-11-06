-- RetailGrowthAI Feature #2 / F2-19+F2-20 proposed PRIVATE source tables.
-- CODE REVIEW PROPOSAL ONLY. DO NOT APPLY IN DEV OR PROD IN THIS SPRINT.
-- Needs independent tenant/security/finance reviewer; requires existing
-- public shops/campaigns, retail_private.has_role and an operator-provisioned
-- PRIVATE Supabase Storage bucket named feature2-private-voice.
-- User JWT has SELECT only; all INSERT/UPDATE/DELETE and outbox/leases must
-- be performed by independently reviewed, atomic, service-side transactions.
-- Source, job and audio records are NOT publish/rights/model approvals.

create table public.feature2_private_voice_plans (
    shop_id uuid not null references public.shops(id),
    campaign_id uuid not null references public.campaigns(id),
    source_plan jsonb not null,
    private boolean not null default true check (private is true),
    revoked_at timestamptz,
    revision bigint not null default 0 check (revision >= 0),
    primary key (shop_id,campaign_id),
    constraint feature2_voice_source_contract check (
        jsonb_typeof(source_plan) = 'object'
        and jsonb_typeof(source_plan->'creative_direction_v1') = 'object'
        and jsonb_typeof(source_plan->'approval_record') = 'object'
        and source_plan->'creative_direction_v1'->>'shop_id' = shop_id::text
        and source_plan->'creative_direction_v1'->>'campaign_id' = campaign_id::text
        and source_plan->'approval_record'->'can_publish' = 'false'::jsonb
    )
);
create index feature2_private_voice_plans_campaign_shop_idx
    on public.feature2_private_voice_plans(campaign_id,shop_id);
alter table public.feature2_private_voice_plans enable row level security;
revoke all on public.feature2_private_voice_plans
    from public, anon, authenticated;
grant select on public.feature2_private_voice_plans to authenticated;
grant all on public.feature2_private_voice_plans to service_role;
create policy feature2_voice_plan_editor_read on public.feature2_private_voice_plans
    for select to authenticated using (
        revoked_at is null and
        retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[])
    );

create table public.feature2_private_voice_jobs (
    shop_id uuid not null references public.shops(id),
    campaign_id uuid not null references public.campaigns(id),
    request_key uuid not null,
    job_receipt jsonb not null,
    revoked_at timestamptz,
    primary key (shop_id,campaign_id,request_key),
    constraint feature2_voice_job_contract check (
        jsonb_typeof(job_receipt) = 'object'
        and job_receipt->>'shop_id'=shop_id::text
        and job_receipt->>'campaign_id'=campaign_id::text
        and job_receipt->>'request_key'=request_key::text
        and job_receipt->>'provider'='kokoro-onnx'
        and job_receipt->'private'='true'::jsonb
        and job_receipt->'can_publish'='false'::jsonb
        and job_receipt->'paid_api_calls'='0'::jsonb
    )
);
create index feature2_private_voice_jobs_campaign_idx
    on public.feature2_private_voice_jobs(shop_id,campaign_id);
alter table public.feature2_private_voice_jobs enable row level security;
revoke all on public.feature2_private_voice_jobs
    from public, anon, authenticated;
grant select on public.feature2_private_voice_jobs to authenticated;
grant all on public.feature2_private_voice_jobs to service_role;
create policy feature2_voice_job_editor_read on public.feature2_private_voice_jobs
    for select to authenticated using (
        revoked_at is null and
        retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[])
    );

create table public.feature2_private_voice_assets (
    shop_id uuid not null references public.shops(id),
    campaign_id uuid not null references public.campaigns(id),
    audio_asset_id uuid not null,
    -- Exact shape checked by source reader:
    -- {shop_uuid}/{campaign_uuid}/{audio_asset_uuid}.wav
    object_path text not null,
    asset_receipt jsonb not null,
    revoked_at timestamptz,
    primary key (shop_id,campaign_id,audio_asset_id),
    unique (object_path),
    constraint feature2_voice_asset_path check (
        object_path = shop_id::text||'/'||campaign_id::text||'/'||
            audio_asset_id::text||'.wav'
    ),
    constraint feature2_voice_asset_contract check (
        jsonb_typeof(asset_receipt) = 'object'
        and asset_receipt->>'shop_id'=shop_id::text
        and asset_receipt->>'campaign_id'=campaign_id::text
        and asset_receipt->>'audio_asset_id'=audio_asset_id::text
        and asset_receipt->>'mime_type'='audio/wav'
        and asset_receipt->'private'='true'::jsonb
        and asset_receipt->'can_publish'='false'::jsonb
    )
);
create index feature2_private_voice_assets_campaign_idx
    on public.feature2_private_voice_assets(shop_id,campaign_id);
alter table public.feature2_private_voice_assets enable row level security;
revoke all on public.feature2_private_voice_assets
    from public, anon, authenticated;
grant select on public.feature2_private_voice_assets to authenticated;
grant all on public.feature2_private_voice_assets to service_role;
create policy feature2_voice_asset_editor_read on public.feature2_private_voice_assets
    for select to authenticated using (
        revoked_at is null and
        retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[])
    );

-- Review requirements before executing:
-- 1. A DB transaction must atomically reserve budget and job uniqueness,
--    source revision and lease fencing. The above tables do NOT implement it.
-- 2. A trusted server writer registers exact WAV SHA, duration and private
--    object path only after the underlying object upload succeeds.
-- 3. A genuine signed role is required; no seed customer/OWNER identities.
-- 4. Provision bucket separately with private=true, no public policies;
--    access must be authorized by owner/editor + exact shop/campaign/asset.
-- 5. No provider fallback, auto-publish, GPU, Azure deployment or paid model.
