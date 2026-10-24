-- Part2 video adapter state bridge, STAGED SOURCE ONLY. Do not apply hosted
-- without owner authorization; real OAuth+provider publishing remain disabled.
-- Requires pending P2 190000..191500 and their active claim invariants.
begin;

alter table retail_private.social_video_uploads
  add column youtube_session_key_version integer
  check (youtube_session_key_version is null or
         youtube_session_key_version between 1 and 2147483647);

-- A durable Meta container can be read only by its exact live send lease;
-- it is never a general user-visible media endpoint.
create function public.p2_video_container_for_claim(
  p_job uuid,p_claim uuid
) returns text language plpgsql security definer set search_path=''
as $$
declare value text;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'video receipt service only' using errcode='42501';
  end if;
  select v.remote_container_id into value
  from retail_private.social_video_uploads v
  join public.social_publish_jobs j on j.id=v.job_id
    and j.shop_id=v.shop_id and j.provider=v.provider
    and j.social_account_id=v.social_account_id
    and j.revision=v.revision
    and j.approved_content_sha256=v.approved_digest
    and j.media_asset_id=v.media_asset_id
  join retail_private.social_publish_attempts a
    on a.job_id=v.job_id and a.claim_token=v.claim_token
  join public.social_accounts acct
    on acct.id=j.social_account_id and acct.shop_id=j.shop_id
       and acct.connection_status='CONNECTED'
       and 'instagram_content_publish'=any(acct.granted_scopes)
  where v.job_id=p_job and v.claim_token=p_claim
    and v.provider='instagram' and j.status='SENDING'
    and v.stage in ('CONTAINER_KNOWN','PUBLISH_INTENT')
    and a.finished_at is null and a.result_code='EXTERNAL_INFLIGHT'
    and v.remote_container_id ~ '^[0-9]{1,32}$';
  return value;
end
$$;

-- Store AES-256-GCM session *and key version* atomically. No plaintext URL
-- is ever stored in the table, message, public API or logs.
create function public.p2_save_youtube_session(
  p_job uuid,p_claim uuid,p_cipher_hex text,p_version integer
) returns boolean language plpgsql security definer set search_path=''
as $$
declare worked boolean;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'video session service only' using errcode='42501';
  end if;
  if p_version is null or p_version<1 or
     p_cipher_hex !~ '^[0-9a-f]+$' or
     length(p_cipher_hex) not between 80 and 16384 or
     length(p_cipher_hex)%2<>0 then
    return false;
  end if;
  if not exists(
    select 1 from retail_private.social_video_uploads v
      join public.social_publish_jobs j on j.id=v.job_id
      join public.social_accounts acct on acct.id=j.social_account_id
        and acct.shop_id=j.shop_id and acct.provider='youtube'
        and acct.connection_status='CONNECTED'
        and 'youtube.upload'=any(acct.granted_scopes)
      where v.job_id=p_job and v.claim_token=p_claim
        and v.provider='youtube' and v.stage='INITIATED'
        and j.status='SENDING'
  ) then return false; end if;
  worked:=public.p2_advance_social_video_upload(
    p_job,p_claim,'INITIATED','SESSION_KNOWN',null,p_cipher_hex);
  if not worked then return false; end if;
  update retail_private.social_video_uploads
    set youtube_session_key_version=p_version
    where job_id=p_job and claim_token=p_claim
      and provider='youtube' and stage='SESSION_KNOWN';
  if not found then
    raise exception 'encrypted session state not durable' using errcode='23514';
  end if;
  return true;
end
$$;

create function public.p2_youtube_session_for_claim(
  p_job uuid,p_claim uuid
) returns jsonb language plpgsql security definer set search_path=''
as $$
declare context jsonb;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'video session service only' using errcode='42501';
  end if;
  select jsonb_build_object(
    'ciphertext_hex',encode(v.encrypted_session,'hex'),
    'key_version',v.youtube_session_key_version) into context
  from retail_private.social_video_uploads v
  join public.social_publish_jobs j on j.id=v.job_id
    and j.shop_id=v.shop_id and j.provider=v.provider
    and j.social_account_id=v.social_account_id
    and j.revision=v.revision
    and j.approved_content_sha256=v.approved_digest
  join retail_private.social_publish_attempts a
    on a.job_id=v.job_id and a.claim_token=v.claim_token
  join public.social_accounts acct
    on acct.id=j.social_account_id and acct.shop_id=j.shop_id
       and acct.connection_status='CONNECTED'
       and 'youtube.upload'=any(acct.granted_scopes)
  where v.job_id=p_job and v.claim_token=p_claim
    and v.provider='youtube' and j.status='SENDING'
    and v.stage in ('SESSION_KNOWN','BINARY_INTENT')
    and a.finished_at is null and a.result_code='EXTERNAL_INFLIGHT'
    and v.encrypted_session is not null
    and v.youtube_session_key_version>0;
  return context;
end
$$;

revoke all on function public.p2_video_container_for_claim(uuid,uuid)
 from public,anon,authenticated;
revoke all on function public.p2_save_youtube_session(uuid,uuid,text,integer)
 from public,anon,authenticated;
revoke all on function public.p2_youtube_session_for_claim(uuid,uuid)
 from public,anon,authenticated;
grant execute on function public.p2_video_container_for_claim(uuid,uuid)
 to service_role;
grant execute on function public.p2_save_youtube_session(uuid,uuid,text,integer)
 to service_role;
grant execute on function public.p2_youtube_session_for_claim(uuid,uuid)
 to service_role;
commit;
