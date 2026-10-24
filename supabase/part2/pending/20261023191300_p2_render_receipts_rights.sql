-- Part 2 source-only immutable evidence ledger for existing Part1 rendered MP4.
-- Apply AFTER P2 190000..191200 under explicit hosted migration approval.
-- No trigger, worker, browser or live provider publishing is activated.
begin;

create table retail_private.social_render_byte_receipts(
  shop_id uuid not null,
  media_asset_id uuid not null,
  render_job_id uuid not null,
  object_path text not null,
  source_sha256 bytea not null check(octet_length(source_sha256)=32),
  recorded_at timestamptz not null default now(),
  primary key(shop_id,media_asset_id),
  foreign key(shop_id,media_asset_id)
    references public.media_assets(shop_id,id) on delete cascade,
  foreign key(shop_id,render_job_id)
    references public.render_jobs(shop_id,id) on delete cascade,
  unique(shop_id,render_job_id)
);
alter table retail_private.social_render_byte_receipts enable row level security;
revoke all on retail_private.social_render_byte_receipts from public,anon,authenticated;
-- Append-only: no general UPDATE or DELETE grant, including to service_role.
grant select,insert on retail_private.social_render_byte_receipts to service_role;

-- Only an internal service that has personally read, hashed and verified the
-- completed rendered source may call this. NEVER expose from a user endpoint.
-- The database enforces exact successful render + tenant object lineage and
-- refuses a later attempt to replace a stored render SHA.
create function public.p2_record_finalized_render_digest(
  p_shop uuid,p_render uuid,p_asset uuid,p_digest text
) returns boolean language plpgsql security definer set search_path=''
as $$
declare
  a public.media_assets%rowtype;
  r public.render_jobs%rowtype;
  existing bytea;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'render digest service only' using errcode='42501';
  end if;
  if p_digest is null or p_digest !~ '^[0-9a-f]{64}$' then return false; end if;
  select * into r from public.render_jobs
    where id=p_render and shop_id=p_shop
      and status='SUCCEEDED' and output_asset_id=p_asset
      and preset='instagram_reel_30s';
  if not found then return false; end if;
  select * into a from public.media_assets
    where id=p_asset and shop_id=p_shop and mime_type='video/mp4'
      and source='GENERATED' and storage_bucket='retailgrowth-media'
      and license_name='owned';
  if not found or a.object_path is null or
       a.object_path not like (p_shop::text||'/renders/'||p_render::text||'%')
      or (a.object_path <> p_shop::text||'/renders/'||p_render::text||'.mp4'
          and a.object_path !~ (
            '^'||p_shop::text||'/renders/'||p_render::text||
            '/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}[.]mp4$'))
  then return false; end if;
  insert into retail_private.social_render_byte_receipts(
     shop_id,media_asset_id,render_job_id,object_path,source_sha256)
  values(p_shop,p_asset,p_render,a.object_path,decode(p_digest,'hex'))
  on conflict do nothing;
  select b.source_sha256 into existing
    from retail_private.social_render_byte_receipts b
    where b.shop_id=p_shop and b.media_asset_id=p_asset
      and b.render_job_id=p_render and b.object_path=a.object_path;
  return existing=decode(p_digest,'hex');
end
$$;

-- This server-only lookup extends the previously reviewed candidate RPC
-- with scheduling CAS context, but NEVER accepts a media path from the caller.
create function public.p2_social_video_review_candidate(
  p_shop uuid,p_job uuid,p_actor uuid
) returns jsonb language plpgsql security definer set search_path=''
as $$
declare candidate jsonb; j public.social_publish_jobs%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'video candidate service only' using errcode='42501';
  end if;
  candidate:=public.p2_social_video_source(p_shop,p_job,p_actor);
  if candidate is null then return null; end if;
  select * into j from public.social_publish_jobs
    where id=p_job and shop_id=p_shop and status='DRAFT';
  if not found or not exists(
    select 1 from retail_private.social_render_byte_receipts b
      where b.shop_id=p_shop and b.media_asset_id=j.media_asset_id
        and b.object_path=candidate->>'object_path'
  ) then return null; end if;
  return candidate || jsonb_build_object('scheduled_at',j.scheduled_at);
end
$$;

create function public.p2_social_video_render_receipt(
  p_shop uuid,p_job uuid,p_actor uuid
) returns jsonb language plpgsql security definer set search_path=''
as $$
declare candidate jsonb; b retail_private.social_render_byte_receipts%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'render receipt service only' using errcode='42501';
  end if;
  candidate:=public.p2_social_video_review_candidate(p_shop,p_job,p_actor);
  if candidate is null then return null; end if;
  select * into b from retail_private.social_render_byte_receipts
    where shop_id=p_shop
      and media_asset_id=(candidate->>'media_asset_id')::uuid
      and object_path=candidate->>'object_path';
  if not found then return null; end if;
  return jsonb_build_object('shop_id',b.shop_id,
    'media_asset_id',b.media_asset_id,'object_path',b.object_path,
    'source_sha256',encode(b.source_sha256,'hex'),
    'source','PART1_RENDER_FINALIZED');
end
$$;

-- Explicit separate reviewer attestations. These are not inferred from
-- media_assets.license_name, generated clips or FFprobe.
create table retail_private.social_video_rights_clearances(
  job_id uuid not null,
  revision integer not null check(revision>0),
  shop_id uuid not null,
  media_asset_id uuid not null,
  reviewed_by uuid not null references auth.users(id),
  rights_kind text not null check (rights_kind in (
    'OWNER_ATTESTED','STOCK_LICENSE_VERIFIED','GENERATED_RIGHTS_VERIFIED')),
  rights_evidence_sha256 bytea not null check(octet_length(rights_evidence_sha256)=32),
  rights_expires_at timestamptz not null,
  recorded_at timestamptz not null default now(),
  primary key(job_id,revision),
  foreign key(shop_id,job_id) references public.social_publish_jobs(shop_id,id)
    on delete cascade,
  foreign key(shop_id,media_asset_id) references public.media_assets(shop_id,id)
    on delete cascade
);
alter table retail_private.social_video_rights_clearances enable row level security;
revoke all on retail_private.social_video_rights_clearances from public,anon,authenticated;
grant select,insert on retail_private.social_video_rights_clearances to service_role;

-- A trusted licensing reviewer service must verify the underlying document,
-- account consent and commercial rights before creating this durable receipt.
create function public.p2_record_social_video_rights(
  p_shop uuid,p_job uuid,p_actor uuid,p_revision integer,
  p_evidence text,p_kind text,p_expires timestamptz
) returns boolean language plpgsql security definer set search_path=''
as $$
declare
  c jsonb; j public.social_publish_jobs%rowtype;
  existing retail_private.social_video_rights_clearances%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'rights attestation service only' using errcode='42501';
  end if;
  if p_evidence is null or p_evidence !~ '^[0-9a-f]{64}$'
     or p_kind not in ('OWNER_ATTESTED','STOCK_LICENSE_VERIFIED',
                      'GENERATED_RIGHTS_VERIFIED')
     or p_revision is null or p_revision<1 or p_expires is null
     or p_expires<=now() then return false; end if;
  select * into j from public.social_publish_jobs
    where id=p_job and shop_id=p_shop for update;
  c:=public.p2_social_video_review_candidate(p_shop,p_job,p_actor);
  if not found or c is null or j.revision<>p_revision
     or p_expires<=j.scheduled_at+interval '1 hour'
  then return false; end if;
  insert into retail_private.social_video_rights_clearances(
    shop_id,job_id,revision,media_asset_id,reviewed_by,rights_kind,
    rights_evidence_sha256,rights_expires_at)
  values(p_shop,p_job,p_revision,j.media_asset_id,p_actor,p_kind,
    decode(p_evidence,'hex'),p_expires)
  on conflict do nothing;
  select * into existing from retail_private.social_video_rights_clearances
    where job_id=p_job and revision=p_revision;
  return found and existing.shop_id=p_shop
    and existing.media_asset_id=j.media_asset_id
    and existing.reviewed_by=p_actor
    and existing.rights_kind=p_kind
    and existing.rights_evidence_sha256=decode(p_evidence,'hex')
    and existing.rights_expires_at=p_expires;
end
$$;

create function public.p2_social_video_rights_for_review(
  p_shop uuid,p_job uuid,p_actor uuid,p_revision integer
) returns jsonb language plpgsql security definer set search_path=''
as $$
declare
  c jsonb; l retail_private.social_video_rights_clearances%rowtype;
  j public.social_publish_jobs%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'rights lookup service only' using errcode='42501';
  end if;
  c:=public.p2_social_video_review_candidate(p_shop,p_job,p_actor);
  if c is null or (c->>'revision')::integer<>p_revision then return null; end if;
  select * into j from public.social_publish_jobs
    where id=p_job and shop_id=p_shop and status='DRAFT';
  select * into l from retail_private.social_video_rights_clearances
    where job_id=p_job and shop_id=p_shop and revision=p_revision
      and media_asset_id=(c->>'media_asset_id')::uuid
      and reviewed_by=p_actor
      and rights_expires_at>now()
      and rights_expires_at>j.scheduled_at+interval '1 hour';
  if not found then return null; end if;
  return jsonb_build_object('shop_id',l.shop_id,
    'media_asset_id',l.media_asset_id,'reviewed_by',l.reviewed_by,
    'revision',l.revision,'rights_kind',l.rights_kind,
    'rights_evidence_sha256',encode(l.rights_evidence_sha256,'hex'),
    'rights_expires_at',l.rights_expires_at);
end
$$;
revoke all on function public.p2_record_finalized_render_digest(uuid,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_social_video_review_candidate(uuid,uuid,uuid)
  from public,anon,authenticated;
revoke all on function public.p2_social_video_render_receipt(uuid,uuid,uuid)
  from public,anon,authenticated;
revoke all on function public.p2_record_social_video_rights(uuid,uuid,uuid,integer,text,text,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_social_video_rights_for_review(uuid,uuid,uuid,integer)
  from public,anon,authenticated;
grant execute on function public.p2_record_finalized_render_digest(uuid,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_social_video_review_candidate(uuid,uuid,uuid)
  to service_role;
grant execute on function public.p2_social_video_render_receipt(uuid,uuid,uuid)
  to service_role;
grant execute on function public.p2_record_social_video_rights(uuid,uuid,uuid,integer,text,text,timestamptz)
  to service_role;
grant execute on function public.p2_social_video_rights_for_review(uuid,uuid,uuid,integer)
  to service_role;
commit;
