-- Part 2 unsent cancellation with atomic, period-correct quota release.
-- STAGED SOURCE ONLY; never applied to hosted RetailGrowthAI without approval.
-- Ordered AFTER 20261023190900_p2_social_draft_revision.sql.
-- Keep the same private service-only RPC signature; no public API change.
begin;

create or replace function public.p2_cancel_social_job(
  p_shop uuid,p_job uuid,p_actor uuid,p_expected_revision integer
) returns boolean language plpgsql security definer set search_path=''
as $$
declare
  j public.social_publish_jobs%rowtype;
  released uuid;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'service only' using errcode='42501';
  end if;
  if p_expected_revision is null or p_expected_revision<1 then
    return false;
  end if;
  if not exists(
    select 1 from public.shop_memberships m
     where m.shop_id=p_shop and m.user_id=p_actor
       and m.active and m.role in ('OWNER','EDITOR')
  ) then return false; end if;

  -- Serialize against approvals, claims and another cancellation.
  select * into j from public.social_publish_jobs
    where id=p_job and shop_id=p_shop for update;
  if not found or j.revision is distinct from p_expected_revision
     or j.status not in ('DRAFT','APPROVED','QUEUED','RETRYABLE')
     or exists(
        select 1 from retail_private.social_publish_attempts a
         where a.job_id=p_job and a.finished_at is null
     ) then return false; end if;

  if j.status <> 'DRAFT' then
    -- Follow the reservation lock ordering job -> subscription; any
    -- overlapping new approval/reservation for the same shop serializes.
    perform 1 from public.shop_subscriptions s
      where s.shop_id=p_shop for update;
    if not found or not exists (
      select 1 from retail_private.social_publish_quota_ledger l
        where l.publish_job_id=p_job and l.shop_id=p_shop
    ) then return false; end if;
  end if;

  update public.social_publish_jobs
    set status='CANCELED',updated_at=now()
    where id=p_job and shop_id=p_shop;

  -- Only a never-sent job is eligible. This deletion and status update
  -- commit together; a racing approval cannot consume this slot early.
  delete from retail_private.social_publish_quota_ledger l
    where l.publish_job_id=p_job and l.shop_id=p_shop
    returning l.publish_job_id into released;
  if j.status <> 'DRAFT' and released is distinct from p_job then
    raise exception 'quota release inconsistent' using errcode='23514';
  end if;
  insert into public.social_publish_audit(
    shop_id,job_id,actor_user_id,event_code)
  values(p_shop,p_job,p_actor,'SOCIAL_JOB_CANCELED');
  if released is not null then
    insert into public.social_publish_audit(
      shop_id,job_id,actor_user_id,event_code)
    values(p_shop,p_job,p_actor,'SOCIAL_QUOTA_RELEASED');
  end if;
  return true;
end
$$;

revoke all on function public.p2_cancel_social_job(uuid,uuid,uuid,integer)
  from public,anon,authenticated;
grant execute on function public.p2_cancel_social_job(uuid,uuid,uuid,integer)
  to service_role;
commit;
