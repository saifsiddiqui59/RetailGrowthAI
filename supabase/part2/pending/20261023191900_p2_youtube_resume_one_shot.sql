-- P2 YouTube resumable upload: ONE irreversible resume attempt per claim.
-- STAGED SOURCE ONLY; not deployed or registered in a live video worker.
-- Requires all pending Part2 migrations 190000..191800.
begin;

alter table retail_private.social_video_uploads
  add column youtube_resume_intent_at timestamptz,
  add column youtube_resume_next_byte bigint,
  add constraint p2_youtube_resume_offset_bounds check (
    (youtube_resume_intent_at is null and youtube_resume_next_byte is null)
    or (youtube_resume_intent_at is not null
        and youtube_resume_next_byte is not null
        and youtube_resume_next_byte >= 0
        and youtube_resume_next_byte < media_size
        and provider='youtube'));

create function public.p2_begin_youtube_resume(
  p_job uuid,p_claim uuid,p_next_byte bigint,
  p_size bigint,p_sha text
) returns boolean language plpgsql security definer set search_path=''
as $$
declare
  j public.social_publish_jobs%rowtype;
  v retail_private.social_video_uploads%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'YouTube resume service role only' using errcode='42501';
  end if;
  if p_claim is null or p_next_byte is null or p_size is null
     or p_size not between 1 and 83886080
     or p_next_byte<0 or p_next_byte>=p_size
     or p_sha is null or p_sha !~ '^[a-f0-9]{64}$' then
    return false;
  end if;
  -- Serialize cancellation, media-revision updates and competing workers.
  select * into j from public.social_publish_jobs
    where id=p_job for update;
  if not found or j.status<>'SENDING' or j.provider<>'youtube'
      or j.media_asset_id is null or j.approved_content_sha256 is null
      or not exists(
        select 1 from retail_private.social_publish_attempts a
        where a.job_id=p_job and a.claim_token=p_claim
         and a.finished_at is null and a.result_code='EXTERNAL_INFLIGHT'
      ) then return false; end if;
  select * into v from retail_private.social_video_uploads
    where job_id=p_job for update;
  if not found or v.provider<>'youtube'
      or v.stage<>'BINARY_INTENT'
      or v.youtube_resume_intent_at is not null
      or v.youtube_resume_next_byte is not null
      or v.claim_token is distinct from p_claim
      or v.shop_id<>j.shop_id
      or v.media_asset_id is distinct from j.media_asset_id
      or v.social_account_id<>j.social_account_id
      or v.revision<>j.revision
      or v.approved_digest is distinct from j.approved_content_sha256
      or v.source_sha256 is distinct from decode(p_sha,'hex')
      or v.media_size is distinct from p_size
      or v.encrypted_session is null
      or v.youtube_session_key_version is null
      or not public.p2_video_send_claim_valid(
         p_job,p_claim,j.revision,p_sha) then
    return false;
  end if;
  update retail_private.social_video_uploads set
    youtube_resume_intent_at=now(),
    youtube_resume_next_byte=p_next_byte,
    updated_at=now()
    where job_id=p_job and claim_token=p_claim
      and youtube_resume_intent_at is null
      and stage='BINARY_INTENT';
  return found;
end
$$;

revoke all on function public.p2_begin_youtube_resume(
 uuid,uuid,bigint,bigint,text) from public,anon,authenticated;
grant execute on function public.p2_begin_youtube_resume(
 uuid,uuid,bigint,bigint,text) to service_role;
commit;
