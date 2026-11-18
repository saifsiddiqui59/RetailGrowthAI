-- Feature3 SERVICE-ONLY private output evidence for manual, read-only reconciliation.
-- SQL PROPOSAL ONLY: outside canonical 31 migration versions.\n-- Coordinator must allocate a reviewed migration version and explicit hosted release.
-- Does not allow retries, settlement, refunds, publication or GPU activation.
begin;

create function public.feature3_read_gpu_private_evidence(
  p_shop_id uuid, p_job_id uuid, p_media_asset_id uuid
) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare
  e retail_private.feature3_gpu_output_evidence%rowtype;
  j public.feature3_gpu_jobs%rowtype;
  a public.media_assets%rowtype;
  stored storage.objects%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'Service-only Feature3 recovery evidence' using errcode='42501';
  end if;
  if p_shop_id is null or p_job_id is null or p_media_asset_id is null then
    return null;
  end if;
  select * into e from retail_private.feature3_gpu_output_evidence
   where shop_id=p_shop_id and job_id=p_job_id
     and media_asset_id=p_media_asset_id
     and attempt=1 and review_status='UNREVIEWED';
  if not found then return null; end if;
  select * into j from public.feature3_gpu_jobs
   where id=p_job_id and shop_id=p_shop_id
     and status='SUCCEEDED' and attempts=1 and output_asset_id=p_media_asset_id;
  if not found then return null; end if;
  select * into a from public.media_assets
   where shop_id=p_shop_id and id=p_media_asset_id
     and storage_bucket='retailgrowth-media' and source='GENERATED'
     and mime_type='image/png' and object_path=e.object_path;
  if not found then return null; end if;
  select * into stored from storage.objects
   where bucket_id='retailgrowth-media' and name=e.object_path;
  if not found or stored.metadata is null
    or stored.metadata->>'mimetype' <> 'image/png'
    or coalesce(stored.metadata->>'size','') !~ '^[0-9]{1,10}$'
    or (stored.metadata->>'size')::bigint <> e.object_bytes
    or e.image_sha256 !~ '^[a-f0-9]{64}$'
    or e.object_path <> p_shop_id::text||'/feature3/gpu/'||
       p_job_id::text||'/'||e.image_sha256||'.png'
    then return null;
  end if;
  return jsonb_build_object(
    'shop_id',e.shop_id,'job_id',e.job_id,
    'media_asset_id',e.media_asset_id,
    'image_sha256',e.image_sha256,
    'object_path',e.object_path,'object_bytes',e.object_bytes,
    'attempt',e.attempt,'review_status',e.review_status,
    'private',true);
end $$;
revoke all on function public.feature3_read_gpu_private_evidence(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.feature3_read_gpu_private_evidence(uuid,uuid,uuid)
  to service_role;
commit;
