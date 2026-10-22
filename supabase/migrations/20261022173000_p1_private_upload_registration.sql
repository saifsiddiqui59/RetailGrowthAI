-- RetailGrowthAI private upload metadata binding. DO NOT apply to WineShopPOS.
-- The Storage API uploads a private object first. This registration RPC then
-- verifies that object exists, belongs to the current user/shop, has a supported
-- image MIME type and bounded size. Rights are still USER-DECLARED; human review
-- of evidence is required before publishing commercially.
begin;
revoke insert on public.media_assets from authenticated;

create function public.register_uploaded_image(
  p_shop_id uuid, p_object_path text, p_license_name text,
  p_license_url text, p_attribution text
)
returns uuid language plpgsql volatile security definer set search_path = ''
as $$
declare
  object_row storage.objects%rowtype;
  image_type text;
  object_bytes bigint;
  new_id uuid;
  basename text;
begin
  if (select auth.uid()) is null or p_shop_id is null
     or not retail_private.has_role(p_shop_id, array['OWNER','EDITOR']) then
    return null;
  end if;
  if p_object_path is null or length(p_object_path) > 200
     or split_part(p_object_path, '/', 1) <> p_shop_id::text
     or split_part(p_object_path, '/', 2) <> 'uploads'
     or array_length(string_to_array(p_object_path, '/'), 1) <> 3 then
    return null;
  end if;
  basename := split_part(p_object_path, '/', 3);
  if basename !~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.](png|jpg|webp)$' then
    return null;
  end if;
  if p_license_name is null or p_license_name not in ('owned','cc0','commercial','royalty_free')
     or p_attribution is null or length(trim(p_attribution)) not between 10 and 500
     or p_license_url is not null and length(p_license_url) > 500
     or (p_license_name <> 'owned'
         and (p_license_url is null or p_license_url !~ '^https://[^[:space:]]{4,}$')) then
    return null;
  end if;
  select * into object_row from storage.objects
   where bucket_id = 'retailgrowth-media' and name = p_object_path
     and owner_id = (select auth.uid())::text;
  if not found or object_row.metadata is null then return null; end if;

  image_type := object_row.metadata->>'mimetype';
  if image_type not in ('image/jpeg','image/png','image/webp')
     or coalesce(object_row.metadata->>'size','') !~ '^[0-9]{1,10}$' then
    return null;
  end if;
  object_bytes := (object_row.metadata->>'size')::bigint;
  if object_bytes < 100 or object_bytes > 26214400 then return null; end if;
  if (image_type = 'image/jpeg' and basename !~ '[.]jpg$')
     or (image_type = 'image/png' and basename !~ '[.]png$')
     or (image_type = 'image/webp' and basename !~ '[.]webp$') then
    return null;
  end if;

  -- Authenticated cannot directly fabricate asset rows after grant revocation.
  -- Retains DB uniqueness on (storage_bucket,object_path).
  if exists(select 1 from public.media_assets
            where storage_bucket='retailgrowth-media' and object_path=p_object_path) then
    return null;
  end if;
  insert into public.media_assets (
    shop_id, created_by, object_path, mime_type, source,
    license_name, license_url, attribution
  ) values (
    p_shop_id, (select auth.uid()), p_object_path, image_type, 'UPLOAD',
    p_license_name, p_license_url, trim(p_attribution)
  ) returning id into new_id;
  return new_id;
end;
$$;
revoke all on function public.register_uploaded_image(uuid,text,text,text,text)
  from public, anon, authenticated;
grant execute on function public.register_uploaded_image(uuid,text,text,text,text)
  to authenticated;
commit;
