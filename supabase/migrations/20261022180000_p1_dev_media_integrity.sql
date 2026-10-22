-- RetailGrowthAI DEV-readiness hardening. Approval is required before applying
-- this migration to the existing RetailGrowthAI DEV project.
-- The private bucket also holds backend-created render outputs; do not change its
-- 50 MB global limit or restrict its MIME types to images.
begin;

-- A browser upload may ONLY create a new image at its own shop's canonical path.
-- Previously any file/path below a shop prefix was accepted by Storage RLS.
drop policy if exists retailgrowth_media_insert on storage.objects;
create policy retailgrowth_media_insert on storage.objects
  for insert to authenticated
  with check (
    bucket_id = 'retailgrowth-media'
    and retail_private.has_role(retail_private.media_path_shop(name), array['OWNER','EDITOR'])
    and name ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/uploads/[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}[.](png|jpg|webp)$'
  );

-- The app uses Storage uploads with x-upsert=false. Browser UPDATE permits
-- replacement, rename and owner/metadata mutation of already licensed assets.
-- Backend service_role is responsible for generated media and controlled repair.
drop policy if exists retailgrowth_media_update on storage.objects;

-- A failed registration leaves an orphan upload. Members may clean it up.
-- Registered assets must NOT be erased via Storage before service-side metadata,
-- references and render use are reconciled.
drop policy if exists retailgrowth_media_delete on storage.objects;
create policy retailgrowth_media_delete on storage.objects
  for delete to authenticated
  using (
    bucket_id = 'retailgrowth-media'
    and retail_private.has_role(retail_private.media_path_shop(name), array['OWNER','EDITOR'])
    and not exists (
      select 1 from public.media_assets a
      where a.storage_bucket = 'retailgrowth-media' and a.object_path = name
    )
  );

-- Prevent a browser deleting the registration first to bypass the above guard.
-- Future revocation/removal must be a separately authorized, auditable backend flow.
revoke delete on public.media_assets from authenticated;

commit;
