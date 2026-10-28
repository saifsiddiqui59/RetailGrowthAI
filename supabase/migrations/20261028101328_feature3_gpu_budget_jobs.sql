-- Feature3 Task3.4: service-only, default-OFF GPU job + existing AI ledger.
-- Source/review only. No Container Apps provisioning or automatic GPU worker.
begin;

alter table public.shop_ai_budget_controls
  add column feature3_gpu_enabled boolean not null default false,
  add column feature3_gpu_max_job_usd numeric(10,6) not null default 0
    check (feature3_gpu_max_job_usd between 0 and 2.5);

alter table public.shop_ai_spend_reservations
  drop constraint shop_ai_spend_reservations_operation_check;
alter table public.shop_ai_spend_reservations
  add constraint shop_ai_spend_reservations_operation_check
    check (operation in ('prompt','campaign_copy','image_generation'));
alter table public.shop_ai_spend_reservations
  drop constraint shop_ai_spend_reservations_reserved_usd_check;
alter table public.shop_ai_spend_reservations
  add constraint shop_ai_spend_reservations_reserved_usd_check
    check (reserved_usd > 0 and reserved_usd <= 2.5);

create table public.feature3_gpu_jobs (
  id uuid primary key default gen_random_uuid(),
  shop_id uuid not null references public.shops(id) on delete cascade,
  requested_by uuid not null references auth.users(id),
  design_id uuid not null,
  design_revision integer not null check(design_revision > 0),
  design_server_sha256 text not null check(design_server_sha256 ~ '^[a-f0-9]{64}$'),
  request_id uuid not null,
  reservation_id uuid not null unique references public.shop_ai_spend_reservations(id),
  status text not null default 'QUEUED'
    check(status in ('QUEUED','RUNNING','SUCCEEDED','FAILED')),
  attempts integer not null default 0 check(attempts between 0 and 1),
  claim_token uuid,
  lease_until timestamptz,
  output_asset_id uuid,
  error_code text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(shop_id,id),
  unique(shop_id,request_id),
  foreign key(shop_id,design_id) references public.feature3_poster_designs(shop_id,id),
  foreign key(shop_id,output_asset_id) references public.media_assets(shop_id,id),
  constraint feature3_output_status check(
    (status='SUCCEEDED' and output_asset_id is not null) or
    (status<>'SUCCEEDED' and output_asset_id is null)
  )
);
create index feature3_gpu_jobs_shop on public.feature3_gpu_jobs(shop_id,created_at desc);
alter table public.feature3_gpu_jobs enable row level security;
revoke all on public.feature3_gpu_jobs from public,anon,authenticated;
grant select on public.feature3_gpu_jobs to authenticated;
grant all on public.feature3_gpu_jobs to service_role;
create policy feature3_gpu_jobs_member_read on public.feature3_gpu_jobs
  for select to authenticated
  using(retail_private.has_role(shop_id,array['OWNER','EDITOR','VIEWER']));

create table retail_private.feature3_gpu_outbox (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null unique references public.feature3_gpu_jobs(id) on delete cascade,
  state text not null default 'PENDING' check(state in ('PENDING','CLAIMED','SENT')),
  attempts integer not null default 0 check(attempts between 0 and 10),
  claimed_until timestamptz,
  created_at timestamptz not null default now()
);
alter table retail_private.feature3_gpu_outbox enable row level security;
revoke all on retail_private.feature3_gpu_outbox from public,anon,authenticated;
grant all on retail_private.feature3_gpu_outbox to service_role;

-- Explicit backend-controlled *single* paid request; unlike the existing
-- Feature2 RPC this operation can quote more than USD0.05. Both share one
-- shop_ai_spend_reservations table and subscription-serializing lock.
create function public.feature3_reserve_gpu_job(
  p_shop_id uuid, p_actor_id uuid, p_design_id uuid,
  p_expected_revision integer, p_expected_sha256 text,
  p_request_id uuid, p_upper_cost_usd numeric
) returns jsonb language plpgsql security definer set search_path='' as $$
declare
  sub public.shop_subscriptions%rowtype;
  approval public.shop_ai_budget_controls%rowtype;
  d public.feature3_poster_designs%rowtype;
  current_cost numeric;
  reserved_cost numeric(10,6);
  current_count integer;
  rid uuid;
  jid uuid;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'Service-owned GPU queue only' using errcode='42501';
  end if;
  if p_shop_id is null or p_actor_id is null or p_design_id is null
     or p_request_id is null or p_expected_revision is null or
     p_expected_revision < 1 or p_expected_sha256 !~ '^[a-f0-9]{64}$'
     or p_upper_cost_usd is null or p_upper_cost_usd <= 0
     or p_upper_cost_usd > 2.5 then
    raise exception 'Invalid image job reservation' using errcode='22023';
  end if;
  reserved_cost := pg_catalog.ceil(p_upper_cost_usd * 1000000) / 1000000;
  if not exists(select 1 from public.shop_memberships m
       where m.shop_id=p_shop_id and m.user_id=p_actor_id and m.active
         and m.role in ('OWNER','EDITOR')) then
    raise exception 'Active author required' using errcode='42501';
  end if;
  select * into sub from public.shop_subscriptions
    where shop_id=p_shop_id for update;
  if not found or sub.status not in ('TRIAL','ACTIVE')
     or now()<sub.valid_from or now()>=sub.valid_until
     or now()<sub.period_start or now()>=sub.period_end then
    raise exception 'SUBSCRIPTION_REQUIRED' using errcode='RG001';
  end if;
  select * into approval from public.shop_ai_budget_controls
    where shop_id=p_shop_id for update;
  if not found or approval.enabled is not true
     or approval.feature3_gpu_enabled is not true
     or approval.approved_until is null or now()>=approval.approved_until
     or approval.feature3_gpu_max_job_usd<reserved_cost
     or approval.period_cap_usd<reserved_cost then
    raise exception 'GPU_COST_NOT_APPROVED' using errcode='RG003';
  end if;
  select * into d from public.feature3_poster_designs
    where shop_id=p_shop_id and id=p_design_id for update;
  if not found or d.status <> 'DRAFT' or
     d.revision<>p_expected_revision or
     d.server_document_sha256<>p_expected_sha256 then
    raise exception 'Versioned source denied' using errcode='RG004';
  end if;
  if exists(select 1 from public.feature3_gpu_jobs
       where shop_id=p_shop_id and request_id=p_request_id) or
     exists(select 1 from public.shop_ai_spend_reservations
       where shop_id=p_shop_id and request_id=p_request_id) then
    raise exception 'GPU_REQUEST_ALREADY_RESERVED' using errcode='RG005';
  end if;
  if exists(select 1 from public.feature3_gpu_jobs
       where shop_id=p_shop_id and status in ('QUEUED','RUNNING')) then
    raise exception 'GPU_CONCURRENCY_LIMIT' using errcode='RG004';
  end if;
  select coalesce(sum(case when state='SETTLED' then actual_usd else reserved_usd end),0),
         count(*) into current_cost,current_count
     from public.shop_ai_spend_reservations
    where shop_id=p_shop_id and period_start=sub.period_start;
  if current_cost+reserved_cost>approval.period_cap_usd or current_count>=200 then
    raise exception 'GPU_BUDGET_EXCEEDED' using errcode='RG004';
  end if;
  insert into public.shop_ai_spend_reservations
    (shop_id,request_id,actor_id,operation,period_start,reserved_usd)
    values (p_shop_id,p_request_id,p_actor_id,'image_generation',
            sub.period_start,reserved_cost)
    returning id into rid;
  insert into public.feature3_gpu_jobs
    (shop_id,requested_by,design_id,design_revision,
     design_server_sha256,request_id,reservation_id)
    values(p_shop_id,p_actor_id,p_design_id,p_expected_revision,
      p_expected_sha256,p_request_id,rid)
    returning id into jid;
  insert into retail_private.feature3_gpu_outbox(job_id) values(jid);
  return jsonb_build_object('shop_id',p_shop_id,'job_id',jid,
    'reservation_id',rid,'reserved_usd',reserved_cost,
    'status','QUEUED','gpu_started',false);
end $$;
revoke all on function public.feature3_reserve_gpu_job(uuid,uuid,uuid,integer,text,uuid,numeric)
  from public,anon,authenticated;
grant execute on function public.feature3_reserve_gpu_job(uuid,uuid,uuid,integer,text,uuid,numeric)
  to service_role;

-- No automatic expensive retry. A queued job may be claimed exactly once.
create function public.feature3_claim_gpu_job(p_job_id uuid, p_claim_token uuid)
returns jsonb language plpgsql security definer set search_path='' as $$
declare j public.feature3_gpu_jobs%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' or
     p_job_id is null or p_claim_token is null then return null; end if;
  select * into j from public.feature3_gpu_jobs where id=p_job_id for update;
  if not found or j.status<>'QUEUED' or j.attempts<>0 or not exists(
      select 1 from retail_private.feature3_gpu_outbox o
      where o.job_id=j.id and o.state='SENT'
  ) then return null; end if;
  update public.feature3_gpu_jobs
     set status='RUNNING',attempts=1,claim_token=p_claim_token,
         lease_until=now()+interval '15 minutes',updated_at=now()
   where id=p_job_id;
  return jsonb_build_object('shop_id',j.shop_id,'job_id',j.id,
    'attempt',1,'claim_token',p_claim_token);
end $$;
revoke all on function public.feature3_claim_gpu_job(uuid,uuid) from public,anon,authenticated;
grant execute on function public.feature3_claim_gpu_job(uuid,uuid) to service_role;

-- Only fenced actual worker may settle; never let client-supplied generated
-- bytes or signed URL authorize success. Must be registered private output.
create function public.feature3_finish_gpu_job(
  p_job_id uuid, p_claim_token uuid, p_actual_usd numeric,
  p_asset_id uuid default null
) returns boolean language plpgsql security definer set search_path='' as $$
declare j public.feature3_gpu_jobs%rowtype;
        r public.shop_ai_spend_reservations%rowtype;
        a public.media_assets%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'Service GPU settlement only' using errcode='42501';
  end if;
  select * into j from public.feature3_gpu_jobs where id=p_job_id for update;
  if not found or j.status<>'RUNNING' or j.attempts<>1 or
     j.claim_token is distinct from p_claim_token or
     j.lease_until is null or now()>=j.lease_until then
    raise exception 'Expired/stale GPU claim' using errcode='RG005';
  end if;
  select * into r from public.shop_ai_spend_reservations
     where id=j.reservation_id and shop_id=j.shop_id for update;
  if not found or r.state<>'RESERVED' or r.operation<>'image_generation' or
     p_actual_usd is null or p_actual_usd<0 or p_actual_usd>r.reserved_usd then
    raise exception 'Invalid GPU settlement' using errcode='22023';
  end if;
  if p_asset_id is not null then
    select * into a from public.media_assets
       where id=p_asset_id and shop_id=j.shop_id for update;
    if not found or a.storage_bucket<>'retailgrowth-media' or
       a.mime_type<>'image/png' or a.source<>'GENERATED' or
       a.object_path not like j.shop_id::text||'/feature3/gpu/'||j.id::text||'/%'
       or not exists(select 1 from storage.objects o where
          o.bucket_id='retailgrowth-media' and o.name=a.object_path) then
      raise exception 'Untrusted private image asset' using errcode='42501';
    end if;
  end if;
  update public.shop_ai_spend_reservations
    set state='SETTLED',actual_usd=p_actual_usd where id=r.id;
  update public.feature3_gpu_jobs
    set status=case when p_asset_id is null then 'FAILED' else 'SUCCEEDED' end,
        output_asset_id=p_asset_id,
        error_code=case when p_asset_id is null then 'GPU_OUTPUT_UNAVAILABLE' else null end,
        claim_token=null,lease_until=null,updated_at=now()
    where id=j.id;
  return true;
end $$;
revoke all on function public.feature3_finish_gpu_job(uuid,uuid,numeric,uuid)
  from public,anon,authenticated;
grant execute on function public.feature3_finish_gpu_job(uuid,uuid,numeric,uuid)
  to service_role;

commit;
