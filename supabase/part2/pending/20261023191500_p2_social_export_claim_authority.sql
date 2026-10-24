-- Part2 staged source only: immutable Instagram export proof + lease CAS.
-- Requires approved P2 migrations 190000..191400, no hosted auto-apply.
-- This RPC is a prerequisite for a service-only media export, NOT a publish
-- authorization or social platform API adapter by itself.
begin;
create function public.p2_can_export_social_video(
  p_shop uuid,p_job uuid,p_claim uuid,p_revision integer,p_sha text
) returns boolean language plpgsql security definer set search_path=''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'export authority service only' using errcode='42501';
  end if;
  if p_sha is null or p_sha !~ '^[0-9a-f]{64}$'
     or p_revision is null or p_revision<1
     or p_shop is null or p_job is null or p_claim is null
  then return false; end if;
  return exists(
    select 1
    from public.social_publish_jobs j
    join public.social_accounts acct
      on acct.id=j.social_account_id and acct.shop_id=j.shop_id
        and acct.provider=j.provider and acct.connection_status='CONNECTED'
        and 'instagram_content_publish'=any(acct.granted_scopes)
    join retail_private.social_publish_attempts attempt
      on attempt.job_id=j.id and attempt.claim_token=p_claim
        and attempt.finished_at is null
        and attempt.result_code='EXTERNAL_INFLIGHT'
    join retail_private.social_publish_quota_ledger l
      on l.publish_job_id=j.id and l.shop_id=j.shop_id
    join public.shop_subscriptions subscription
      on subscription.shop_id=j.shop_id
         and subscription.period_start=l.period_start
         and subscription.status in ('TRIAL','ACTIVE')
         and now()>=subscription.valid_from
         and now()<subscription.valid_until
         and now()>=subscription.period_start
         and now()<subscription.period_end
    join retail_private.social_video_job_reviews v
      on v.job_id=j.id and v.shop_id=j.shop_id
        and v.media_asset_id=j.media_asset_id and v.revision=j.revision
        and v.source_sha256=decode(p_sha,'hex')
    join retail_private.social_media_reviews review
      on review.shop_id=j.shop_id and review.media_asset_id=v.media_asset_id
        and review.source_sha256=v.source_sha256
        and review.rights_expires_at>now()+interval '6 hours'
        and review.ffprobe->>'video_codec'='h264'
        and review.ffprobe->>'audio_codec'='aac'
        and review.ffprobe->>'pixel_format'='yuv420p'
    join retail_private.social_render_byte_receipts render_receipt
      on render_receipt.shop_id=j.shop_id
        and render_receipt.media_asset_id=v.media_asset_id
        and render_receipt.source_sha256=v.source_sha256
    join public.media_assets media
      on media.id=v.media_asset_id and media.shop_id=j.shop_id
        and media.object_path=render_receipt.object_path
        and media.source='GENERATED' and media.mime_type='video/mp4'
        and media.storage_bucket='retailgrowth-media'
    join retail_private.social_video_rights_clearances rights
      on rights.job_id=j.id and rights.shop_id=j.shop_id
        and rights.revision=j.revision
        and rights.media_asset_id=v.media_asset_id
        and rights.rights_evidence_sha256=review.rights_evidence_sha256
        and rights.rights_expires_at>now()+interval '6 hours'
    join public.shop_memberships approver
      on approver.shop_id=j.shop_id and approver.user_id=j.approved_by
        and approver.active and approver.role in ('OWNER','EDITOR')
    join public.shop_memberships reviewer
      on reviewer.shop_id=j.shop_id and reviewer.user_id=v.reviewed_by
        and reviewer.active and reviewer.role in ('OWNER','EDITOR')
    where j.id=p_job and j.shop_id=p_shop and j.provider='instagram'
      and j.status='SENDING' and j.revision=p_revision
      and j.approved_content_sha256 is not null
      and j.approved_at is not null
      and j.scheduled_at<=now()
      and not exists(
        select 1 from retail_private.social_video_uploads u
        where u.job_id=j.id and u.stage<>'INITIATED'
      )
  );
end
$$;
revoke all on function public.p2_can_export_social_video(uuid,uuid,uuid,integer,text)
  from public,anon,authenticated;
grant execute on function public.p2_can_export_social_video(uuid,uuid,uuid,integer,text)
  to service_role;
commit;
