-- Additive Part 1 poster job ledger and dedicated outbox. No cloud mutation by CI.
-- Independent from Part 2 publishing and Part 3 premium queue/usage ledgers.
begin;
create table public.poster_jobs (
  id uuid primary key default gen_random_uuid(),
  shop_id uuid not null,
  poster_id uuid not null,
  requested_by uuid not null references auth.users(id),
  revision integer not null check (revision > 0),
  snapshot jsonb not null,
  status text not null default 'QUEUED' check(status in ('QUEUED','RUNNING','SUCCEEDED','FAILED')),
  attempts integer not null default 0 check(attempts between 0 and 3),
  claim_token uuid,
  lease_until timestamptz,
  output_asset_id uuid,
  error_code text,
  created_at timestamptz not null default now(),
  unique (poster_id, revision),
  unique (shop_id, id),
  foreign key (shop_id, poster_id) references public.poster_drafts(shop_id,id) on delete cascade,
  foreign key (shop_id, output_asset_id) references public.media_assets(shop_id,id)
);
create index poster_jobs_ready_idx on public.poster_jobs (created_at)
  where status in ('QUEUED','RUNNING');
alter table public.poster_jobs enable row level security;
revoke all on public.poster_jobs from public, anon, authenticated;
grant select on public.poster_jobs to authenticated;
grant all on public.poster_jobs to service_role;
create policy poster_job_member_read on public.poster_jobs for select to authenticated
  using (retail_private.has_role(shop_id, array['OWNER','EDITOR','VIEWER']));

create table retail_private.poster_outbox (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null unique references public.poster_jobs(id) on delete cascade,
  state text not null default 'PENDING' check(state in ('PENDING','CLAIMED','SENT')),
  delivery_attempts integer not null default 0 check(delivery_attempts between 0 and 100),
  lease_token uuid,
  lease_until timestamptz,
  next_attempt_at timestamptz not null default now(),
  sent_at timestamptz,
  created_at timestamptz not null default now()
);
create index poster_outbox_dispatch_idx on retail_private.poster_outbox(next_attempt_at,created_at)
  where state in ('PENDING','CLAIMED');
revoke all on retail_private.poster_outbox from public, anon, authenticated;
grant select,insert,update on retail_private.poster_outbox to service_role;

create function retail_private.poster_enqueue() returns trigger
 language plpgsql security definer set search_path = '' as $$
begin
  insert into retail_private.poster_outbox(job_id) values (new.id);
  return new;
end $$;
revoke all on function retail_private.poster_enqueue() from public,anon,authenticated;
create trigger poster_job_enqueue after insert on public.poster_jobs
  for each row execute function retail_private.poster_enqueue();

-- Authenticated intent is durable and idempotent; no direct INSERT grants.
-- Saved campaign topic/CTA is pinned so subsequent edits cannot silently alter output.
create function public.request_poster_job(p_poster_id uuid)
returns uuid language plpgsql volatile security definer set search_path = '' as $$
declare p public.poster_drafts%rowtype;
        d public.campaign_days%rowtype;
        plan public.shop_subscriptions%rowtype;
        result_id uuid;
        actor uuid := (select auth.uid());
begin
 if (select auth.role()) is distinct from 'authenticated' or actor is null then return null; end if;
 select * into p from public.poster_drafts where id=p_poster_id for update;
 if not found or p.status not in ('DRAFT','RENDERING','READY')
    or not retail_private.has_role(p.shop_id,array['OWNER','EDITOR']) then return null; end if;
 select * into plan from public.shop_subscriptions where shop_id=p.shop_id for update;
 if not found or plan.status not in ('TRIAL','ACTIVE')
   or now()<plan.valid_from or now()>=plan.valid_until
   or now()<plan.period_start or now()>=plan.period_end then return null; end if;
 select * into d from public.campaign_days
   where id=p.day_id and campaign_id=p.campaign_id and shop_id=p.shop_id;
 if not found or d.review_status<>'DRAFT' or
   not exists(select 1 from public.campaigns c where c.id=p.campaign_id
     and c.shop_id=p.shop_id and c.status='DRAFT')
   or not exists(select 1 from jsonb_array_elements(
     case when jsonb_typeof(d.instagram#>'{reel,storyboard}')='array'
     then d.instagram#>'{reel,storyboard}' else '[]'::jsonb end) s
     where s->>'asset_id'=p.source_asset_id::text) then return null; end if;
 if not exists(select 1 from public.media_assets a
    where a.id=p.source_asset_id and a.shop_id=p.shop_id
    and a.storage_bucket='retailgrowth-media'
    and a.mime_type in ('image/jpeg','image/png','image/webp')
    and a.license_name in ('owned','cc0','royalty_free','commercial')
    and length(trim(coalesce(a.attribution,'')))>=10
    and (a.license_name='owned' or a.license_url like 'https://%')) then return null; end if;
 if p.logo_asset_id is not null and not exists(select 1 from public.media_assets a
    where a.id=p.logo_asset_id and a.shop_id=p.shop_id
    and a.storage_bucket='retailgrowth-media'
    and a.mime_type in ('image/jpeg','image/png','image/webp')
    and a.license_name in ('owned','cc0','royalty_free','commercial')
    and length(trim(coalesce(a.attribution,'')))>=10
    and (a.license_name='owned' or a.license_url like 'https://%')) then return null; end if;
 -- At most one render per draft revision, regardless of HTTP retries.
 select id into result_id from public.poster_jobs
    where poster_id=p.id and revision=p.revision;
 if result_id is not null then return result_id; end if;
 if p.status <> 'DRAFT' then return null; end if;
 insert into public.poster_jobs(shop_id,poster_id,requested_by,revision,snapshot)
 values(p.shop_id,p.id,actor,p.revision,
    jsonb_build_object('topic',d.topic,'cta',d.instagram#>>'{reel,cta}',
                       'day_index',d.day_index,'day_id',d.id))
 returning id into result_id;
 update public.poster_drafts set status='RENDERING',updated_at=now() where id=p.id;
 return result_id;
end $$;
revoke all on function public.request_poster_job(uuid) from public,anon,authenticated;
grant execute on function public.request_poster_job(uuid) to authenticated;

-- Service role alone claims an unexpired/fresh lease; terminal writes compare attempt + token.
create function public.claim_poster_job(p_id uuid)
returns jsonb language plpgsql volatile security invoker set search_path = '' as $$
declare v public.poster_jobs%rowtype;
begin
 update public.poster_jobs set status='RUNNING',attempts=attempts+1,
   claim_token=gen_random_uuid(),lease_until=now()+interval '5 minutes',error_code=null
 where id=p_id and status in ('QUEUED','RUNNING') and attempts<3
   and (lease_until is null or lease_until<=now()) returning * into v;
 if v.id is null then return null; end if;
 return to_jsonb(v);
end $$;
revoke all on function public.claim_poster_job(uuid) from public,anon,authenticated;
grant execute on function public.claim_poster_job(uuid) to service_role;

-- Completion binds the exact output key to the live claim and real asset rights.
-- The worker must independently decode/stage sources and validate the bytes.
create function public.complete_poster_job(p_id uuid,p_attempt int,p_token uuid,p_object_path text)
returns boolean language plpgsql volatile security invoker set search_path = '' as $$
declare j public.poster_jobs%rowtype;
        p public.poster_drafts%rowtype;
        d public.campaign_days%rowtype;
        result_asset uuid;
begin
 select * into j from public.poster_jobs where id=p_id for update;
 if not found or j.status<>'RUNNING' or j.attempts<>p_attempt
   or j.claim_token is distinct from p_token or p_token is null
   or j.lease_until<=now() or j.lease_until is null
   or p_object_path is distinct from
       (j.shop_id::text||'/posters/'||j.poster_id::text||'/'||p_token::text||'.png')
 then return false; end if;
 select * into p from public.poster_drafts where id=j.poster_id and shop_id=j.shop_id for update;
 if not found or p.status<>'RENDERING' or p.revision<>j.revision
    or not exists (select 1 from public.shop_memberships m
        where m.shop_id=j.shop_id and m.user_id=j.requested_by and m.active
        and m.role in ('OWNER','EDITOR')) then return false; end if;
 select * into d from public.campaign_days where id=p.day_id and shop_id=j.shop_id;
 if not found or d.review_status<>'DRAFT' or d.topic is distinct from j.snapshot->>'topic'
   or d.instagram#>>'{reel,cta}' is distinct from j.snapshot->>'cta'
   or not exists (select 1 from public.campaigns c where c.id=p.campaign_id
     and c.shop_id=j.shop_id and c.status='DRAFT')
   or not exists (select 1 from jsonb_array_elements(
      case when jsonb_typeof(d.instagram#>'{reel,storyboard}')='array'
      then d.instagram#>'{reel,storyboard}' else '[]'::jsonb end) s
      where s->>'asset_id'=p.source_asset_id::text) then return false; end if;
 if not exists (select 1 from public.media_assets a where a.id=p.source_asset_id
   and a.shop_id=j.shop_id and a.storage_bucket='retailgrowth-media'
   and a.license_name in ('owned','cc0','royalty_free','commercial')
   and length(trim(coalesce(a.attribution,'')))>=10) then return false; end if;
 if p.logo_asset_id is not null and not exists(select 1 from public.media_assets a
    where a.id=p.logo_asset_id and a.shop_id=j.shop_id
    and a.storage_bucket='retailgrowth-media'
    and a.license_name in ('owned','cc0','royalty_free','commercial')
    and length(trim(coalesce(a.attribution,'')))>=10) then return false; end if;
 insert into public.media_assets(shop_id,created_by,object_path,mime_type,
                                  source,license_name,attribution)
 values(j.shop_id,j.requested_by,p_object_path,'image/png','GENERATED','owned',
        'Generated from retailer-licensed poster inputs')
 returning id into result_asset;
 update public.poster_jobs set status='SUCCEEDED',output_asset_id=result_asset,
   claim_token=null,lease_until=null where id=j.id;
 update public.poster_drafts set status='READY',output_asset_id=result_asset,
   updated_at=now() where id=p.id;
 return true;
end $$;
revoke all on function public.complete_poster_job(uuid,int,uuid,text) from public,anon,authenticated;
grant execute on function public.complete_poster_job(uuid,int,uuid,text) to service_role;

create function public.fail_poster_job(p_id uuid,p_attempt int,p_token uuid,
 p_error text,p_permanent boolean default false)
returns boolean language plpgsql volatile security invoker set search_path = '' as $$
declare v public.poster_jobs%rowtype;
begin
 update public.poster_jobs set status=case when p_permanent or attempts>=3
     then 'FAILED' else 'QUEUED' end,
   claim_token=null,lease_until=null,error_code=left(coalesce(p_error,'POSTER_FAILED'),70)
 where id=p_id and status='RUNNING' and attempts=p_attempt and
   claim_token=p_token and lease_until>now()
 returning * into v;
 if v.id is null then return false; end if;
 if v.status='FAILED' then
   update public.poster_drafts set status='FAILED',updated_at=now()
    where id=v.poster_id and status='RENDERING';
 else
   update retail_private.poster_outbox set state='PENDING',lease_token=null,
      lease_until=null,next_attempt_at=now()+interval '30 seconds'
    where job_id=v.id;
 end if;
 return true;
end $$;
revoke all on function public.fail_poster_job(uuid,int,uuid,text,boolean) from public,anon,authenticated;
grant execute on function public.fail_poster_job(uuid,int,uuid,text,boolean) to service_role;

create function public.claim_poster_outbox(p_limit integer default 15)
returns jsonb language plpgsql volatile security invoker set search_path = '' as $$
declare result jsonb;
begin
 if p_limit is null or p_limit not between 1 and 50 then
   raise exception 'invalid poster outbox limit'; end if;
 with ready as (
  select id from retail_private.poster_outbox
   where ((state='PENDING' and next_attempt_at<=now())
      or (state='CLAIMED' and lease_until<=now()))
   and delivery_attempts<100 order by created_at,id limit p_limit for update skip locked
 ), claimed as (
  update retail_private.poster_outbox o set state='CLAIMED',
    delivery_attempts=o.delivery_attempts+1,lease_token=gen_random_uuid(),
    lease_until=now()+interval '2 minutes'
  from ready r where o.id=r.id
  returning o.id,o.job_id,o.lease_token
 )
 select coalesce(jsonb_agg(to_jsonb(claimed)),'[]'::jsonb) into result from claimed;
 return result;
end $$;
revoke all on function public.claim_poster_outbox(integer) from public,anon,authenticated;
grant execute on function public.claim_poster_outbox(integer) to service_role;

create function public.confirm_poster_outbox(p_id uuid,p_token uuid,p_sent boolean)
returns boolean language plpgsql volatile security invoker set search_path = '' as $$
declare affected uuid;
begin
 update retail_private.poster_outbox set
   state=case when p_sent then 'SENT' else 'PENDING' end,
   lease_token=null,lease_until=null,
   sent_at=case when p_sent then now() else sent_at end,
   next_attempt_at=case when p_sent then now()+interval '10 minutes'
      else now()+interval '30 seconds' end
 where id=p_id and state='CLAIMED' and lease_token=p_token and lease_until>now()
 returning id into affected;
 return affected is not null;
end $$;
revoke all on function public.confirm_poster_outbox(uuid,uuid,boolean) from public,anon,authenticated;
grant execute on function public.confirm_poster_outbox(uuid,uuid,boolean) to service_role;

-- Expired dispatch/worker claims can be recovered without another client POST.
create function public.reconcile_poster_jobs(p_limit integer default 20)
returns integer language plpgsql volatile security invoker set search_path = '' as $$
declare v record;
        count_updated integer:=0;
begin
 if p_limit is null or p_limit not between 1 and 50 then
  raise exception 'invalid poster recovery limit'; end if;
 for v in select id,poster_id,attempts,status from public.poster_jobs
  where status in ('QUEUED','RUNNING')
    and ((status='QUEUED' and created_at<now()-interval '1 minute')
      or (status='RUNNING' and lease_until<now()))
  order by created_at limit p_limit for update skip locked
 loop
   if v.status='RUNNING' and v.attempts>=3 then
     update public.poster_jobs set status='FAILED',claim_token=null,
        lease_until=null,error_code='RETRY_EXHAUSTED' where id=v.id;
     update public.poster_drafts set status='FAILED',updated_at=now()
        where id=v.poster_id and status='RENDERING';
   else
     update public.poster_jobs set status='QUEUED',claim_token=null,
        lease_until=null where id=v.id and status='RUNNING';
     update retail_private.poster_outbox set state='PENDING',lease_token=null,
       lease_until=null,next_attempt_at=now() where job_id=v.id;
   end if;
   count_updated:=count_updated+1;
 end loop;
 return count_updated;
end $$;
revoke all on function public.reconcile_poster_jobs(integer) from public,anon,authenticated;
grant execute on function public.reconcile_poster_jobs(integer) to service_role;
commit;
