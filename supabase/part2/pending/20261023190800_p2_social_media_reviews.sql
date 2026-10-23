-- P2 independent video rights/FFprobe attestation, SOURCE ONLY.
-- These records DO NOT enable video approval or publishing by themselves.
-- Apply to hosted Supabase ONLY under separate owner approval.
begin;

create table retail_private.social_media_reviews (
  shop_id uuid not null,
  media_asset_id uuid not null,
  reviewed_by uuid not null references auth.users(id),
  source_sha256 bytea not null check(octet_length(source_sha256)=32),
  rights_evidence_sha256 bytea not null check(octet_length(rights_evidence_sha256)=32),
  rights_kind text not null check(rights_kind in
    ('OWNER_ATTESTED','STOCK_LICENSE_VERIFIED','GENERATED_RIGHTS_VERIFIED')),
  ffprobe jsonb not null,
  reviewed_at timestamptz not null default now(),
  rights_expires_at timestamptz,
  primary key(shop_id,media_asset_id),
  foreign key(shop_id,media_asset_id) references public.media_assets(shop_id,id)
    on delete cascade
);

alter table retail_private.social_media_reviews enable row level security;
revoke all on retail_private.social_media_reviews from public,anon,authenticated;
grant select,insert,update,delete on retail_private.social_media_reviews to service_role;

create function public.p2_record_social_media_review(
  p_shop uuid,p_asset uuid,p_actor uuid,p_source_sha text,
  p_evidence_sha text,p_kind text,p_probe jsonb,p_expires timestamptz
) returns boolean language plpgsql security definer set search_path=''
as $$
declare
  a public.media_assets%rowtype;
  n numeric;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'service-only media rights review' using errcode='42501';
  end if;
  if p_kind not in ('OWNER_ATTESTED','STOCK_LICENSE_VERIFIED',
                    'GENERATED_RIGHTS_VERIFIED')
      or p_source_sha !~ '^[0-9a-f]{64}$'
      or p_evidence_sha !~ '^[0-9a-f]{64}$'
      or p_probe is null or jsonb_typeof(p_probe)<>'object'
      or length(p_probe::text)>4096
      or (p_expires is not null and p_expires<=now())
      or p_probe->>'container' not in ('mp4','mov,mp4,m4a,3gp,3g2,mj2')
      or p_probe->>'video_codec'<>'h264'
      or p_probe->>'pixel_format'<>'yuv420p'
      or p_probe->>'width'<>'1080'
      or p_probe->>'height'<>'1920'
      or p_probe->>'duration_seconds' !~ '^[0-9]{1,3}([.][0-9]{1,3})?$'
      then raise exception 'invalid license/ffprobe evidence' using errcode='22023';
  end if;
  n := (p_probe->>'duration_seconds')::numeric;
  if n<29 or n>31 then
    raise exception 'unreviewed video duration' using errcode='22023';
  end if;
  if not exists(
      select 1 from public.shop_memberships m
      where m.shop_id=p_shop and m.user_id=p_actor and m.active
        and m.role in ('OWNER','EDITOR')
     ) then return false; end if;
  select * into a from public.media_assets
    where id=p_asset and shop_id=p_shop
      and mime_type='video/mp4' and storage_bucket='retailgrowth-media';
  if not found then return false; end if;
  -- Material rights evidence is a 32-byte digest of a reviewed license or
  -- owner's explicit attestation; no inference from a generated file alone.
  insert into retail_private.social_media_reviews(
    shop_id,media_asset_id,reviewed_by,source_sha256,
    rights_evidence_sha256,rights_kind,ffprobe,rights_expires_at)
  values(p_shop,p_asset,p_actor,decode(p_source_sha,'hex'),
         decode(p_evidence_sha,'hex'),p_kind,p_probe,p_expires)
  on conflict(shop_id,media_asset_id) do update
    set reviewed_by=excluded.reviewed_by,source_sha256=excluded.source_sha256,
        rights_evidence_sha256=excluded.rights_evidence_sha256,
        rights_kind=excluded.rights_kind,ffprobe=excluded.ffprobe,
        rights_expires_at=excluded.rights_expires_at,reviewed_at=now();
  return true;
end
$$;

create function public.p2_social_media_is_reviewed(p_shop uuid,p_asset uuid)
returns boolean language plpgsql security definer set search_path=''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only media review lookup' using errcode='42501';
  end if;
  return exists(
    select 1 from retail_private.social_media_reviews r
    join public.media_assets a on a.id=r.media_asset_id and a.shop_id=r.shop_id
    join public.shop_memberships m
      on m.shop_id=r.shop_id and m.user_id=r.reviewed_by and m.active
      and m.role in ('OWNER','EDITOR')
    where r.shop_id=p_shop and r.media_asset_id=p_asset
      and a.mime_type='video/mp4' and a.storage_bucket='retailgrowth-media'
      and (r.rights_expires_at is null or r.rights_expires_at>now())
      and octet_length(r.rights_evidence_sha256)=32
      and octet_length(r.source_sha256)=32
  );
end
$$;

revoke all on function public.p2_record_social_media_review(
  uuid,uuid,uuid,text,text,text,jsonb,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_social_media_is_reviewed(uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_record_social_media_review(
  uuid,uuid,uuid,text,text,text,jsonb,timestamptz) to service_role;
grant execute on function public.p2_social_media_is_reviewed(uuid,uuid) to service_role;
commit;
