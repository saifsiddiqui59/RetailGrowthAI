-- Part 2 immutable job/revision binding for reviewed tenant-generated video.
-- STAGED SOURCE ONLY; no hosted migration or actual video publish activation.
-- Must run after P2 190000..191000 and the existing private media reviews.
begin;

create table retail_private.social_video_job_reviews (
  job_id uuid primary key,
  shop_id uuid not null,
  media_asset_id uuid not null,
  revision integer not null check(revision>0),
  source_sha256 bytea not null check(octet_length(source_sha256)=32),
  reviewed_by uuid not null references auth.users(id),
  recorded_at timestamptz not null default now(),
  foreign key(shop_id,job_id) references public.social_publish_jobs(shop_id,id)
    on delete cascade,
  foreign key(shop_id,media_asset_id) references public.media_assets(shop_id,id)
    on delete cascade
);
alter table retail_private.social_video_job_reviews enable row level security;
revoke all on retail_private.social_video_job_reviews from public,anon,authenticated;
grant select,insert,update,delete on retail_private.social_video_job_reviews
  to service_role;

-- Only a successful existing Part1 render output for this EXACT campaign
-- day can be offered for video review. Untrusted arbitrary client asset IDs,
-- user uploads, other shops' outputs and unrelated render media are excluded.
create function public.p2_social_video_source(
  p_shop uuid,p_job uuid,p_actor uuid
) returns jsonb language plpgsql security definer set search_path=''
as $$
declare
  j public.social_publish_jobs%rowtype;
  a public.media_assets%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'service role only' using errcode='42501';
  end if;
  select * into j from public.social_publish_jobs
    where id=p_job and shop_id=p_shop;
  if not found or j.provider not in ('instagram','youtube')
     or j.status<>'DRAFT' or j.approved_at is not null
     or j.approved_content_sha256 is not null or j.media_asset_id is null
     or not exists (
       select 1 from public.shop_memberships m
         where m.shop_id=p_shop and m.user_id=p_actor
           and m.active and m.role in ('OWNER','EDITOR')
     ) or not exists (
       select 1 from public.campaign_days d
         where d.id=j.campaign_day_id and d.shop_id=p_shop
           and d.review_status='APPROVED'
     ) or not exists (
       select 1 from public.social_accounts s
         where s.id=j.social_account_id and s.shop_id=p_shop
           and s.provider=j.provider and s.connection_status='CONNECTED'
           and ((j.provider='instagram' and 'instagram_content_publish'=any(s.granted_scopes))
             or (j.provider='youtube' and 'youtube.upload'=any(s.granted_scopes)))
     ) then return null; end if;

  select * into a from public.media_assets
    where id=j.media_asset_id and shop_id=p_shop
      and source='GENERATED' and mime_type='video/mp4'
      and storage_bucket='retailgrowth-media'
      and object_path like p_shop::text||'/renders/%'
      and license_name='owned'
      and nullif(btrim(coalesce(attribution,'')),'') is not null;
  if not found or not exists (
      select 1 from public.render_jobs r
        where r.shop_id=p_shop and r.day_id=j.campaign_day_id
          and r.output_asset_id=a.id and r.status='SUCCEEDED'
          and r.preset='instagram_reel_30s'
     ) then return null; end if;
  return jsonb_build_object(
    'shop_id',p_shop,'job_id',j.id,'revision',j.revision,
    'media_asset_id',a.id,'object_path',a.object_path,
    'storage_bucket',a.storage_bucket,'source','GENERATED');
end
$$;

-- Server must already have fetched the returned private object and run real
-- FFprobe/byte SHA plus independently verified rights. This DB RPC binds that
-- evidence to the current exact DRAFT, not to a reusable asset-only approval.
create function public.p2_bind_social_video_review(
  p_shop uuid,p_job uuid,p_actor uuid,p_revision integer,p_sha text
) returns boolean language plpgsql security definer set search_path=''
as $$
declare
  j public.social_publish_jobs%rowtype;
  review retail_private.social_media_reviews%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'service role only' using errcode='42501';
  end if;
  if p_sha is null or p_sha !~ '^[0-9a-f]{64}$'
     or p_revision is null or p_revision<1 then return false; end if;
  select * into j from public.social_publish_jobs
    where id=p_job and shop_id=p_shop for update;
  if not found or j.status<>'DRAFT' or j.revision<>p_revision
     or j.media_asset_id is null
     or public.p2_social_video_source(p_shop,p_job,p_actor) is null
  then return false; end if;
  select * into review from retail_private.social_media_reviews r
    where r.shop_id=p_shop and r.media_asset_id=j.media_asset_id
      and r.source_sha256=decode(p_sha,'hex')
      and (r.rights_expires_at is null
           or r.rights_expires_at>j.scheduled_at+interval '1 hour')
    for update;
  if not found or not public.p2_social_media_is_reviewed(
      p_shop,j.media_asset_id) then return false; end if;
  insert into retail_private.social_video_job_reviews(
    job_id,shop_id,media_asset_id,revision,source_sha256,reviewed_by)
  values(p_job,p_shop,j.media_asset_id,p_revision,decode(p_sha,'hex'),p_actor)
  on conflict(job_id) do update
    set revision=excluded.revision,media_asset_id=excluded.media_asset_id,
        source_sha256=excluded.source_sha256,reviewed_by=excluded.reviewed_by,
        recorded_at=now();
  return true;
end
$$;

-- This is an evidence/readiness check, NOT authorization for outbound media
-- transfer. A trusted worker must re-fetch and verify the exact private object
-- against the pinned digest immediately before issuing a signed URL or upload.
create function public.p2_social_video_review_bound(
  p_shop uuid,p_job uuid,p_sha text
) returns boolean language plpgsql security definer set search_path=''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'service role only' using errcode='42501';
  end if;
  if p_sha is null or p_sha !~ '^[0-9a-f]{64}$' then return false; end if;
  return exists(
    select 1 from retail_private.social_video_job_reviews v
    join public.social_publish_jobs j
      on j.id=v.job_id and j.shop_id=v.shop_id
    join retail_private.social_media_reviews r
      on r.shop_id=v.shop_id and r.media_asset_id=v.media_asset_id
    join public.social_accounts a
      on a.shop_id=j.shop_id and a.id=j.social_account_id
        and a.provider=j.provider and a.connection_status='CONNECTED'
    join public.render_jobs render
      on render.shop_id=j.shop_id and render.day_id=j.campaign_day_id
        and render.output_asset_id=v.media_asset_id
        and render.status='SUCCEEDED'
    join public.shop_memberships m
      on m.shop_id=v.shop_id and m.user_id=v.reviewed_by
       and m.active and m.role in ('OWNER','EDITOR')
    where v.shop_id=p_shop and v.job_id=p_job
      and j.status in ('DRAFT','APPROVED','QUEUED','RETRYABLE','SENDING')
      and j.media_asset_id=v.media_asset_id and j.revision=v.revision
      and j.provider in ('instagram','youtube')
      and ((j.provider='instagram' and 'instagram_content_publish'=any(a.granted_scopes))
         or (j.provider='youtube' and 'youtube.upload'=any(a.granted_scopes)))
      and v.source_sha256=decode(p_sha,'hex')
      and r.source_sha256=v.source_sha256
      and (r.rights_expires_at is null
           or r.rights_expires_at>j.scheduled_at+interval '1 hour')
      and r.ffprobe->>'video_codec'='h264'
      and r.ffprobe->>'audio_codec'='aac'
      and r.ffprobe->>'pixel_format'='yuv420p'
  );
end
$$;
revoke all on function public.p2_social_video_source(uuid,uuid,uuid)
  from public,anon,authenticated;
revoke all on function public.p2_bind_social_video_review(uuid,uuid,uuid,integer,text)
  from public,anon,authenticated;
revoke all on function public.p2_social_video_review_bound(uuid,uuid,text)
  from public,anon,authenticated;
grant execute on function public.p2_social_video_source(uuid,uuid,uuid)
  to service_role;
grant execute on function public.p2_bind_social_video_review(uuid,uuid,uuid,integer,text)
  to service_role;
grant execute on function public.p2_social_video_review_bound(uuid,uuid,text)
  to service_role;
commit;
