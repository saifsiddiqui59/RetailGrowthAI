-- Feature3 GPU job outbox dispatch and NON-RETRY paid-uncertainty audit.
-- SOURCE ONLY; default-off GPU, no hosted migration/deployment authorization.
begin;

alter table retail_private.feature3_gpu_outbox
 add column dispatch_token uuid,
 add column sent_at timestamptz;

create table retail_private.feature3_gpu_recovery_events (
  job_id uuid not null references public.feature3_gpu_jobs(id),
  kind text not null check(kind in ('EXPIRED_PAID_CLAIM','DISPATCH_EXHAUSTED')),
  observed_status text not null,
  observed_at timestamptz not null default now(),
  operator_action text not null default 'MANUAL_FINANCIAL_RECONCILIATION'
    check(operator_action='MANUAL_FINANCIAL_RECONCILIATION'),
  primary key (job_id,kind)
);
alter table retail_private.feature3_gpu_recovery_events enable row level security;
revoke all on retail_private.feature3_gpu_recovery_events from public,anon,authenticated;
grant select on retail_private.feature3_gpu_recovery_events to service_role;

-- One protected queue dispatcher may claim a bounded batch. Retry an
-- uncertain *queue enqueue* at most four times; the worker's SQL job claim
-- remains strictly one shot, and no GPU job is started by this function.
create function public.feature3_claim_gpu_dispatch(p_limit integer default 5)
returns jsonb language plpgsql security definer set search_path='' as $$
declare r record;
        packets jsonb:='[]'::jsonb;
        tok uuid;
        seq integer:=0;
begin
 if (select auth.role()) is distinct from 'service_role' then
   raise exception 'GPU dispatch is service-only' using errcode='42501';
 end if;
 if p_limit is null or p_limit not between 1 and 10 then
   raise exception 'invalid GPU dispatch limit' using errcode='22023';
 end if;
 for r in
   select o.id,o.job_id,j.shop_id from retail_private.feature3_gpu_outbox o
   join public.feature3_gpu_jobs j on j.id=o.job_id
   join public.shop_ai_budget_controls b on b.shop_id=j.shop_id
   join public.shop_subscriptions s on s.shop_id=j.shop_id
   where ((o.state='PENDING') or (o.state='CLAIMED' and o.claimed_until<now()))
     and o.attempts<4
     and j.status='QUEUED' and j.attempts=0
     and b.enabled and b.feature3_gpu_enabled and b.approved_until>now()
     and s.status in ('TRIAL','ACTIVE')
     and s.valid_from<=now() and s.valid_until>now()
     and s.period_start<=now() and s.period_end>now()
     and exists(select 1 from public.shop_memberships m
       where m.shop_id=j.shop_id and m.user_id=j.requested_by
         and m.active and m.role in ('OWNER','EDITOR'))
   order by o.created_at,o.id
   for update of o skip locked
   limit p_limit
 loop
   tok:=gen_random_uuid();
   update retail_private.feature3_gpu_outbox
      set state='CLAIMED',attempts=attempts+1,
          claimed_until=now()+interval '2 minutes',dispatch_token=tok
    where id=r.id;
   packets:=packets||jsonb_build_array(jsonb_build_object(
       'job_id',r.job_id,'shop_id',r.shop_id,
       'dispatch_token',tok,'expires_in_seconds',120));
 end loop;
 return packets;
end $$;
revoke all on function public.feature3_claim_gpu_dispatch(integer) from public,anon,authenticated;
grant execute on function public.feature3_claim_gpu_dispatch(integer) to service_role;

-- A queue acknowledgement is not a paid inference acknowledgement. A stale
-- dispatch token must not mark SENT or release the claim.
create function public.feature3_confirm_gpu_dispatch(
  p_job_id uuid,p_dispatch_token uuid,p_sent boolean
) returns boolean language plpgsql security definer set search_path='' as $$
declare matched uuid;
begin
 if (select auth.role()) is distinct from 'service_role' then
   raise exception 'GPU dispatch acknowledgement is service-only' using errcode='42501';
 end if;
 if p_job_id is null or p_dispatch_token is null or p_sent is null then return false; end if;
 update retail_private.feature3_gpu_outbox
    set state=case when p_sent then 'SENT' else 'PENDING' end,
        dispatch_token=null,claimed_until=null,
        sent_at=case when p_sent then now() else sent_at end
  where job_id=p_job_id and state='CLAIMED'
    and dispatch_token=p_dispatch_token and claimed_until>now()
    and exists(select 1 from public.feature3_gpu_jobs j
       where j.id=p_job_id and j.status='QUEUED' and j.attempts=0)
 returning id into matched;
 return matched is not null;
end $$;
revoke all on function public.feature3_confirm_gpu_dispatch(uuid,uuid,boolean)
 from public,anon,authenticated;
grant execute on function public.feature3_confirm_gpu_dispatch(uuid,uuid,boolean)
 to service_role;

-- Expired RUNNING may have consumed cloud money or committed an output.
-- Record a private operator incident; NEVER auto-claim, retry, refund,
-- settle cost, delete objects, or invent a measured USD amount.
create function public.feature3_audit_gpu_recovery(p_limit integer default 20)
returns integer language plpgsql security definer set search_path='' as $$
declare r record;
        inserted integer:=0;
        affected integer;
begin
 if (select auth.role()) is distinct from 'service_role' then
   raise exception 'GPU financial audit is service-only' using errcode='42501';
 end if;
 if p_limit is null or p_limit not between 1 and 50 then
   raise exception 'invalid GPU reconciliation limit' using errcode='22023';
 end if;
 for r in
  select j.id as job_id,j.status as observed_status,
    'EXPIRED_PAID_CLAIM'::text as kind
  from public.feature3_gpu_jobs j
  join public.shop_ai_spend_reservations s on s.id=j.reservation_id
  where j.status='RUNNING' and j.attempts=1 and j.lease_until<now()
    and s.state='RESERVED'
  union all
  select j.id as job_id,j.status as observed_status,
    'DISPATCH_EXHAUSTED'::text as kind
  from public.feature3_gpu_jobs j
  join retail_private.feature3_gpu_outbox o on o.job_id=j.id
  where j.status='QUEUED' and j.attempts=0 and o.attempts>=4
    and (o.state='PENDING' or (o.state='CLAIMED' and o.claimed_until<now()))
  limit p_limit
 loop
  insert into retail_private.feature3_gpu_recovery_events(job_id,kind,observed_status)
  values(r.job_id,r.kind,r.observed_status)
  on conflict(job_id,kind) do nothing;
  get diagnostics affected=row_count;
  inserted:=inserted+affected;
 end loop;
 return inserted;
end $$;
revoke all on function public.feature3_audit_gpu_recovery(integer)
  from public,anon,authenticated;
grant execute on function public.feature3_audit_gpu_recovery(integer)
  to service_role;

commit;
