-- Feature3 P0 service-only immutable evidence writer, additive AFTER #542.
-- Source only. NEVER auto-apply to hosted DEV/PROD.
-- This is a server-verified *metadata transaction*, NOT proof that remote
-- private image bytes or a commercial image license have been inspected.
begin;

create function public.feature3_commit_verified_evidence(
  p_shop_id uuid,
  p_model_id uuid,
  p_media_asset_id uuid,
  p_verifier_id uuid,
  p_expected_image_sha256 text,
  p_expected_license_evidence_sha256 text,
  p_source_uri text,
  p_pose text,
  p_synthetic_adult_verified boolean,
  p_component_rights_cleared boolean,
  p_commercial_reuse_approved boolean
) returns jsonb
language plpgsql volatile security definer set search_path=''
as $$
declare
  m public.feature3_models%rowtype;
  a public.media_assets%rowtype;
  expected_key text;
begin
  -- An exposed RPC still cannot be executed by any user/anon credential.
  -- The service-owned transport MUST independently verify exact private
  -- Storage bytes and documented rights BEFORE calling this function.
  if p_shop_id is null or p_model_id is null or p_media_asset_id is null
     or p_verifier_id is null
     or p_expected_image_sha256 is null or p_expected_image_sha256 !~ '^[a-f0-9]{64}$'
     or p_expected_license_evidence_sha256 is null or p_expected_license_evidence_sha256 !~ '^[a-f0-9]{64}$'
     or p_pose is null or p_pose not in ('front','three_quarter','side','full_body','portrait')
     or p_synthetic_adult_verified is distinct from true
     or p_component_rights_cleared is distinct from true
     or p_commercial_reuse_approved is distinct from true
     or p_source_uri is null or length(p_source_uri) not between 12 and 1500
     or p_source_uri !~ '^https://[^/@?#[:space:]]+(/[^#[:space:]]*)?$'
  then return null; end if;

  -- Lock the model before deciding: competing decisions/revocations must
  -- serialize. A verified attestation may be committed only once while
  -- the model is still unapproved and at its original revision.
  select * into m from public.feature3_models
   where owner_shop_id=p_shop_id and model_id=p_model_id for update;
  if not found or m.status<>'PENDING_REVIEW'
    or m.rights_verified or m.rights_revision<>1
    or m.media_asset_id<>p_media_asset_id
    or m.image_sha256<>p_expected_image_sha256
    or m.license_evidence_sha256<>p_expected_license_evidence_sha256
    or m.synthetic_adult is not true
  then return null; end if;

  -- The trusted server cannot claim a random user as verifier:
  -- require the user to remain an active eligible member of that shop.
  if not exists (
    select 1 from public.shop_memberships s
    where s.shop_id=p_shop_id and s.user_id=p_verifier_id
      and s.active and s.role in ('OWNER','EDITOR')
  ) then return null; end if;

  expected_key := p_shop_id::text || '/model-library/' ||
    case when m.scope='platform' then 'platform/' else '' end ||
    p_model_id::text || '/' || m.image_sha256 || '.png';
  select * into a from public.media_assets
   where shop_id=p_shop_id and id=m.media_asset_id for share;
  if not found or a.storage_bucket<>'retailgrowth-media'
     or a.object_path<>expected_key or a.mime_type<>'image/png'
     or a.source not in ('UPLOAD','GENERATED')
     or a.license_name not in ('owned','cc0','commercial','royalty_free')
     or length(trim(coalesce(a.attribution,'')))<10
     or (a.license_name<>'owned' and
       (a.license_url is null or a.license_url not like 'https://%'))
     or (m.license_id='CC-BY-4.0' and length(trim(m.attribution))=0)
  then return null; end if;

  -- Only INSERT: service_role is not granted UPDATE/DELETE on evidence.
  -- Duplicate submissions are denied, not silently upserted or replayed.
  if exists (select 1 from retail_private.feature3_model_evidence e
     where e.owner_shop_id=p_shop_id and e.model_id=p_model_id)
  then return null; end if;

  insert into retail_private.feature3_model_evidence (
    owner_shop_id,model_id,media_asset_id,image_sha256,license_id,
    license_evidence_sha256,source_kind,source_uri,pose,
    synthetic_adult_verified,component_rights_cleared,
    commercial_reuse_approved,verified_by)
  values (
    p_shop_id,p_model_id,m.media_asset_id,m.image_sha256,m.license_id,
    m.license_evidence_sha256,m.source_kind,p_source_uri,p_pose,
    true,true,true,p_verifier_id);

  return jsonb_build_object(
    'owner_shop_id',p_shop_id,'model_id',p_model_id,
    'media_asset_id',m.media_asset_id,
    'image_sha256',m.image_sha256,
    'license_evidence_sha256',m.license_evidence_sha256,
    'evidence_revision',1,
    'persisted',true);
end
$$;

revoke all on function public.feature3_commit_verified_evidence(
  uuid,uuid,uuid,uuid,text,text,text,text,boolean,boolean,boolean
) from public,anon,authenticated;
grant execute on function public.feature3_commit_verified_evidence(
  uuid,uuid,uuid,uuid,text,text,text,text,boolean,boolean,boolean
) to service_role;
commit;
