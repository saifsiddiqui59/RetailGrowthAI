-- Part2 PRIVATE video send claim context: SOURCE ONLY, unhosted.
-- Apply only after staged 190000..191700 under an approved release gate.
-- This RPC grants no HTTP/queue route; no live social posting is enabled.
begin;

create function public.p2_video_send_claim_context(p_job uuid,p_claim uuid)
returns jsonb language plpgsql security definer set search_path=''
as $$
declare
  result jsonb;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'video send context requires service role' using errcode='42501';
  end if;
  select jsonb_build_object(
      'shop_id',j.shop_id,'job_id',j.id,'claim_token',a.claim_token,
      'provider',j.provider,'media_asset_id',j.media_asset_id,
      'source_sha256',encode(b.source_sha256,'hex'),
      'source','PART1_RENDER_FINALIZED',
      'object_path',b.object_path,'storage_bucket',m.storage_bucket,
      'revision',j.revision,'status',j.status,
      'approved_digest',encode(j.approved_content_sha256,'hex'),
      'scheduled_at',j.scheduled_at,'rights_expires_at',rights.rights_expires_at,
      'rights_kind',rights.rights_kind,
      'rights_evidence_sha256',encode(rights.rights_evidence_sha256,'hex'),
      'connection_status',acct.connection_status,
      'granted_scopes',acct.granted_scopes,
      'social_account_id',acct.id,'provider_account_id',acct.provider_account_id,
      'caption',j.caption,
      -- YouTube title and description are derived from approved copy only.
      -- No non-approved textual metadata is supplied to the publisher.
      'title',left(j.caption,100),'description',j.caption,
      'access_ciphertext_hex',encode(credentials.access_token_ciphertext,'hex'),
      'key_version',credentials.encryption_key_version,
      'credential_expires_at',credentials.expires_at
  ) into result
  from public.social_publish_jobs j
  join retail_private.social_publish_attempts a
    on a.job_id=j.id and a.claim_token=p_claim
     and a.finished_at is null and a.result_code='EXTERNAL_INFLIGHT'
  join public.social_accounts acct
    on acct.id=j.social_account_id and acct.shop_id=j.shop_id
     and acct.provider=j.provider and acct.connection_status='CONNECTED'
  join retail_private.social_account_credentials credentials
    on credentials.social_account_id=acct.id
     and credentials.encryption_key_version>0
     and credentials.expires_at>now()+interval '90 seconds'
  join public.shop_memberships approver
    on approver.shop_id=j.shop_id and approver.user_id=j.approved_by
     and approver.active and approver.role in ('OWNER','EDITOR')
  join public.shop_subscriptions sub
    on sub.shop_id=j.shop_id and sub.status in ('TRIAL','ACTIVE')
     and now()>=sub.valid_from and now()<sub.valid_until
     and now()>=sub.period_start and now()<sub.period_end
  join retail_private.social_publish_quota_ledger quota
    on quota.publish_job_id=j.id and quota.shop_id=j.shop_id
     and quota.period_start=sub.period_start
  join retail_private.social_video_job_reviews v
    on v.job_id=j.id and v.shop_id=j.shop_id
     and v.media_asset_id=j.media_asset_id and v.revision=j.revision
  join public.shop_memberships reviewer
    on reviewer.shop_id=j.shop_id and reviewer.user_id=v.reviewed_by
     and reviewer.active and reviewer.role in ('OWNER','EDITOR')
  join retail_private.social_media_reviews review
    on review.shop_id=j.shop_id and review.media_asset_id=v.media_asset_id
     and review.reviewed_by=v.reviewed_by
     and review.source_sha256=v.source_sha256
     and review.rights_expires_at>now()+interval '6 hours'
     and review.rights_expires_at>j.scheduled_at+interval '6 hours'
     and review.ffprobe->>'video_codec'='h264'
     and review.ffprobe->>'audio_codec'='aac'
     and review.ffprobe->>'pixel_format'='yuv420p'
     and review.ffprobe->>'width'='1080'
     and review.ffprobe->>'height'='1920'
  join retail_private.social_render_byte_receipts b
    on b.shop_id=v.shop_id and b.media_asset_id=v.media_asset_id
     and b.source_sha256=v.source_sha256
  join retail_private.social_video_rights_clearances rights
    on rights.shop_id=j.shop_id and rights.job_id=j.id
     and rights.revision=j.revision and rights.media_asset_id=v.media_asset_id
     and rights.reviewed_by=v.reviewed_by
     and rights.rights_kind=review.rights_kind
     and rights.rights_evidence_sha256=review.rights_evidence_sha256
     and rights.rights_expires_at>now()+interval '6 hours'
     and rights.rights_expires_at>j.scheduled_at+interval '6 hours'
  join public.media_assets m
    on m.shop_id=j.shop_id and m.id=j.media_asset_id
     and m.object_path=b.object_path
     and m.storage_bucket='retailgrowth-media'
     and m.source='GENERATED' and m.mime_type='video/mp4'
  join public.render_jobs render
    on render.shop_id=j.shop_id and render.id=b.render_job_id
     and render.output_asset_id=m.id and render.day_id=j.campaign_day_id
     and render.status='SUCCEEDED' and render.preset='instagram_reel_30s'
  join public.campaign_days day
    on day.shop_id=j.shop_id and day.id=j.campaign_day_id
     and day.review_status='APPROVED'
  where j.id=p_job and j.status='SENDING'
    and j.provider in ('instagram','youtube')
    and ((j.provider='instagram'
           and 'instagram_content_publish'=any(acct.granted_scopes))
      or (j.provider='youtube'
           and 'youtube.upload'=any(acct.granted_scopes)))
    and j.approved_by is not null and j.approved_at is not null
    and j.approved_content_sha256 is not null
    and j.scheduled_at<=now()
    and j.media_asset_id is not null
    and j.revision>0
    and v.source_sha256=b.source_sha256
    and public.p2_social_video_review_bound(j.shop_id,j.id,encode(b.source_sha256,'hex'));
  return result;
end
$$;

-- Always recheck the same active immutable revision and byte SHA before
-- any irreversible provider intent, not just when the worker first starts.
create function public.p2_video_send_claim_valid(
  p_job uuid,p_claim uuid,p_revision integer,p_source_sha text
) returns boolean language plpgsql security definer set search_path=''
as $$
declare verified jsonb;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'video send authority service only' using errcode='42501';
  end if;
  if p_revision is null or p_revision<1
     or p_source_sha is null or p_source_sha !~ '^[0-9a-f]{64}$' then
    return false;
  end if;
  verified:=public.p2_video_send_claim_context(p_job,p_claim);
  return coalesce(verified->>'source_sha256'=p_source_sha
    and (verified->>'revision')::integer=p_revision,false);
end
$$;

revoke all on function public.p2_video_send_claim_context(uuid,uuid)
  from public,anon,authenticated;
revoke all on function public.p2_video_send_claim_valid(uuid,uuid,integer,text)
  from public,anon,authenticated;
grant execute on function public.p2_video_send_claim_context(uuid,uuid)
  to service_role;
grant execute on function public.p2_video_send_claim_valid(uuid,uuid,integer,text)
  to service_role;
commit;
