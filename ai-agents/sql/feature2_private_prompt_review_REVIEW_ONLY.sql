-- RetailGrowthAI F2-03/F2-31 signed reviewed-prompt source proposal.
-- REVIEW ONLY. DO NOT APPLY TO DEV OR PROD IN THIS CODE SPRINT.
-- No real signed human decision, model inference, provider charges, automatic
-- publishing, customer approval, or migration is created by this file.
-- Review tenant constraints with security lead before any execution.

create table public.feature2_private_prompt_drafts (
  shop_id uuid not null references public.shops(id),
  campaign_id uuid not null references public.campaigns(id),
  revision integer not null default 0 check (revision between 0 and 99999),
  brief text not null check (length(brief) between 1 and 1500),
  review_status text not null default 'DRAFT' check (review_status='DRAFT'),
  private boolean not null default true check (private is true),
  can_publish boolean not null default false check (can_publish is false),
  revoked_at timestamptz,
  primary key(shop_id,campaign_id)
);
alter table public.feature2_private_prompt_drafts enable row level security;
revoke all on public.feature2_private_prompt_drafts from public,anon,authenticated;
grant select on public.feature2_private_prompt_drafts to authenticated;
grant all on public.feature2_private_prompt_drafts to service_role;
create policy feature2_private_prompt_draft_editor_read
on public.feature2_private_prompt_drafts for select to authenticated
using (revoked_at is null and
       retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[]));

create table public.feature2_private_prompt_proposals (
  shop_id uuid not null,
  campaign_id uuid not null,
  proposal_id uuid not null,
  creative_plan_sha256 text not null check (
    creative_plan_sha256 ~ '^[0-9a-f]{64}$'),
  source_revision integer not null check (source_revision between 0 and 99999),
  original_prompt text not null check(length(original_prompt) between 1 and 1500),
  improved_prompt text not null check(length(improved_prompt) between 1 and 1500),
  original_prompt_sha256 text not null check(
    original_prompt_sha256 ~ '^[0-9a-f]{64}$'),
  improved_prompt_sha256 text not null check(
    improved_prompt_sha256 ~ '^[0-9a-f]{64}$'),
  review_status text not null default 'NEEDS_REVIEW'
    check (review_status='NEEDS_REVIEW'),
  private boolean not null default true check(private is true),
  can_publish boolean not null default false check(can_publish is false),
  revoked_at timestamptz,
  primary key(shop_id,campaign_id,proposal_id),
  foreign key(shop_id,campaign_id)
    references public.feature2_private_prompt_drafts(shop_id,campaign_id)
);
create index feature2_private_prompt_proposals_scope_idx on
  public.feature2_private_prompt_proposals(shop_id,campaign_id,source_revision);
alter table public.feature2_private_prompt_proposals enable row level security;
revoke all on public.feature2_private_prompt_proposals from public,anon,authenticated;
grant select on public.feature2_private_prompt_proposals to authenticated;
grant all on public.feature2_private_prompt_proposals to service_role;
create policy feature2_private_prompt_proposal_editor_read
on public.feature2_private_prompt_proposals for select to authenticated
using (revoked_at is null and
       retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[]));

create table public.feature2_private_editor_decisions (
  shop_id uuid not null,
  campaign_id uuid not null,
  proposal_id uuid not null,
  review_event_id uuid not null,
  reviewer_user_id uuid not null,
  source_revision integer not null check(source_revision between 0 and 99999),
  original_prompt_sha256 text not null check(
    original_prompt_sha256 ~ '^[0-9a-f]{64}$'),
  improved_prompt_sha256 text not null check(
    improved_prompt_sha256 ~ '^[0-9a-f]{64}$'),
  decision_state text not null check(
    decision_state='SIGNED_EDITOR_DRAFT_ONLY'),
  server_mac text not null check(server_mac ~ '^[0-9a-f]{64}$'),
  revoked_at timestamptz,
  primary key(shop_id,campaign_id,proposal_id,review_event_id),
  foreign key(shop_id,campaign_id,proposal_id)
    references public.feature2_private_prompt_proposals(
      shop_id,campaign_id,proposal_id
    )
);
alter table public.feature2_private_editor_decisions enable row level security;
revoke all on public.feature2_private_editor_decisions from public,anon,authenticated;
grant select on public.feature2_private_editor_decisions to authenticated;
grant all on public.feature2_private_editor_decisions to service_role;
create policy feature2_private_editor_decision_read
on public.feature2_private_editor_decisions for select to authenticated
using (revoked_at is null and auth.uid()=reviewer_user_id and
       retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[]));

-- Independently reviewed atomic backend RPC still REQUIRED, and deliberately
-- NOT included in this proposed schema:
-- 1. Verify current JWT reviewer identity and exact immutable source hashes.
-- 2. Verify the separately signed real reviewer decision BEFORE transaction.
-- 3. Atomically CAS source_revision->revision+1 with source shop/campaign,
--    grant/current plan, and exactly-one request UUID idempotency.
-- 4. Fence role revocation and no-publishing/no-billing DRAFT attributes.
-- 5. On uncertain ACK do NOT reissue POST; use a signed GET by request UUID.
-- 6. No browser-supplied raw rights, reviewer approval, path or trusted keys.
