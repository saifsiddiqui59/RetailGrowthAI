-- Feature 2 -> Feature 4: versioned, once-per-approved-plan CPU job.
-- SOURCE CANDIDATE; only the isolated CI database may load this file.
-- Depends on the separately reviewed feature4_creative_plans candidate.
-- Never deploy to hosted DEV or PROD without security/schema review.
-- No GPU, providers, model credits or client-issued approvals.
-- Required JSON approval predicates reject SQL NULL from absent keys.
begin;

create table public.feature4_cpu_render_jobs (
  id uuid primary key default gen_random_uuid(),
  shop_id uuid not null references public.shops(id) on delete cascade,
  campaign_id uuid not null,
  plan_id uuid not null unique references public.feature4_creative_plans(id),
  requested_by uuid not null references auth.users(id),
  approved_review_sha256 text not null check (approved_review_sha256 ~ '^[0-9a-f]{64}$'),
  idempotency_key text not null check (idempotency_key ~ '^[0-9a-f]{64}$'),
  status text not null default 'QUEUED'
    check (status in ('QUEUED','RUNNING','SUCCEEDED','FAILED')),
  attempts integer not null default 0 check (attempts between 0 and 3),
  render_claim_token uuid,
  render_lease_until timestamptz,
  output_asset_id uuid,
  output_sha256 text check(output_sha256 is null or output_sha256 ~ '^[0-9a-f]{64}$'),
  error_code text check (error_code is null or error_code ~ '^[A-Z_]{3,64}$'),
  created_at timestamptz not null default now(),
  completed_at timestamptz,
  unique(shop_id,idempotency_key),
  unique(shop_id,id),
  foreign key(shop_id,campaign_id) references public.campaigns(shop_id,id),
  foreign key(shop_id,output_asset_id) references public.media_assets(shop_id,id)
);
create index feature4_cpu_job_shop_recent on public.feature4_cpu_render_jobs
  (shop_id,created_at desc);
alter table public.feature4_cpu_render_jobs enable row level security;
revoke all on public.feature4_cpu_render_jobs from public,anon,authenticated;
grant select on public.feature4_cpu_render_jobs to authenticated;
grant select on public.feature4_cpu_render_jobs to service_role;
create policy feature4_cpu_job_same_shop on public.feature4_cpu_render_jobs
  for select to authenticated
  using (retail_private.has_role(shop_id,array['OWNER','EDITOR','VIEWER']::text[]));

-- Independent from legacy 'render' outbox so the legacy v1 queue/worker never
-- sees a new v2 job ID or interprets it as instagram_reel_30s.
create table retail_private.feature4_cpu_outbox (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null unique references public.feature4_cpu_render_jobs(id)
    on delete cascade,
  state text not null default 'PENDING'
    check(state in ('PENDING','CLAIMED','SENT','DEAD')),
  attempts integer not null default 0 check(attempts between 0 and 8),
  lease_token uuid,
  lease_until timestamptz,
  retry_after timestamptz not null default now(),
  created_at timestamptz not null default now(),
  delivered_at timestamptz
);
create index feature4_cpu_outbox_ready on retail_private.feature4_cpu_outbox
  (retry_after,created_at) where state in ('PENDING','CLAIMED');
revoke all on retail_private.feature4_cpu_outbox from public,anon,authenticated;
grant select on retail_private.feature4_cpu_outbox to service_role;

-- This function owns EVERY financial/job/outbox write; authenticated clients
-- only receive the narrow invoker wrapper. No direct job, quota or outbox grant.
create function retail_private.feature4_submit_cpu_render_internal(
  p_plan_id uuid,p_expected_review_hash text
) returns jsonb language plpgsql volatile security definer
set search_path='' as $body$
declare
  actor uuid := (select auth.uid());
  source public.feature4_creative_plans%rowtype;
  sub public.shop_subscriptions%rowtype;
  media public.media_assets%rowtype;
  snapshot_item jsonb;
  source_asset uuid;
  prior public.feature4_cpu_render_jobs%rowtype;
  job public.feature4_cpu_render_jobs%rowtype;
  current_claim text;
  key text;
  max_units integer;
  consumed integer;
  computed text;
begin
  if p_plan_id is null or p_expected_review_hash is null
    or p_expected_review_hash !~ '^[0-9a-f]{64}$'
    or actor is null
    or (select auth.jwt())->>'role' is distinct from 'authenticated'
    or actor::text is distinct from (select auth.jwt())->>'sub'
    or (select auth.jwt())->>'is_anonymous' = 'true'
  then return null; end if;

  -- Single-plan lock serializes duplicate submits by ANY eligible editor,
  -- including a lost POST ACK. No billing before all fresh checks.
  select * into source from public.feature4_creative_plans p
    where p.id=p_plan_id and p.state='APPROVED'
      and p.review_sha256=p_expected_review_hash for update;
  if not found or source.reviewed_by is null
     or source.approved_direction->>'approval_id' is distinct from source.id::text
     or source.approved_direction->'approved' is distinct from 'true'::jsonb
     or source.approved_direction->>'campaign_id' is distinct from source.campaign_id::text
     or source.approved_direction->>'shop_id' is distinct from source.shop_id::text
     or source.approved_direction->>'version' is distinct from 'creative_direction_v1'
     or source.approved_direction->'script'->'approved' is distinct from 'true'::jsonb
     or source.approved_direction->>'review_hash' is distinct from source.review_sha256
     or pg_catalog.jsonb_typeof(source.media_snapshot) is distinct from 'array'
     or pg_catalog.jsonb_array_length(source.media_snapshot)
          is distinct from cardinality(source.media_asset_ids)
  then return null; end if;

  computed := pg_catalog.encode(extensions.digest(
    pg_catalog.convert_to('rgai-f2-f4-approved-v1','UTF8')
      || pg_catalog.decode('00','hex')
      || pg_catalog.convert_to(retail_private.python_json_v1(
        source.approved_direction - 'review_hash'),'UTF8'),
    'sha256'),'hex');
  if computed is distinct from source.review_sha256 then return null; end if;

  if not exists (
      select 1 from public.shop_memberships m
      where m.shop_id=source.shop_id and m.user_id=actor
        and m.active and m.role in ('OWNER','EDITOR')
  ) or not exists (
      select 1 from public.campaigns c
      where c.id=source.campaign_id and c.shop_id=source.shop_id
        and c.status in ('DRAFT','READY')
  ) then return null; end if;

  -- Freeze original saved-day revision: after editing/rejecting a reel, an
  -- earlier approved storyboard must be sent back to retailer review.
  if source.approved_direction ? 'source_reel' then
    if source.approved_direction->>'day_id' is null
      or source.approved_direction->>'day_id' !~
        '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
      or not exists (
        select 1 from public.campaign_days d
        where d.id=(source.approved_direction->>'day_id')::uuid
          and d.campaign_id=source.campaign_id
          and d.shop_id=source.shop_id and d.review_status='DRAFT'
          and d.instagram->'reel'=source.approved_direction->'source_reel'
      ) then return null; end if;
  end if;

  -- Restrict first CPU lane to owned, immutable private UPLOAD stills only.
  -- Re-read against the EXACT reviewer snapshot so license/path edits and
  -- deleted or swapped metadata fail before even idempotent replays.
  for snapshot_item in select value
      from pg_catalog.jsonb_array_elements(source.media_snapshot) loop
    if pg_catalog.jsonb_typeof(snapshot_item) <> 'object'
       or (snapshot_item->>'id') !~
        '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    then return null; end if;
    source_asset := (snapshot_item->>'id')::uuid;
    select * into media from public.media_assets a
      where a.id=source_asset and a.shop_id=source.shop_id for share;
    if not found or not source_asset=any(source.media_asset_ids)
      or media.storage_bucket <> 'retailgrowth-media'
      or media.source <> 'UPLOAD' or pg_catalog.lower(media.license_name) <> 'owned'
      or media.mime_type not in ('image/png','image/jpeg','image/webp')
      or pg_catalog.left(media.object_path,
           pg_catalog.length(source.shop_id::text)+9)
           <> source.shop_id::text || '/uploads/'
      or snapshot_item <> pg_catalog.jsonb_build_object(
           'id',media.id,'shop_id',media.shop_id,'path',media.object_path,
           'mime',media.mime_type,'source',media.source,
           'license',media.license_name)
    then return null; end if;
  end loop;

  key := pg_catalog.encode(extensions.digest(pg_catalog.convert_to(
     'rgai-feature4-cpu-job-v1:' || source.shop_id::text || ':' ||
     source.id::text || ':' || source.review_sha256,'UTF8'),'sha256'),'hex');

  -- Idempotent replay must pass CURRENT actor, source and media checks.
  select * into prior from public.feature4_cpu_render_jobs j
    where j.plan_id=source.id;
  if found then
    if prior.shop_id <> source.shop_id
       or prior.approved_review_sha256 <> source.review_sha256
       or prior.idempotency_key <> key then return null; end if;
    return pg_catalog.jsonb_build_object(
      'id',prior.id,'job_id',prior.id,'shop_id',prior.shop_id,
      'status',prior.status);
  end if;

  select * into sub from public.shop_subscriptions s
    where s.shop_id=source.shop_id for update;
  if not found or sub.status not in ('TRIAL','ACTIVE')
    or now()<sub.valid_from or now()>=sub.valid_until
    or now()<sub.period_start or now()>=sub.period_end
  then
    raise exception 'SUBSCRIPTION_REQUIRED' using errcode='RG001';
  end if;
  max_units := case sub.plan_code
    when 'TRIAL' then 2
    when 'STARTER' then 10
    when 'GROWTH' then 45
    when 'BUSINESS' then 150
    else null end;
  if max_units is null then
    raise exception 'SUBSCRIPTION_REQUIRED' using errcode='RG001';
  end if;
  select pg_catalog.count(*) into consumed
    from public.shop_usage_reservations u
    where u.shop_id=source.shop_id and u.operation='render'
      and u.period_start=sub.period_start;
  if consumed >= max_units then
    raise exception 'QUOTA_EXCEEDED' using errcode='RG002';
  end if;

  insert into public.feature4_cpu_render_jobs (
    shop_id,campaign_id,plan_id,requested_by,approved_review_sha256,
    idempotency_key,status)
  values(source.shop_id,source.campaign_id,source.id,actor,
         source.review_sha256,key,'QUEUED')
  returning * into job;
  -- Existing quota ledger counts BOTH v1 and F4 v2 in the same period.
  insert into public.shop_usage_reservations(shop_id,operation,job_id,period_start)
    values(source.shop_id,'render',job.id,sub.period_start);
  insert into retail_private.feature4_cpu_outbox(job_id) values(job.id);

  return pg_catalog.jsonb_build_object(
    'id',job.id,'job_id',job.id,'shop_id',job.shop_id,'status',job.status);
end $body$;
revoke all on function retail_private.feature4_submit_cpu_render_internal(uuid,text)
  from public,anon,authenticated;
grant execute on function retail_private.feature4_submit_cpu_render_internal(uuid,text)
  to authenticated;

create function public.feature4_submit_cpu_render(
  p_plan_id uuid,p_expected_review_hash text
) returns jsonb language sql volatile security invoker set search_path=''
as $wrapper$
  select retail_private.feature4_submit_cpu_render_internal(
    p_plan_id,p_expected_review_hash)
$wrapper$;
revoke all on function public.feature4_submit_cpu_render(uuid,text)
  from public,anon,authenticated;
grant execute on function public.feature4_submit_cpu_render(uuid,text)
  to authenticated;

commit;
