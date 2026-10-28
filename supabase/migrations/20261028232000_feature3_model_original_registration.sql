-- Feature3 signed model-original registration from private retailer Storage.
-- SOURCE ONLY, NO hosted DEV execution or paid/GPU activation.
begin;

-- Add the exact signed-upload namespace needed by feature3_register_model_original.
-- Existing user uploads remain allowed. Browser may never write GPU outputs.
drop policy retailgrowth_media_insert on storage.objects;
create policy retailgrowth_media_insert on storage.objects
 for insert to authenticated with check (
  bucket_id='retailgrowth-media'
  and retail_private.has_role(retail_private.media_path_shop(name),array['OWNER','EDITOR'])
  and (
   name ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/uploads/[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}[.](png|jpg|webp)$'
   or
   (name ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/model-library/[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/[a-f0-9]{64}[.]png$'
     and owner_id=(select auth.uid())::text)
  )
 );

create function public.feature3_register_model_original(
 p_shop_id uuid,p_model_id uuid,p_image_sha256 text,
 p_license_name text,p_license_url text,p_attribution text
) returns jsonb language plpgsql security definer set search_path='' as $$
declare
 actor uuid := (select auth.uid());
 key text;
 obj storage.objects%rowtype;
 asset uuid;
 bytes bigint;
begin
 -- Registration is only a DECLARATION: neither real image bytes, likeness,
 -- adult provenance nor customer-uploaded license is independently verified.
 if actor is null or p_shop_id is null or p_model_id is null or
    p_image_sha256 is null or p_image_sha256 !~ '^[a-f0-9]{64}$' or
    p_license_name not in ('owned','cc0','royalty_free','commercial') or
    p_attribution is null or length(trim(p_attribution)) not between 10 and 200 or
    p_attribution ~ '[[:cntrl:]]' or
    (p_license_name <> 'owned' and
     (p_license_url is null or p_license_url !~ '^https://[^[:space:]]{4,}$')) or
    length(coalesce(p_license_url,''))>500 or
    not exists(select 1 from public.shop_memberships m
      where m.shop_id=p_shop_id and m.user_id=actor
        and m.active and m.role in ('OWNER','EDITOR'))
 then return null; end if;

 key:=p_shop_id::text||'/model-library/'||
      p_model_id::text||'/'||p_image_sha256||'.png';
 select * into obj from storage.objects
  where bucket_id='retailgrowth-media' and name=key
    and owner_id=actor::text for share;
 if not found or obj.metadata is null or
    obj.metadata->>'mimetype'<>'image/png' or
    coalesce(obj.metadata->>'size','') !~ '^[0-9]{1,10}$'
 then return null; end if;
 bytes:=(obj.metadata->>'size')::bigint;
 if bytes<100 or bytes>26214400 then return null; end if;
 -- Serialize bounded model originals per shop; later model import has its
 -- own separate <=30 catalog cap and human/curator evidence requirement.
 perform 1 from public.shops where id=p_shop_id for update;
 if not found or (select count(*) from public.media_assets a
      where a.shop_id=p_shop_id and
      a.object_path like p_shop_id::text||'/model-library/%')>=30
 then return null; end if;
 insert into public.media_assets
   (shop_id,created_by,object_path,mime_type,source,
    license_name,license_url,attribution)
 values(p_shop_id,actor,key,'image/png','UPLOAD',
        p_license_name,p_license_url,trim(p_attribution))
 on conflict(storage_bucket,object_path) do nothing returning id into asset;
 if asset is null then return null; end if;
 return jsonb_build_object(
   'shop_id',p_shop_id,'model_id',p_model_id,'media_asset_id',asset,
   'image_sha256',p_image_sha256,'registered',true,
   'byte_sha_verified',false,'license_verified',false,
   'status','SOURCE_REGISTERED_PENDING_EVIDENCE','gpu_authorized',false);
end $$;
revoke all on function public.feature3_register_model_original(
 uuid,uuid,text,text,text,text) from public,anon,authenticated;
grant execute on function public.feature3_register_model_original(
 uuid,uuid,text,text,text,text) to authenticated;
commit;
