-- Feature3 GPU-OFF model rights authority, REVIEW-ONLY SQL PROPOSAL.
-- NOT a canonical migration. Do not apply to hosted DEV/PROD without
-- coordinator/DB-owner review, a migration version and separate approval.
-- The trusted service must independently validate original licence evidence
-- before inserting feature3_model_evidence. SQL cannot establish legal title.
-- No inference, billing, queue ACK, publication or data mutation.
begin;

create function public.feature3_read_current_model_review(
  p_shop_id uuid, p_media_asset_id uuid, p_image_sha256 text
) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare
  m public.feature3_models%rowtype;
  e retail_private.feature3_model_evidence%rowtype;
  ev retail_private.feature3_model_review_events%rowtype;
  a public.media_assets%rowtype;
  o storage.objects%rowtype;
  expected_key text;
  required_checks text[] := array[
    'adult_synthetic','approved_uses','image_license',
    'likeness_and_consent','private_media_integrity','visual_quality'];
  k text;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'Feature3 model rights require service role'
      using errcode='42501';
  end if;
  if p_shop_id is null or p_media_asset_id is null
     or p_image_sha256 is null
     or p_image_sha256 !~ '^[0-9a-f]{64}$' then
    return null;
  end if;

  -- A shop-only model proof: platform model metadata never grants another
  -- tenant the original private pixels or a cross-shop source receipt.
  select * into m from public.feature3_models
   where owner_shop_id=p_shop_id and media_asset_id=p_media_asset_id
     and image_sha256=p_image_sha256
     and status='APPROVED' and rights_verified is true
     and synthetic_adult is true
     and 'poster'=any(approved_uses)
     and rights_revision>=2
   limit 2;
  if not found then return null; end if;
  -- Exactly one current model must own this media ID per shop. An ambiguous
  -- duplicate entry is not a valid rights authority.
  if (select count(*) from public.feature3_models
      where owner_shop_id=p_shop_id and media_asset_id=p_media_asset_id
        and image_sha256=p_image_sha256) <> 1 then
    return null;
  end if;

  select * into e from retail_private.feature3_model_evidence
   where owner_shop_id=p_shop_id and model_id=m.model_id
     and media_asset_id=p_media_asset_id;
  if not found or e.image_sha256 <> m.image_sha256
     or e.license_id <> m.license_id
     or e.license_evidence_sha256 <> m.license_evidence_sha256
     or e.source_kind <> m.source_kind
     or e.evidence_revision <> 1
     or e.synthetic_adult_verified is not true
     or e.component_rights_cleared is not true
     or e.commercial_reuse_approved is not true then
    return null;
  end if;

  -- The latest event, NOT any historical approval, decides current rights.
  select * into ev from retail_private.feature3_model_review_events
   where owner_shop_id=p_shop_id and model_id=m.model_id
   order by rights_revision desc limit 1;
  if not found or ev.media_asset_id <> p_media_asset_id
     or ev.image_sha256 <> p_image_sha256
     or ev.action <> 'APPROVE'
     or ev.from_status <> 'PENDING_REVIEW'
     or ev.to_status <> 'APPROVED'
     or ev.rights_revision <> m.rights_revision
     or ev.previous_revision <> m.rights_revision-1
     or ev.evidence_revision <> e.evidence_revision
     or jsonb_typeof(ev.checks) <> 'object' then
    return null;
  end if;
  if (select array_agg(key order by key)
        from jsonb_object_keys(ev.checks) as key)
       is distinct from required_checks then
    return null;
  end if;
  foreach k in array required_checks loop
    if jsonb_typeof(ev.checks->k) <> 'boolean'
       or ev.checks->>k <> 'true' then
      return null;
    end if;
  end loop;

  expected_key := p_shop_id::text||'/model-library/'||
    case when m.scope='platform' then 'platform/' else '' end||
    m.model_id::text||'/'||p_image_sha256||'.png';
  select * into a from public.media_assets
   where shop_id=p_shop_id and id=p_media_asset_id
     and storage_bucket='retailgrowth-media'
     and object_path=expected_key
     and mime_type='image/png'
     and source in ('UPLOAD','GENERATED')
     and license_name in ('owned','cc0','commercial','royalty_free')
     and length(trim(coalesce(attribution,'')))>=10
     and (license_name='owned' or license_url like 'https://%');
  if not found then return null; end if;
  if m.license_id='CC-BY-4.0' and length(trim(m.attribution))=0 then
    return null;
  end if;

  -- Storage metadata is only an existence/size check, never SHA proof.
  -- The Python source reader independently GETs and hashes actual bytes.
  select * into o from storage.objects
    where bucket_id='retailgrowth-media' and name=expected_key;
  if not found or o.metadata is null
     or o.metadata->>'mimetype' <> 'image/png'
     or coalesce(o.metadata->>'size','') !~ '^[0-9]{1,10}$' then
    return null;
  end if;
  if (o.metadata->>'size')::bigint not between 100 and 26214400 then
    return null;
  end if;

  return jsonb_build_object(
    'shop_id',p_shop_id,'asset_id',p_media_asset_id,
    'image_sha256',p_image_sha256,'rights_revision',m.rights_revision,
    'independent_license_verified',true,
    'current_customer_approval',true,'rights_revoked',false);
end $$;

revoke all on function public.feature3_read_current_model_review(uuid,uuid,text)
  from public,anon,authenticated;
grant execute on function public.feature3_read_current_model_review(uuid,uuid,text)
  to service_role;
commit;
