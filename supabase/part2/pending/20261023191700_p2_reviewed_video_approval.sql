-- RetailGrowthAI Part 2: conditional, reviewed VIDEO approval RPC, STAGED ONLY.
-- No HTTP/Azure route calls this RPC. Existing p2_approve_social_job continues
-- to DENY Instagram/YouTube until a separately approved provider release.
-- Requires all Part2 pending 190000..191600 in ascending version order.
begin;

create function public.p2_approve_reviewed_video_job(
  p_shop uuid,p_job uuid,p_actor uuid,p_revision integer,
  p_digest_hex text,p_caption text,p_scheduled_at timestamptz,
  p_timezone text,p_media uuid,p_source_sha text
) returns boolean language plpgsql security definer set search_path=''
as $$
declare
  j public.social_publish_jobs%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'reviewed video approval requires service role'
      using errcode='42501';
  end if;
  if p_digest_hex is null or p_digest_hex !~ '^[0-9a-f]{64}$'
     or p_source_sha is null or p_source_sha !~ '^[0-9a-f]{64}$'
     or p_revision is null or p_revision<1
     or p_media is null or p_caption is null
     or p_scheduled_at is null or p_timezone is null then
    return false;
  end if;
  select * into j from public.social_publish_jobs
    where id=p_job and shop_id=p_shop for update;
  if not found or j.status<>'DRAFT'
     or j.provider not in ('instagram','youtube')
     or j.revision is distinct from p_revision
     or j.caption is distinct from p_caption
     or j.scheduled_at is distinct from p_scheduled_at
     or j.timezone is distinct from p_timezone
     or j.media_asset_id is distinct from p_media
     or j.approved_by is not null or j.approved_at is not null
     or j.approved_content_sha256 is not null
     or j.scheduled_at<=now()+interval '1 minute'
     or not exists (
       select 1 from public.shop_memberships m
       where m.shop_id=p_shop and m.user_id=p_actor
         and m.active and m.role in ('OWNER','EDITOR')
     ) or not exists (
       select 1 from public.shop_memberships m
       where m.shop_id=p_shop and m.user_id=j.requested_by
         and m.active and m.role in ('OWNER','EDITOR')
     ) or not exists (
       select 1 from public.campaign_days d
       where d.id=j.campaign_day_id and d.shop_id=p_shop
         and d.review_status='APPROVED'
     ) then return false; end if;
  -- The immutable revision/media SHA review is only one component of proof.
  -- A complete authorization also requires the prior *finalized render* SHA
  -- AND a separate append-only clearance matching the same reviewer/license.
  if not public.p2_social_video_review_bound(p_shop,p_job,p_source_sha)
     or not exists(
       select 1
       from retail_private.social_video_job_reviews v
       join retail_private.social_media_reviews proof
         on proof.shop_id=v.shop_id and proof.media_asset_id=v.media_asset_id
         and proof.source_sha256=v.source_sha256
         and proof.reviewed_by=v.reviewed_by
       join retail_private.social_render_byte_receipts receipt
         on receipt.shop_id=v.shop_id
         and receipt.media_asset_id=v.media_asset_id
         and receipt.source_sha256=v.source_sha256
       join public.media_assets media
         on media.id=v.media_asset_id and media.shop_id=v.shop_id
         and media.object_path=receipt.object_path
         and media.storage_bucket='retailgrowth-media'
         and media.mime_type='video/mp4' and media.source='GENERATED'
       join public.render_jobs render
         on render.id=receipt.render_job_id and render.shop_id=v.shop_id
         and render.output_asset_id=v.media_asset_id
         and render.day_id=j.campaign_day_id and render.status='SUCCEEDED'
         and render.preset='instagram_reel_30s'
       join retail_private.social_video_rights_clearances rights
         on rights.shop_id=v.shop_id
         and rights.job_id=v.job_id and rights.revision=v.revision
         and rights.media_asset_id=v.media_asset_id
         and rights.reviewed_by=v.reviewed_by
         and rights.rights_kind=proof.rights_kind
         and rights.rights_evidence_sha256=proof.rights_evidence_sha256
         and rights.rights_expires_at=proof.rights_expires_at
       join public.shop_memberships reviewer
         on reviewer.shop_id=v.shop_id and reviewer.user_id=v.reviewed_by
         and reviewer.active and reviewer.role in ('OWNER','EDITOR')
       join public.social_accounts acct
         on acct.id=j.social_account_id and acct.shop_id=j.shop_id
         and acct.provider=j.provider and acct.connection_status='CONNECTED'
         and ((j.provider='instagram'
                and 'instagram_content_publish'=any(acct.granted_scopes))
             or (j.provider='youtube'
                and 'youtube.upload'=any(acct.granted_scopes)))
       where v.job_id=j.id and v.shop_id=p_shop
         and v.media_asset_id=p_media and v.revision=p_revision
         and v.source_sha256=decode(p_source_sha,'hex')
         and proof.rights_expires_at is not null
         and proof.rights_expires_at>now()+interval '6 hours'
         and proof.rights_expires_at>j.scheduled_at+interval '6 hours'
         and proof.ffprobe->>'video_codec'='h264'
         and proof.ffprobe->>'audio_codec'='aac'
         and proof.ffprobe->>'pixel_format'='yuv420p'
         and proof.ffprobe->>'width'='1080'
         and proof.ffprobe->>'height'='1920'
         and (proof.ffprobe->>'duration_seconds')::numeric between 29 and 31
     ) then return false; end if;

  update public.social_publish_jobs
    set status='APPROVED',approved_by=p_actor,approved_at=now(),
        approved_content_sha256=decode(p_digest_hex,'hex'),updated_at=now()
    where id=p_job and shop_id=p_shop;
  -- Quota/active plan check is atomic: failure raises and rolls back approval.
  -- No default publish allowance; no user or provider side effects in this RPC.
  if not public.p2_reserve_social_publish_quota(p_shop,p_job) then
    raise exception 'reviewed video quota denied' using errcode='RG001';
  end if;
  insert into public.social_publish_audit(
    shop_id,job_id,actor_user_id,event_code)
  values(p_shop,p_job,p_actor,'SOCIAL_CONTENT_APPROVED');
  return true;
end
$$;

revoke all on function public.p2_approve_reviewed_video_job(
 uuid,uuid,uuid,integer,text,text,timestamptz,text,uuid,text)
 from public,anon,authenticated;
grant execute on function public.p2_approve_reviewed_video_job(
 uuid,uuid,uuid,integer,text,text,timestamptz,text,uuid,text)
 to service_role;
commit;
