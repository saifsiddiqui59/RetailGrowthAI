-- RetailGrowthAI P2 backend-only authoring transactions. STAGED, NOT HOSTED.
-- Requires ordered P2 190000 through 190300 pending migrations first.
-- Publishing app remains disabled and cannot reserve without approved caps.
begin;

create function public.p2_create_social_draft(
  p_id uuid, p_shop uuid, p_actor uuid, p_day uuid,
  p_account uuid, p_provider text, p_caption text, p_media uuid,
  p_scheduled_at timestamptz, p_timezone text, p_idempotency text
) returns jsonb language plpgsql security definer set search_path=''
as $$
declare j public.social_publish_jobs%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'service only' using errcode='42501';
  end if;
  if p_provider not in ('facebook','linkedin','instagram','youtube')
      or length(trim(coalesce(p_caption,''))) not between 1 and 5000
      or p_caption ~ '[[:cntrl:]]'
      or length(coalesce(p_timezone,'')) not between 1 and 64
      or p_timezone ~ '[[:cntrl:]]'
      or p_scheduled_at is null or p_scheduled_at<now()+interval '1 minute'
      or p_scheduled_at>now()+interval '365 days'
      or p_idempotency !~ '^[A-Za-z0-9:_-]{8,128}$' then
    raise exception 'invalid social draft' using errcode='22023';
  end if;
  if (p_provider in ('facebook','linkedin') and p_media is not null)
      or (p_provider in ('instagram','youtube') and p_media is null) then
    raise exception 'unsupported provider media' using errcode='22023';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
      where m.shop_id=p_shop and m.user_id=p_actor and m.active
      and m.role in ('OWNER','EDITOR')
  ) or not exists (
    select 1 from public.campaign_days d
      where d.id=p_day and d.shop_id=p_shop
  ) or not exists (
    select 1 from public.social_accounts a
      where a.id=p_account and a.shop_id=p_shop
      and a.provider=p_provider and a.connection_status='CONNECTED'
  ) or (p_media is not null and not exists (
    select 1 from public.media_assets ma
      where ma.id=p_media and ma.shop_id=p_shop
  )) then
    raise exception 'social tenant or role denied' using errcode='42501';
  end if;
  insert into public.social_publish_jobs(
    id,shop_id,social_account_id,campaign_day_id,provider,
    revision,requested_by,scheduled_at,timezone,caption,media_asset_id,
    status,idempotency_key)
  values(p_id,p_shop,p_account,p_day,p_provider,1,p_actor,p_scheduled_at,
         p_timezone,p_caption,p_media,'DRAFT',p_idempotency)
  on conflict (shop_id,social_account_id,idempotency_key) do nothing;

  select * into j from public.social_publish_jobs
    where shop_id=p_shop and social_account_id=p_account
      and idempotency_key=p_idempotency for update;
  if not found or j.provider is distinct from p_provider
       or j.campaign_day_id is distinct from p_day
       or j.requested_by is distinct from p_actor
       or j.caption is distinct from p_caption
       or j.media_asset_id is distinct from p_media
       or j.scheduled_at is distinct from p_scheduled_at
       or j.timezone is distinct from p_timezone then
    raise exception 'idempotency conflict' using errcode='23505';
  end if;
  if j.id=p_id then
    insert into public.social_publish_audit(shop_id,job_id,actor_user_id,event_code)
      values(p_shop,j.id,p_actor,'SOCIAL_DRAFT_CREATED');
  end if;
  return jsonb_build_object('id',j.id,'status',j.status,'revision',j.revision);
end
$$;

-- This is called only by the JWT-verified backend, which first fetches the
-- authoritative row and computes the SHA-256 digest using approved_digest().
-- Exact field CAS below rejects a concurrent edit/reschedule between read and
-- approval. The quota reservation commits in THIS SAME transaction.
create function public.p2_approve_social_job(
  p_shop uuid,p_job uuid,p_actor uuid,p_revision integer,
  p_digest_hex text,p_caption text,p_scheduled_at timestamptz,
  p_timezone text,p_media uuid
) returns boolean language plpgsql security definer set search_path=''
as $$
declare j public.social_publish_jobs%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'service only' using errcode='42501';
  end if;
  if p_digest_hex !~ '^[0-9a-f]{64}$' or p_revision<1 then
    raise exception 'invalid approval digest' using errcode='22023';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
      where m.shop_id=p_shop and m.user_id=p_actor and m.active
      and m.role in ('OWNER','EDITOR')
  ) then return false; end if;
  select * into j from public.social_publish_jobs
    where id=p_job and shop_id=p_shop for update;
  if not found or j.status<>'DRAFT'
     or j.revision is distinct from p_revision
     or j.caption is distinct from p_caption
     or j.scheduled_at is distinct from p_scheduled_at
     or j.timezone is distinct from p_timezone
     or j.media_asset_id is distinct from p_media
     or j.scheduled_at<=now()+interval '1 minute'
     or not exists (
       select 1 from public.campaign_days d
         where d.id=j.campaign_day_id and d.shop_id=p_shop
         and d.review_status='APPROVED'
     ) or not exists (
       select 1 from public.social_accounts a
         where a.id=j.social_account_id and a.shop_id=p_shop
         and a.provider=j.provider and a.connection_status='CONNECTED'
     ) then return false; end if;
  -- Media rights/ffprobe authoritative approval is not yet staged.
  -- Therefore deny video publication, rather than approve unchecked media.
  if j.provider not in ('facebook','linkedin') or j.media_asset_id is not null then
    return false;
  end if;

  update public.social_publish_jobs
    set status='APPROVED',approved_by=p_actor,approved_at=now(),
        approved_content_sha256=decode(p_digest_hex,'hex'),updated_at=now()
    where id=p_job and shop_id=p_shop;
  -- Failure/no approved plan caps rolls back approval and prevents dispatch.
  if not public.p2_reserve_social_publish_quota(p_shop,p_job) then
    raise exception 'publish quota denied' using errcode='RG001';
  end if;
  insert into public.social_publish_audit(shop_id,job_id,actor_user_id,event_code)
    values(p_shop,p_job,p_actor,'SOCIAL_CONTENT_APPROVED');
  return true;
end
$$;

create function public.p2_cancel_social_job(
  p_shop uuid,p_job uuid,p_actor uuid,p_expected_revision integer
) returns boolean language plpgsql security definer set search_path=''
as $$
declare j public.social_publish_jobs%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'service only' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
      where m.shop_id=p_shop and m.user_id=p_actor and m.active
      and m.role in ('OWNER','EDITOR')
  ) then return false; end if;
  select * into j from public.social_publish_jobs
    where id=p_job and shop_id=p_shop for update;
  if not found or j.revision is distinct from p_expected_revision
     or j.status not in ('DRAFT','APPROVED','QUEUED','RETRYABLE') then
    -- Never pretend that a possibly outbound SENDING job was cancelled.
    return false;
  end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where id=p_job;
  insert into public.social_publish_audit(shop_id,job_id,actor_user_id,event_code)
    values(p_shop,p_job,p_actor,'SOCIAL_JOB_CANCELED');
  return true;
end
$$;

revoke all on function public.p2_create_social_draft(
  uuid,uuid,uuid,uuid,uuid,text,text,uuid,timestamptz,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_approve_social_job(
  uuid,uuid,uuid,integer,text,text,timestamptz,text,uuid)
  from public,anon,authenticated;
revoke all on function public.p2_cancel_social_job(uuid,uuid,uuid,integer)
  from public,anon,authenticated;
grant execute on function public.p2_create_social_draft(
  uuid,uuid,uuid,uuid,uuid,text,text,uuid,timestamptz,text,text) to service_role;
grant execute on function public.p2_approve_social_job(
  uuid,uuid,uuid,integer,text,text,timestamptz,text,uuid) to service_role;
grant execute on function public.p2_cancel_social_job(uuid,uuid,uuid,integer)
  to service_role;
commit;
