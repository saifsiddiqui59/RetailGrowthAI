-- Transactional job dispatch and claim fencing. SOURCE ONLY: requires approved DEV migration.
begin;
alter table public.campaigns add column planning_claim_token uuid;
alter table public.render_jobs add column render_claim_token uuid;

-- Trigger-written in the same transaction as the user-visible job. Never expose to browsers.
create table public.job_outbox (
  id uuid primary key default gen_random_uuid(),
  kind text not null check (kind in ('planning','render')),
  job_id uuid not null,
  state text not null default 'PENDING' check (state in ('PENDING','CLAIMED','SENT')),
  delivery_attempts int not null default 0 check (delivery_attempts between 0 and 100),
  lease_token uuid,
  lease_until timestamptz,
  next_attempt_at timestamptz not null default now(),
  sent_at timestamptz,
  created_at timestamptz not null default now(),
  unique(kind,job_id)
);
create index job_outbox_ready on public.job_outbox(next_attempt_at,created_at)
  where state in ('PENDING','CLAIMED');
alter table public.job_outbox enable row level security;
revoke all on public.job_outbox from public, anon, authenticated;
grant select,insert,update on public.job_outbox to service_role;

create table public.job_poison_events (
  id uuid primary key default gen_random_uuid(),
  kind text not null check(kind in ('planning','render')),
  fingerprint text not null check(fingerprint ~ '^[0-9a-f]{64}$'),
  job_id uuid,
  recorded_at timestamptz not null default now(),
  unique(kind,fingerprint)
);
alter table public.job_poison_events enable row level security;
revoke all on public.job_poison_events from public, anon, authenticated;
grant select,insert on public.job_poison_events to service_role;

-- Runs after RLS authorization but inside the same INSERT transaction.
create function retail_private.enqueue_new_job()
returns trigger language plpgsql security definer set search_path = ''
as $$
begin
  if (tg_table_name = 'campaigns' and new.status = 'PLANNING') then
    insert into public.job_outbox(kind,job_id) values ('planning',new.id);
  elsif (tg_table_name = 'render_jobs' and new.status = 'QUEUED') then
    insert into public.job_outbox(kind,job_id) values ('render',new.id);
  end if;
  return new;
end;
$$;
revoke all on function retail_private.enqueue_new_job() from public,anon,authenticated;
create trigger campaign_job_outbox after insert on public.campaigns
  for each row execute function retail_private.enqueue_new_job();
create trigger render_job_outbox after insert on public.render_jobs
  for each row execute function retail_private.enqueue_new_job();

-- At-least-once dispatcher: a crashed sender's lease expires; a lost ACK may resend.
-- The worker's claim token/attempt always gates commits.
create function public.claim_outbox_events(p_limit integer default 20)
returns jsonb language plpgsql volatile security invoker set search_path = ''
as $$
declare v jsonb;
begin
  if p_limit < 1 or p_limit > 50 then raise exception 'invalid batch size'; end if;
  with available as (
    select id from public.job_outbox
     where ((state='PENDING' and next_attempt_at<=now())
        or (state='CLAIMED' and lease_until<=now()))
       and delivery_attempts<100
     order by created_at,id for update skip locked limit p_limit
  ), claimed as (
    update public.job_outbox o
       set state='CLAIMED',delivery_attempts=o.delivery_attempts+1,
           lease_token=gen_random_uuid(), lease_until=now()+interval '2 minutes'
      from available a where o.id=a.id
      returning o.id,o.kind,o.job_id,o.lease_token
  )
  select coalesce(jsonb_agg(to_jsonb(claimed)),'[]'::jsonb) into v from claimed;
  return v;
end;
$$;

create function public.confirm_outbox_event(p_id uuid,p_token uuid,p_sent boolean)
returns boolean language plpgsql volatile security invoker set search_path = ''
as $$
declare v_id uuid;
begin
  update public.job_outbox set
    state=case when p_sent then 'SENT' else 'PENDING' end,
    sent_at=case when p_sent then now() else sent_at end,
    next_attempt_at=case when p_sent then next_attempt_at
      else now() + least(delivery_attempts*delivery_attempts,300)*interval '1 second' end,
    lease_token=null,lease_until=null
  where id=p_id and state='CLAIMED' and lease_token=p_token
    and lease_until>now() returning id into v_id;
  return v_id is not null;
end;
$$;

-- Each successful claim gets a new unpredictable token and incremented attempt.
create or replace function public.claim_campaign_job(p_id uuid)
returns jsonb language plpgsql volatile security invoker set search_path = ''
as $$
declare v public.campaigns%rowtype;
begin
  update public.campaigns set
    planning_attempts=planning_attempts+1,
    planning_claim_token=gen_random_uuid(),
    planning_lease_until=now()+interval '25 minutes',planning_error_code=null
  where id=p_id and status='PLANNING' and planning_attempts<3
    and (planning_lease_until is null or planning_lease_until<=now())
  returning * into v;
  if v.id is null then return null; end if;
  return to_jsonb(v);
end;
$$;

create or replace function public.claim_render_job(p_id uuid)
returns jsonb language plpgsql volatile security invoker set search_path = ''
as $$
declare v public.render_jobs%rowtype;
begin
  update public.render_jobs set
    status='RUNNING',attempts=attempts+1,
    render_claim_token=gen_random_uuid(),
    render_lease_until=now()+interval '25 minutes',error_code=null
  where id=p_id and status in ('QUEUED','RUNNING') and attempts<3
    and (render_lease_until is null or render_lease_until<=now())
  returning * into v;
  if v.id is null then return null; end if;
  return to_jsonb(v);
end;
$$;

-- Atomic planner output and final status: no partial draft after a DB failure.
create function public.complete_campaign_claim(
  p_id uuid,p_attempt int,p_token uuid,p_days jsonb)
returns boolean language plpgsql volatile security invoker set search_path = ''
as $$
declare v public.campaigns%rowtype;
declare d jsonb;
declare idx int;
begin
  select * into v from public.campaigns where id=p_id for update;
  if not found or v.status<>'PLANNING' or v.planning_attempts<>p_attempt
     or v.planning_claim_token is distinct from p_token
     or v.planning_lease_until<=now() or p_token is null then return false; end if;
  if not exists (select 1 from public.shop_memberships m
      where m.shop_id=v.shop_id and m.user_id=v.created_by and m.active
        and m.role in ('OWNER','EDITOR')) then return false; end if;
  if jsonb_typeof(p_days)<>'array' or jsonb_array_length(p_days)<>v.duration_days
     then return false; end if;
  for idx in 1..v.duration_days loop
    d := p_days->(idx-1);
    if (d->>'day_index')::int<>idx or (d->>'campaign_id')::uuid<>v.id
       or (d->>'shop_id')::uuid<>v.shop_id or
       (d->>'scheduled_date')::date<>v.start_date+(idx-1)
       or jsonb_typeof(d->'linkedin')<>'object'
       or jsonb_typeof(d->'instagram')<>'object'
    then return false; end if;
  end loop;
  insert into public.campaign_days
      (id,campaign_id,shop_id,day_index,scheduled_date,topic,linkedin,instagram,review_status)
    select x.id,v.id,v.shop_id,x.day_index,x.scheduled_date,x.topic,x.linkedin,x.instagram,'DRAFT'
    from jsonb_to_recordset(p_days) as x(id uuid,campaign_id uuid,shop_id uuid,
      day_index int,scheduled_date date,topic text,linkedin jsonb,instagram jsonb)
    on conflict(campaign_id,day_index) do update
      set topic=excluded.topic,linkedin=excluded.linkedin,instagram=excluded.instagram;
  update public.campaigns set status='DRAFT',planning_lease_until=null,
      planning_claim_token=null,planning_error_code=null where id=v.id;
  return true;
end;
$$;

create function public.fail_campaign_claim(
  p_id uuid,p_attempt int,p_token uuid,p_code text,p_permanent boolean default false)
returns boolean language plpgsql volatile security invoker set search_path = ''
as $$
declare v public.campaigns%rowtype;
begin
  update public.campaigns set
    status=case when p_permanent or planning_attempts>=3 then 'FAILED' else 'PLANNING' end,
    planning_lease_until=null,planning_claim_token=null,planning_error_code=left(p_code,80)
  where id=p_id and status='PLANNING' and planning_attempts=p_attempt
    and planning_claim_token=p_token and planning_lease_until>now()
  returning * into v;
  if v.id is null then return false; end if;
  if v.status='PLANNING' then
    update public.job_outbox set state='PENDING',next_attempt_at=now()+interval '30 seconds',
      lease_token=null,lease_until=null where kind='planning' and job_id=p_id;
  end if;
  return true;
end;
$$;

-- Commit generated asset + successful render in a single fenced DB transaction.
-- Claim-specific object keys avoid collision between stale and replacement workers.
create function public.complete_render_claim(
  p_id uuid,p_attempt int,p_token uuid,p_object_path text)
returns boolean language plpgsql volatile security invoker set search_path = ''
as $$
declare v public.render_jobs%rowtype;
declare aid uuid;
begin
  select * into v from public.render_jobs where id=p_id for update;
  if not found or v.status<>'RUNNING' or v.attempts<>p_attempt
    or v.render_claim_token is distinct from p_token or p_token is null
    or v.render_lease_until<=now() then return false; end if;
  if p_object_path is distinct from
       (v.shop_id::text||'/renders/'||v.id::text||'/'||p_token::text||'.mp4')
    then return false; end if;
  if not exists (select 1 from public.shop_memberships m where
      m.shop_id=v.shop_id and m.user_id=v.requested_by and m.active
      and m.role in ('OWNER','EDITOR')) then return false; end if;
  insert into public.media_assets(shop_id,created_by,object_path,storage_bucket,
      mime_type,source,license_name,attribution)
    values(v.shop_id,v.requested_by,p_object_path,'retailgrowth-media',
      'video/mp4','GENERATED','owned','rendered from tenant-authorized assets')
    returning id into aid;
  update public.render_jobs set status='SUCCEEDED',output_asset_id=aid,
      error_code=null,render_lease_until=null,render_claim_token=null where id=p_id;
  return true;
end;
$$;

create function public.fail_render_claim(
  p_id uuid,p_attempt int,p_token uuid,p_code text,p_permanent boolean default false)
returns boolean language plpgsql volatile security invoker set search_path = ''
as $$
declare v public.render_jobs%rowtype;
begin
  update public.render_jobs set
    status=case when p_permanent or attempts>=3 then 'FAILED' else 'QUEUED' end,
    render_lease_until=null,render_claim_token=null,error_code=left(p_code,80)
  where id=p_id and status='RUNNING' and attempts=p_attempt
    and render_claim_token=p_token and render_lease_until>now()
  returning * into v;
  if v.id is null then return false; end if;
  if v.status='QUEUED' then
    update public.job_outbox set state='PENDING',next_attempt_at=now()+interval '30 seconds',
      lease_token=null,lease_until=null where kind='render' and job_id=p_id;
  end if;
  return true;
end;
$$;

-- Durable receipt BEFORE Azure poison trigger returns success/ACK.
-- A poison event never mutates a job while another valid lease is in force.
create function public.record_poison_event(p_kind text,p_fingerprint text,p_job_id uuid default null)
returns boolean language plpgsql volatile security invoker set search_path = ''
as $$
begin
  if p_kind not in ('planning','render') or p_fingerprint !~ '^[0-9a-f]{64}$'
    then raise exception 'invalid poison envelope'; end if;
  insert into public.job_poison_events(kind,fingerprint,job_id)
    values(p_kind,p_fingerprint,p_job_id)
    on conflict(kind,fingerprint) do nothing;
  return true;
end;
$$;

-- Scan active records, under locks: exhausted leases terminalize, remaining jobs
-- are re-dispatched only after their prior SENT cadence has elapsed.
create function public.reconcile_stale_jobs(p_limit int default 30)
returns jsonb language plpgsql volatile security invoker set search_path = ''
as $$
declare v record;
declare queued int:=0;
declare failed int:=0;
begin
  if p_limit<1 or p_limit>100 then raise exception 'invalid reconcile limit'; end if;
  for v in
    select id,planning_attempts as attempts from public.campaigns
    where status='PLANNING'
      and ((planning_lease_until is not null and planning_lease_until<now()-interval '60 seconds')
        or (planning_lease_until is null and created_at<now()-interval '60 seconds'))
    order by created_at for update skip locked limit p_limit
  loop
    if v.attempts>=3 then
      update public.campaigns set status='FAILED',planning_error_code='RETRY_EXHAUSTED',
        planning_claim_token=null,planning_lease_until=null where id=v.id;
      failed:=failed+1;
    else
      update public.job_outbox set state='PENDING',next_attempt_at=now(),
        lease_token=null,lease_until=null
      where kind='planning' and job_id=v.id
        and ((state='SENT' and sent_at<now()-interval '5 minutes')
          or (state='PENDING' and next_attempt_at<now()-interval '5 minutes')
          or (state='CLAIMED' and lease_until<now()-interval '60 seconds'));
      get diagnostics queued = row_count; -- overwritten below; only observability
    end if;
  end loop;
  for v in
    select id,attempts from public.render_jobs
    where status in ('QUEUED','RUNNING')
      and ((render_lease_until is not null and render_lease_until<now()-interval '60 seconds')
       or (render_lease_until is null and created_at<now()-interval '60 seconds'))
    order by created_at for update skip locked limit p_limit
  loop
    if v.attempts>=3 then
      update public.render_jobs set status='FAILED',error_code='RETRY_EXHAUSTED',
        render_claim_token=null,render_lease_until=null where id=v.id;
      failed:=failed+1;
    else
      update public.job_outbox set state='PENDING',next_attempt_at=now(),
        lease_token=null,lease_until=null
      where kind='render' and job_id=v.id
        and ((state='SENT' and sent_at<now()-interval '5 minutes')
          or (state='PENDING' and next_attempt_at<now()-interval '5 minutes')
          or (state='CLAIMED' and lease_until<now()-interval '60 seconds'));
    end if;
  end loop;
  return jsonb_build_object('failed',failed);
end;
$$;

do $$
declare f text;
begin
  foreach f in array array['claim_outbox_events(integer)',
    'confirm_outbox_event(uuid,uuid,boolean)',
    'claim_campaign_job(uuid)','claim_render_job(uuid)',
    'complete_campaign_claim(uuid,integer,uuid,jsonb)',
    'fail_campaign_claim(uuid,integer,uuid,text,boolean)',
    'complete_render_claim(uuid,integer,uuid,text)',
    'fail_render_claim(uuid,integer,uuid,text,boolean)',
    'record_poison_event(text,text,uuid)',
    'reconcile_stale_jobs(integer)']
  loop
    execute 'revoke all on function public.'||f||' from public,anon,authenticated';
    execute 'grant execute on function public.'||f||' to service_role';
  end loop;
end $$;
commit;