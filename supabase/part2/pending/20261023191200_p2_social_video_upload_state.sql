-- Durable P2 video provider side-effect state, SOURCE ONLY, no live worker.
-- Requires staged Part2 migrations through 20261023191100; do not deploy
-- without separate owner approval and a verified immutable-media send path.
begin;

create table retail_private.social_video_uploads (
  job_id uuid primary key,
  shop_id uuid not null,
  media_asset_id uuid not null,
  social_account_id uuid not null,
  provider text not null check(provider in ('instagram','youtube')),
  claim_token uuid not null,
  revision integer not null check(revision>0),
  approved_digest bytea not null check(octet_length(approved_digest)=32),
  source_sha256 bytea not null check(octet_length(source_sha256)=32),
  media_size bigint not null check(media_size between 1 and 83886080),
  stage text not null default 'INITIATED' check(stage in (
    'INITIATED','CONTAINER_KNOWN','PUBLISH_INTENT','SESSION_KNOWN',
    'BINARY_INTENT','RECONCILE','PUBLISHED')),
  remote_container_id text,
  encrypted_session bytea,
  remote_post_id text,
  updated_at timestamptz not null default now(),
  foreign key(shop_id,job_id) references public.social_publish_jobs(shop_id,id)
    on delete cascade,
  foreign key(shop_id,media_asset_id) references public.media_assets(shop_id,id)
    on delete cascade,
  foreign key(shop_id,social_account_id,provider)
    references public.social_accounts(shop_id,id,provider)
);
alter table retail_private.social_video_uploads enable row level security;
revoke all on retail_private.social_video_uploads from public,anon,authenticated;
grant select,insert,update on retail_private.social_video_uploads to service_role;

-- Record the uncertain remote-create intent BEFORE issuing POST to provider.
-- Duplicate queue messages cannot start a second external create operation.
create function public.p2_begin_social_video_upload(
  p_job uuid,p_claim uuid,p_sha text,p_size bigint
) returns boolean language plpgsql security definer set search_path=''
as $$
declare j public.social_publish_jobs%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'service-only upload intent' using errcode='42501';
  end if;
  if p_sha is null or p_sha !~ '^[0-9a-f]{64}$'
      or p_size is null or p_size not between 1 and 83886080
  then return false; end if;
  select * into j from public.social_publish_jobs
    where id=p_job for update;
  if not found or j.status<>'SENDING'
     or j.provider not in ('instagram','youtube')
     or j.approved_content_sha256 is null or j.media_asset_id is null
     or not exists (
       select 1 from retail_private.social_publish_attempts a
        where a.job_id=p_job and a.claim_token=p_claim
          and a.finished_at is null and a.result_code='EXTERNAL_INFLIGHT'
     ) or not public.p2_social_video_review_bound(j.shop_id,p_job,p_sha)
     or not exists (
       select 1 from retail_private.social_publish_quota_ledger l
       where l.shop_id=j.shop_id and l.publish_job_id=j.id
     ) then return false; end if;
  insert into retail_private.social_video_uploads(
    job_id,shop_id,media_asset_id,social_account_id,provider,
    claim_token,revision,approved_digest,source_sha256,media_size)
  values(j.id,j.shop_id,j.media_asset_id,j.social_account_id,j.provider,
    p_claim,j.revision,j.approved_content_sha256,decode(p_sha,'hex'),p_size)
  on conflict(job_id) do nothing;
  return found;
end
$$;

-- Every provider-visible side effect is preceded by a persisted stage CAS.
-- A lost response never resets this record or authorizes a second POST/PUT.
create function public.p2_advance_social_video_upload(
  p_job uuid,p_claim uuid,p_from text,p_to text,
  p_remote text default null,p_session_hex text default null
) returns boolean language plpgsql security definer set search_path=''
as $$
declare
  j public.social_publish_jobs%rowtype;
  v retail_private.social_video_uploads%rowtype;
  allowed boolean:=false;
  finished boolean;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'service-only upload state' using errcode='42501';
  end if;
  select * into j from public.social_publish_jobs where id=p_job for update;
  if not found or j.status<>'SENDING' then return false; end if;
  select * into v from retail_private.social_video_uploads
    where job_id=p_job for update;
  if not found or v.stage is distinct from p_from
     or v.claim_token is distinct from p_claim
     or v.shop_id<>j.shop_id or v.media_asset_id is distinct from j.media_asset_id
     or v.social_account_id<>j.social_account_id
     or v.provider<>j.provider or v.revision<>j.revision
     or v.approved_digest is distinct from j.approved_content_sha256
     or not exists (
       select 1 from retail_private.social_publish_attempts a
       where a.job_id=p_job and a.claim_token=p_claim
         and a.finished_at is null and a.result_code='EXTERNAL_INFLIGHT'
     ) then return false; end if;
  if p_to='RECONCILE' and p_from in (
       'INITIATED','CONTAINER_KNOWN','PUBLISH_INTENT',
       'SESSION_KNOWN','BINARY_INTENT')
       and p_remote is null and p_session_hex is null then
    allowed:=true;
  elsif v.provider='instagram' then
    allowed:=(p_from='INITIATED' and p_to='CONTAINER_KNOWN'
                and p_remote ~ '^[0-9]{1,32}$'
                and p_session_hex is null)
          or (p_from='CONTAINER_KNOWN' and p_to='PUBLISH_INTENT'
                and p_remote is null and p_session_hex is null)
          or (p_from='PUBLISH_INTENT' and p_to='PUBLISHED'
                and p_remote ~ '^[0-9]{1,32}$'
                and p_session_hex is null);
  elsif v.provider='youtube' then
    allowed:=(p_from='INITIATED' and p_to='SESSION_KNOWN'
                and p_remote is null and p_session_hex ~ '^[0-9a-f]+
          or (p_from='SESSION_KNOWN' and p_to='BINARY_INTENT'
                and p_remote is null and p_session_hex is null)
          or (p_from='BINARY_INTENT' and p_to='PUBLISHED'
                and p_remote ~ '^[A-Za-z0-9_-]{11}$'
                and p_session_hex is null);
  end if;
  if not coalesce(allowed,false) then return false; end if;
  update retail_private.social_video_uploads set
    stage=p_to,
    remote_container_id=case when p_to='CONTAINER_KNOWN'
       then p_remote else remote_container_id end,
    encrypted_session=case when p_to='SESSION_KNOWN'
       then decode(p_session_hex,'hex') else encrypted_session end,
    remote_post_id=case when p_to='PUBLISHED'
       then p_remote else remote_post_id end,
    updated_at=now()
    where job_id=p_job;
  if p_to='PUBLISHED' then
    finished:=public.p2_finish_social_publish(
      p_job,p_claim,'PUBLISHED',null,p_remote);
    if not finished then
      raise exception 'receipt CAS refused' using errcode='23514';
    end if;
  elsif p_to='RECONCILE' then
    finished:=public.p2_finish_social_publish(
      p_job,p_claim,'RECONCILE','AMBIGUOUS_MEDIA',null);
    if not finished then
      raise exception 'reconciliation CAS refused' using errcode='23514';
    end if;
  end if;
  return true;
end
$$;

-- Only exact live private claim can read encrypted YouTube upload session.
-- No plaintext URL, signed media URL or browser exposure.
create function public.p2_video_session_ciphertext(p_job uuid,p_claim uuid)
returns text language plpgsql security definer set search_path=''
as $$
declare c text;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'service-only upload session' using errcode='42501';
  end if;
  select encode(v.encrypted_session,'hex') into c
  from retail_private.social_video_uploads v
  join public.social_publish_jobs j on j.id=v.job_id
  join retail_private.social_publish_attempts a
    on a.job_id=v.job_id and a.claim_token=v.claim_token
  where v.job_id=p_job and v.claim_token=p_claim
    and v.provider='youtube' and v.stage in ('SESSION_KNOWN','BINARY_INTENT')
    and j.status='SENDING' and a.finished_at is null
    and a.result_code='EXTERNAL_INFLIGHT';
  return c;
end
$$;

revoke all on function public.p2_begin_social_video_upload(uuid,uuid,text,bigint)
  from public,anon,authenticated;
revoke all on function public.p2_advance_social_video_upload(uuid,uuid,text,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_video_session_ciphertext(uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_begin_social_video_upload(uuid,uuid,text,bigint)
  to service_role;
grant execute on function public.p2_advance_social_video_upload(uuid,uuid,text,text,text,text)
  to service_role;
grant execute on function public.p2_video_session_ciphertext(uuid,uuid)
  to service_role;
commit;

                and length(p_session_hex) between 80 and 16384
                and length(p_session_hex)%2=0)
          or (p_from='SESSION_KNOWN' and p_to='BINARY_INTENT'
                and p_remote is null and p_session_hex is null)
          or (p_from='BINARY_INTENT' and p_to='PUBLISHED'
                and p_remote ~ '^[A-Za-z0-9_-]{11}$'
                and p_session_hex is null);
  end if;
  if not coalesce(allowed,false) then return false; end if;
  update retail_private.social_video_uploads set
    stage=p_to,
    remote_container_id=case when p_to='CONTAINER_KNOWN'
       then p_remote else remote_container_id end,
    encrypted_session=case when p_to='SESSION_KNOWN'
       then decode(p_session_hex,'hex') else encrypted_session end,
    remote_post_id=case when p_to='PUBLISHED'
       then p_remote else remote_post_id end,
    updated_at=now()
    where job_id=p_job;
  if p_to='PUBLISHED' then
    finished:=public.p2_finish_social_publish(
      p_job,p_claim,'PUBLISHED',null,p_remote);
    if not finished then
      raise exception 'receipt CAS refused' using errcode='23514';
    end if;
  elsif p_to='RECONCILE' then
    finished:=public.p2_finish_social_publish(
      p_job,p_claim,'RECONCILE','AMBIGUOUS_MEDIA',null);
    if not finished then
      raise exception 'reconciliation CAS refused' using errcode='23514';
    end if;
  end if;
  return true;
end
$$;

-- Only exact live private claim can read encrypted YouTube upload session.
-- No plaintext URL, signed media URL or browser exposure.
create function public.p2_video_session_ciphertext(p_job uuid,p_claim uuid)
returns text language plpgsql security definer set search_path=''
as $$
declare c text;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'service-only upload session' using errcode='42501';
  end if;
  select encode(v.encrypted_session,'hex') into c
  from retail_private.social_video_uploads v
  join public.social_publish_jobs j on j.id=v.job_id
  join retail_private.social_publish_attempts a
    on a.job_id=v.job_id and a.claim_token=v.claim_token
  where v.job_id=p_job and v.claim_token=p_claim
    and v.provider='youtube' and v.stage in ('SESSION_KNOWN','BINARY_INTENT')
    and j.status='SENDING' and a.finished_at is null
    and a.result_code='EXTERNAL_INFLIGHT';
  return c;
end
$$;

revoke all on function public.p2_begin_social_video_upload(uuid,uuid,text,bigint)
  from public,anon,authenticated;
revoke all on function public.p2_advance_social_video_upload(uuid,uuid,text,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_video_session_ciphertext(uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_begin_social_video_upload(uuid,uuid,text,bigint)
  to service_role;
grant execute on function public.p2_advance_social_video_upload(uuid,uuid,text,text,text,text)
  to service_role;
grant execute on function public.p2_video_session_ciphertext(uuid,uuid)
  to service_role;
commit;
