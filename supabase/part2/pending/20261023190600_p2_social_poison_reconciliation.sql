-- RetailGrowthAI P2 social queue poison reconciliation, STAGED ONLY.
-- Requires approved pending 190000..190500 migrations; not hosted by CI.
begin;

create function public.p2_record_social_poison(p_job uuid)
returns boolean language plpgsql security definer set search_path=''
as $$
declare
  j public.social_publish_jobs%rowtype;
  outcome text;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'service role required' using errcode='42501';
  end if;
  select * into j from public.social_publish_jobs
    where id=p_job for update;
  if not found then return false; end if;
  if j.status in ('PUBLISHED','PROCESSING','CANCELED','FAILED','RECONCILE') then
    return true; -- poison redelivery is idempotent
  end if;
  if j.status='SENDING' then
    outcome:='RECONCILE'; -- remote provider may already have created the post
  elsif j.status in ('APPROVED','QUEUED','RETRYABLE') then
    outcome:='FAILED'; -- no independently confirmed external side effect
  else
    return false; -- do not change an unapproved DRAFT
  end if;
  update retail_private.social_publish_attempts
    set finished_at=now(),result_code='QUEUE_POISON'
    where job_id=p_job and finished_at is null;
  update public.social_publish_jobs
    set status=outcome,last_error_code='QUEUE_POISON',updated_at=now()
    where id=p_job;
  insert into public.social_publish_audit(shop_id,job_id,event_code)
    values(j.shop_id,j.id,'SOCIAL_QUEUE_POISON_'||outcome);
  return true;
end
$$;
revoke all on function public.p2_record_social_poison(uuid)
  from public,anon,authenticated;
grant execute on function public.p2_record_social_poison(uuid) to service_role;
commit;
