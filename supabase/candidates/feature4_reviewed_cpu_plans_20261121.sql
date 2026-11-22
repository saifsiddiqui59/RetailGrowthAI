-- Feature2 -> Feature4: persist an actual per-shop creative approval instead of
-- treating a browser boolean, replayed token or synthetic fixture as approval.
-- CANDIDATE ONLY outside canonical migrations; tested in isolated Supabase CI.
-- Cannot be deployed or promoted until independently reviewed shared-schema gate.
-- This is the approved-plan gate, NOT the F4 quota/outbox/lease worker release.
begin;

create table public.feature4_creative_plans (
  id uuid primary key default gen_random_uuid(),
  shop_id uuid not null references public.shops(id) on delete cascade,
  campaign_id uuid not null,
  issued_by uuid not null references auth.users(id),
  proposal jsonb not null check (
    jsonb_typeof(proposal)='object'
    and proposal->>'version'='creative_direction_v1'
    and proposal->>'source_feature'='feature2'
    and proposal->'approved'='false'::jsonb
    and proposal->'script'->'approved'='false'::jsonb
    and not (proposal ? 'review_hash')
    and pg_column_size(proposal) <= 96000
  ),
  proposal_sha256 text not null check (proposal_sha256 ~ '^[0-9a-f]{64}$'),
  media_asset_ids uuid[] not null check (
    cardinality(media_asset_ids) between 1 and 12
  ),
  state text not null default 'DRAFT'
    check (state in ('DRAFT','APPROVED','REVOKED')),
  approved_direction jsonb,
  -- Immutable same-shop, original private object/license metadata, never a URL.
  media_snapshot jsonb,
  review_sha256 text check (
    review_sha256 is null or review_sha256 ~ '^[0-9a-f]{64}$'
  ),
  reviewed_by uuid references auth.users(id),
  reviewed_at timestamptz,
  revoked_at timestamptz,
  created_at timestamptz not null default now(),
  -- Prevent ambiguous or double-issued plan revisions across HTTP ACK loss.
  unique(shop_id,proposal_sha256),
  foreign key(shop_id,campaign_id) references public.campaigns(shop_id,id),
  check (
    (state='DRAFT' and approved_direction is null and review_sha256 is null
      and reviewed_by is null and reviewed_at is null and revoked_at is null
      and media_snapshot is null)
    or (state='APPROVED' and approved_direction is not null
      and review_sha256 is not null and reviewed_by is not null
      and reviewed_at is not null and revoked_at is null
      and media_snapshot is not null)
    or (state='REVOKED' and approved_direction is not null
      and review_sha256 is not null and reviewed_by is not null
      and reviewed_at is not null and revoked_at is not null
      and media_snapshot is not null)
  )
);
create index feature4_plans_shop_campaign on public.feature4_creative_plans
  (shop_id,campaign_id,created_at desc);
alter table public.feature4_creative_plans enable row level security;
revoke all on public.feature4_creative_plans from public,anon,authenticated;
grant select on public.feature4_creative_plans to authenticated;
grant select,insert,update on public.feature4_creative_plans to service_role;
create policy feature4_approved_plan_same_shop on public.feature4_creative_plans
  for select to authenticated
  using (retail_private.has_role(
    shop_id,array['OWNER','EDITOR','VIEWER']::text[]));

-- To avoid exposing a security-definer in public, only a narrow invoker
-- wrapper calls the non-exposed internal reviewer. No browser can insert,
-- modify or mint a project plan directly; source proposals must first be
-- issued by a reviewed backend after running genuine F2 compilation.
create function retail_private.feature4_review_cpu_plan_internal(
  p_plan_id uuid,p_expected_source_sha256 text
) returns jsonb
language plpgsql volatile security definer set search_path=''
as $function$
declare
  actor uuid := (select auth.uid());
  plan public.feature4_creative_plans%rowtype;
  media public.media_assets%rowtype;
  asset uuid;
  seen uuid[] := array[]::uuid[];
  shot jsonb;
  raw_id text;
  position_ms numeric := 0;
  seconds numeric;
  payload jsonb;
  reviewed jsonb;
  digest text;
  snapshot jsonb := '[]'::jsonb;
begin
  if p_plan_id is null or p_expected_source_sha256 is null
      or p_expected_source_sha256 !~ '^[0-9a-f]{64}$'
      or actor is null
      or (select auth.jwt())->>'role' is distinct from 'authenticated'
      or actor::text is distinct from (select auth.jwt())->>'sub'
      or (select auth.jwt())->>'is_anonymous'='true' then
    return null;
  end if;

  select * into plan from public.feature4_creative_plans p
  where p.id=p_plan_id and p.proposal_sha256=p_expected_source_sha256
  for update;
  if not found or plan.state='REVOKED'
      or not exists (
        select 1 from public.shop_memberships m
        where m.shop_id=plan.shop_id and m.user_id=actor
          and m.active and m.role in ('OWNER','EDITOR')
      )
      or not exists (
        select 1 from public.campaigns c
        where c.id=plan.campaign_id and c.shop_id=plan.shop_id
          and c.status in ('DRAFT','READY')
      )
  then return null; end if;
  -- Missing JSON approval keys evaluate to SQL NULL. Reject UNKNOWN.
  -- Check real server-issued proposal bytes; never trust a client-provided
  -- hash alone, and recheck the full existing revision on every invocation.
  if plan.proposal->>'shop_id' is distinct from plan.shop_id::text
      or plan.proposal->>'campaign_id' is distinct from plan.campaign_id::text
      or plan.proposal->>'version' is distinct from 'creative_direction_v1'
      or plan.proposal->>'source_feature' is distinct from 'feature2'
      or plan.proposal->'approved' is distinct from 'false'::jsonb
      or plan.proposal->'script'->'approved' is distinct from 'false'::jsonb
      or plan.proposal ? 'review_hash'
      or plan.proposal->'script'->>'source_feature' is distinct from 'feature2'
      or plan.proposal->'script'->>'cta' is distinct from plan.proposal->>'cta'
      or pg_catalog.jsonb_typeof(plan.proposal->'scenes') is distinct from 'array'
      or pg_catalog.jsonb_typeof(plan.proposal->'script'->'approved_text') is distinct from 'array'
      or (plan.proposal->>'duration_seconds' ~ '^(15|30|60)$') is not true
      or pg_catalog.jsonb_array_length(plan.proposal->'scenes') not between 1 and 12
      or plan.proposal_sha256 <> pg_catalog.encode(
          extensions.digest(pg_catalog.convert_to(
             retail_private.python_json_v1(plan.proposal),'UTF8'),'sha256'),'hex')
  then return null; end if;

  for shot in select value from pg_catalog.jsonb_array_elements(
      plan.proposal->'scenes') loop
    if pg_catalog.jsonb_typeof(shot) <> 'object'
        or pg_catalog.jsonb_typeof(shot->'duration') is distinct from 'number'
        or pg_catalog.jsonb_typeof(shot->'headline') is distinct from 'string'
        or (shot->>'asset_id' ~ '^[0-9a-f-]{36}$') is not true
        or ((plan.proposal->'script'->'approved_text') ? (shot->>'headline')) is not true
        or pg_catalog.char_length(shot->>'headline') not between 1 and 110
        or (shot->>'headline') ~ '[<>]'
    then return null; end if;
    raw_id := shot->>'asset_id';
    asset := raw_id::uuid;
    if asset::text <> raw_id or not asset=any(plan.media_asset_ids)
       then return null; end if;
    if not asset=any(seen) then seen:=pg_catalog.array_append(seen,asset); end if;
    seconds := (shot->>'duration')::numeric;
    if seconds < 0.5 or seconds > 30 or seconds*1000 <>
       pg_catalog.trunc(seconds*1000) then return null; end if;
    position_ms:=position_ms + seconds*1000;
  end loop;
  if position_ms <> (plan.proposal->>'duration_seconds')::integer * 1000
      or cardinality(seen) <> cardinality(plan.media_asset_ids)
      or (plan.proposal->'script'->'approved_text') ?
            (plan.proposal->>'cta') is not true
  then return null; end if;

  -- Currently only existing customer-owned, non-replaceable private UPLOAD
  -- stills are eligible. STOCK/GENERATED, licensed songs and video clips
  -- require independent bytes/rights review before widening this allowlist.
  for asset in select unnest(plan.media_asset_ids) loop
    select * into media from public.media_assets a
      where a.id=asset and a.shop_id=plan.shop_id for share;
    if not found or media.storage_bucket <> 'retailgrowth-media'
        or media.source <> 'UPLOAD'
        or coalesce(pg_catalog.lower(media.license_name),'') <> 'owned'
        or media.mime_type not in ('image/png','image/jpeg','image/webp')
        or pg_catalog.left(media.object_path,
               pg_catalog.length(plan.shop_id::text)+9) <>
           plan.shop_id::text || '/uploads/'
    then return null; end if;
    snapshot := snapshot || pg_catalog.jsonb_build_array(
      pg_catalog.jsonb_build_object('id',media.id,'shop_id',media.shop_id,
        'path',media.object_path,'mime',media.mime_type,
        'source',media.source,'license',media.license_name));
  end loop;
  -- A source tied to a saved campaign day becomes stale when the retailer
  -- edits/rejects its original reel. Never approve an earlier source revision.
  if (plan.proposal ? 'source_reel') then
    if pg_catalog.jsonb_typeof(plan.proposal->'source_reel') <> 'object'
       or plan.proposal->'music_asset_id' is distinct from 'null'::jsonb
       or plan.proposal->>'day_id' is null
       or (plan.proposal->>'day_id') !~
          '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
       or not exists (
           select 1 from public.campaign_days d
             where d.id=(plan.proposal->>'day_id')::uuid
               and d.campaign_id=plan.campaign_id
               and d.shop_id=plan.shop_id
               and d.review_status='DRAFT'
               and d.instagram->'reel'=plan.proposal->'source_reel'
       ) then return null; end if;
  end if;
  if plan.state='APPROVED' then
    return pg_catalog.jsonb_build_object(
      'approval_id',plan.id,'shop_id',plan.shop_id,
      'campaign_id',plan.campaign_id,'review_hash',plan.review_sha256,
      'status','APPROVED');
  end if;

  reviewed := plan.proposal || pg_catalog.jsonb_build_object(
    'approved',true,'approval_id',plan.id::text,
    'script',(plan.proposal->'script') ||
      pg_catalog.jsonb_build_object('approved',true,'approval_id',plan.id::text));
  -- Match Python direction_review_digest: SHA256 of the entire approved
  -- direction (excluding its own review_hash) with an explicit NUL domain
  -- separator. A browser never supplies this digest or the approved flag.
  digest := pg_catalog.encode(extensions.digest(
    pg_catalog.convert_to('rgai-f2-f4-approved-v1','UTF8') ||
    pg_catalog.decode('00','hex') ||
    pg_catalog.convert_to(retail_private.python_json_v1(reviewed),'UTF8'),
    'sha256'),'hex');
  update public.feature4_creative_plans
     set state='APPROVED',
         approved_direction=reviewed ||
             pg_catalog.jsonb_build_object('review_hash',digest),
         media_snapshot=snapshot,
         review_sha256=digest, reviewed_by=actor,reviewed_at=now()
   where id=plan.id;
  return pg_catalog.jsonb_build_object(
    'approval_id',plan.id,'shop_id',plan.shop_id,
    'campaign_id',plan.campaign_id,'review_hash',digest,
    'status','APPROVED');
end
$function$;
revoke all on function retail_private.feature4_review_cpu_plan_internal(uuid,text)
  from public,anon,authenticated;
grant execute on function retail_private.feature4_review_cpu_plan_internal(uuid,text)
  to authenticated;
create function public.feature4_review_cpu_plan(
  p_plan_id uuid,p_expected_source_sha256 text
) returns jsonb language sql volatile security invoker set search_path=''
as $wrapper$
  select retail_private.feature4_review_cpu_plan_internal(
      p_plan_id,p_expected_source_sha256)
$wrapper$;
revoke all on function public.feature4_review_cpu_plan(uuid,text)
  from public,anon,authenticated;
grant execute on function public.feature4_review_cpu_plan(uuid,text)
  to authenticated;

-- A revoked creative version must stay revoked; the retailer must obtain
-- a NEW independently reviewed proposal before a new render job is allowed.
create function retail_private.feature4_revoke_cpu_plan_internal(
  p_plan_id uuid
) returns boolean language plpgsql volatile security definer set search_path=''
as $function$
declare actor uuid := (select auth.uid());
        count_changed integer;
begin
  if p_plan_id is null or actor is null
     or (select auth.jwt())->>'role' is distinct from 'authenticated'
     or actor::text is distinct from (select auth.jwt())->>'sub'
     or (select auth.jwt())->>'is_anonymous'='true' then return false; end if;
  update public.feature4_creative_plans p
     set state='REVOKED',revoked_at=now()
  where p.id=p_plan_id and p.state='APPROVED'
    and exists (select 1 from public.shop_memberships m
      where m.shop_id=p.shop_id and m.user_id=actor and m.active
        and m.role='OWNER');
  get diagnostics count_changed = row_count;
  return count_changed=1;
end
$function$;
revoke all on function retail_private.feature4_revoke_cpu_plan_internal(uuid)
  from public,anon,authenticated;
grant execute on function retail_private.feature4_revoke_cpu_plan_internal(uuid)
  to authenticated;
create function public.feature4_revoke_cpu_plan(p_plan_id uuid)
returns boolean language sql volatile security invoker set search_path=''
as $wrapper$
  select retail_private.feature4_revoke_cpu_plan_internal(p_plan_id)
$wrapper$;
revoke all on function public.feature4_revoke_cpu_plan(uuid)
  from public,anon,authenticated;
grant execute on function public.feature4_revoke_cpu_plan(uuid) to authenticated;

commit;
