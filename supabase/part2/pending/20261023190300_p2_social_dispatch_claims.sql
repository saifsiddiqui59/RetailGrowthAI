-- RetailGrowthAI P2 social job attempt fencing, STAGED SOURCE ONLY.
-- Requires approved P2 foundation, OAuth transactions and quota migrations.
-- NEVER apply to hosted DEV without separate explicit owner authorization.
begin;

-- Only one active DB attempt per job, even across duplicate Azure queue deliveries.
create unique index p2_social_one_active_attempt
  on retail_private.social_publish_attempts(job_id)
  where finished_at is null;

-- UUID-only due-dispatch scanning. Queue messages carry NO credentials or media.
create function public.p2_due_social_job_ids(p_limit integer default 20)
returns table(job_id uuid) language plpgsql security definer set search_path=''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if p_limit not between 1 and 50 then
    raise exception 'invalid due limit' using errcode='22023';
  end if;
  return query
    select j.id from public.social_publish_jobs j
    join public.shop_subscriptions s on s.shop_id=j.shop_id
    join retail_private.social_publish_quota_ledger l
      on l.publish_job_id=j.id and l.shop_id=j.shop_id
      and l.period_start=s.period_start
    where j.provider in ('facebook','linkedin')\n      and j.status in ('APPROVED','QUEUED','RETRYABLE')
      and j.scheduled_at<=now() and j.attempts<5
      and j.approved_at is not null and j.approved_by is not null
      and j.approved_content_sha256 is not null
      and s.status in ('TRIAL','ACTIVE')
      and now()>=s.valid_from and now()<s.valid_until
      and now()>=s.period_start and now()<s.period_end
      and not exists (
        select 1 from retail_private.social_publish_attempts a
          where a.job_id=j.id and a.finished_at is null
      )
    order by j.scheduled_at,j.id limit p_limit;
end
$$;

-- Atomic CAS claim, after the job is due and a distinct publish quota was
-- reserved. An interrupted claim stays active, requiring reconciliation;
-- it is never automatically duplicated into an external create-post call.
create function public.p2_claim_social_publish(p_job uuid)
returns jsonb language plpgsql security definer set search_path=''
as $$
declare
  j public.social_publish_jobs%rowtype;
  token uuid;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  select * into j from public.social_publish_jobs
    where id=p_job for update;
  if not found or j.status not in ('APPROVED','QUEUED','RETRYABLE')
     or j.scheduled_at>now() or j.attempts>=5
     or j.approved_at is null or j.approved_by is null
     or j.approved_content_sha256 is null
     or exists (
       select 1 from retail_private.social_publish_attempts a
         where a.job_id=p_job and a.finished_at is null
     )
     or not exists (
       select 1 from retail_private.social_publish_quota_ledger l
       join public.shop_subscriptions s
         on s.shop_id=l.shop_id and s.period_start=l.period_start
       where l.publish_job_id=p_job and l.shop_id=j.shop_id
         and s.status in ('TRIAL','ACTIVE') and now()>=s.valid_from
         and now()<s.valid_until and now()>=s.period_start
         and now()<s.period_end
     ) then
    return null;
  end if;
  token:=gen_random_uuid();
  update public.social_publish_jobs set attempts=attempts+1,updated_at=now()
    where id=p_job;
  insert into retail_private.social_publish_attempts(job_id,attempt_no,claim_token)
    values(p_job,j.attempts+1,token);
  return jsonb_build_object('job_id',p_job,'claim_token',token);
end
$$;

-- The already-deployed text-only timer/queue must NEVER claim a future
-- Instagram/YouTube reviewed media job. A queue UUID may be old, duplicated
-- or injected: enforce the provider fence inside the DB, not just scanner.
-- This function locks the job in the SAME transaction as the generic claim,
-- so the provider cannot change between the check and the CAS.
create function public.p2_claim_social_text_publish(p_job uuid)
returns jsonb language plpgsql security definer set search_path=''
as $$
declare v_provider text;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'service only text publish claim' using errcode='42501';
  end if;
  select j.provider into v_provider
    from public.social_publish_jobs j where j.id=p_job for update;
  if v_provider is null or v_provider not in ('facebook','linkedin') then
    return null;
  end if;
  return public.p2_claim_social_publish(p_job);
end
$$;

-- Durable pre-side-effect barrier, verified by same active claim UUID.
create function public.p2_mark_social_inflight(p_job uuid,p_claim uuid)
returns boolean language plpgsql security definer set search_path=''
as $$
declare
  j public.social_publish_jobs%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  select * into j from public.social_publish_jobs where id=p_job for update;
  if not found or j.status not in ('APPROVED','QUEUED','RETRYABLE') then
    return false;
  end if;
  update retail_private.social_publish_attempts
    set result_code='EXTERNAL_INFLIGHT'
    where job_id=p_job and claim_token=p_claim and finished_at is null
      and result_code is null;
  if not found then return false; end if;
  update public.social_publish_jobs
    set status='SENDING',updated_at=now() where id=p_job;
  return true;
end
$$;

-- CAS records definitive provider receipts or uncertainty. No implicit retry
-- of SENDING/RECONCILE jobs: provider reconciliation must confirm first.
create function public.p2_finish_social_publish(
  p_job uuid,p_claim uuid,p_outcome text,p_error text default null,
  p_remote text default null
) returns boolean language plpgsql security definer set search_path=''
as $$
declare
  j public.social_publish_jobs%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if p_outcome not in ('FAILED','RETRYABLE','RECONCILE','PUBLISHED','PROCESSING')
    or (p_error is not null and (p_error !~ '^[A-Z0-9_]{1,64}$'))
    or (p_remote is not null and
        (length(p_remote) not between 1 and 180
         or p_remote !~ '^[A-Za-z0-9:_-]+$'))
    or (p_outcome in ('PUBLISHED','PROCESSING') and p_remote is null)
    or (p_outcome in ('FAILED','RETRYABLE','RECONCILE') and p_error is null)
    then raise exception 'invalid provider outcome' using errcode='22023';
  end if;
  select * into j from public.social_publish_jobs where id=p_job for update;
  if not found or j.status not in ('APPROVED','QUEUED','RETRYABLE','SENDING')
     or not exists (
       select 1 from retail_private.social_publish_attempts a
       where a.job_id=p_job and a.claim_token=p_claim and a.finished_at is null
     ) then
    return false;
  end if;
  -- A success or uncertain network attempt must have committed the SENDING
  -- barrier before outbound provider write; cannot be forged from an unmarked claim.
  if p_outcome in ('RECONCILE','PUBLISHED','PROCESSING')
     and (j.status<>'SENDING' or not exists (
       select 1 from retail_private.social_publish_attempts a
       where a.job_id=p_job and a.claim_token=p_claim
         and a.result_code='EXTERNAL_INFLIGHT' and a.finished_at is null
     )) then return false;
  end if;
  update retail_private.social_publish_attempts
    set finished_at=now(),result_code=coalesce(p_error,p_outcome)
    where job_id=p_job and claim_token=p_claim and finished_at is null;
  if not found then return false; end if;
  update public.social_publish_jobs
    set status=p_outcome,remote_post_id=p_remote,
        last_error_code=p_error,updated_at=now()
    where id=p_job;
  insert into public.social_publish_audit(shop_id,job_id,event_code)
    values(j.shop_id,p_job,'SOCIAL_ATTEMPT_'||p_outcome);
  return true;
end
$$;

revoke all on function public.p2_due_social_job_ids(integer)
  from public,anon,authenticated;
revoke all on function public.p2_claim_social_publish(uuid)
  from public,anon,authenticated;
revoke all on function public.p2_claim_social_text_publish(uuid)
  from public,anon,authenticated;
revoke all on function public.p2_mark_social_inflight(uuid,uuid)
  from public,anon,authenticated;
revoke all on function public.p2_finish_social_publish(uuid,uuid,text,text,text)
  from public,anon,authenticated;
grant execute on function public.p2_due_social_job_ids(integer) to service_role;
grant execute on function public.p2_claim_social_publish(uuid) to service_role;
grant execute on function public.p2_claim_social_text_publish(uuid)
  to service_role;
grant execute on function public.p2_mark_social_inflight(uuid,uuid) to service_role;
grant execute on function public.p2_finish_social_publish(uuid,uuid,text,text,text) to service_role;
commit;
