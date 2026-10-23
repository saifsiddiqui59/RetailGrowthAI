-- Part 2 draft edit/reschedule: pending-only, NEVER applied to hosted DB.
-- No approved, queued, sending or quota-reserved job may be silently edited.
begin;

create function public.p2_revise_social_draft(
  p_shop uuid, p_job uuid, p_actor uuid, p_revision integer,
  p_caption text, p_scheduled_at timestamptz, p_timezone text
) returns jsonb language plpgsql security definer set search_path=''
as $$
declare j public.social_publish_jobs%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'service only' using errcode='42501';
  end if;
  if p_revision is null or p_revision<1 or p_revision>=2147483647
     or length(trim(coalesce(p_caption,''))) not between 1 and 5000
     or p_caption ~ '[[:cntrl:]]'
     or length(coalesce(p_timezone,'')) not between 1 and 64
     or p_timezone ~ '[[:cntrl:]]'
     or p_scheduled_at is null
     or p_scheduled_at<now()+interval '1 minute'
     or p_scheduled_at>now()+interval '365 days' then
    raise exception 'invalid draft revision' using errcode='22023';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
      where m.shop_id=p_shop and m.user_id=p_actor and m.active
        and m.role in ('OWNER','EDITOR')
  ) then return null; end if;
  select * into j from public.social_publish_jobs
    where id=p_job and shop_id=p_shop for update;
  if not found or j.status<>'DRAFT' or j.revision<>p_revision
     or j.approved_by is not null or j.approved_at is not null
     or j.approved_content_sha256 is not null
     or exists(select 1 from retail_private.social_publish_quota_ledger q
                 where q.publish_job_id=p_job)
     or exists(select 1 from retail_private.social_publish_attempts a
                 where a.job_id=p_job)
     or not exists (
       select 1 from public.campaign_days d
        where d.id=j.campaign_day_id and d.shop_id=p_shop
          and d.review_status='APPROVED')
     or not exists (
       select 1 from public.social_accounts a
        where a.id=j.social_account_id and a.shop_id=p_shop
          and a.provider=j.provider and a.connection_status='CONNECTED')
  then return null; end if;
  update public.social_publish_jobs
     set caption=p_caption,scheduled_at=p_scheduled_at,timezone=p_timezone,
         revision=p_revision+1,updated_at=now()
   where id=p_job and shop_id=p_shop;
  insert into public.social_publish_audit(shop_id,job_id,actor_user_id,event_code)
    values(p_shop,p_job,p_actor,'SOCIAL_DRAFT_REVISED');
  return jsonb_build_object('id',p_job,'revision',p_revision+1,'status','DRAFT');
end
$$;

revoke all on function public.p2_revise_social_draft(
 uuid,uuid,uuid,integer,text,timestamptz,text) from public,anon,authenticated;
grant execute on function public.p2_revise_social_draft(
 uuid,uuid,uuid,integer,text,timestamptz,text) to service_role;
commit;
