-- Apply only to a dedicated RetailGrowthAI Supabase project, after the foundation migration.
begin;
-- Created private by default; no anonymous listing or reads.
insert into storage.buckets (id, name, public, file_size_limit)
values ('retailgrowth-media', 'retailgrowth-media', false, 52428800)
on conflict (id) do update set public = false;

-- Safe parse: invalid/malformed paths evaluate to null rather than raising a cast exception.
create function retail_private.media_path_shop(path text) returns uuid
language sql immutable security invoker set search_path = ''
as $$
  select case when split_part(path,'/',1) ~*
    '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    then split_part(path,'/',1)::uuid else null::uuid end
$$;
revoke all on function retail_private.media_path_shop(text) from public, anon;
grant execute on function retail_private.media_path_shop(text) to authenticated;

create policy retailgrowth_media_read on storage.objects for select to authenticated
using (bucket_id = 'retailgrowth-media'
  and retail_private.has_role(retail_private.media_path_shop(name),array['OWNER','EDITOR','VIEWER']));
create policy retailgrowth_media_insert on storage.objects for insert to authenticated
with check (bucket_id = 'retailgrowth-media'
  and retail_private.has_role(retail_private.media_path_shop(name),array['OWNER','EDITOR']));
create policy retailgrowth_media_update on storage.objects for update to authenticated
using (bucket_id = 'retailgrowth-media'
  and retail_private.has_role(retail_private.media_path_shop(name),array['OWNER','EDITOR']))
with check (bucket_id = 'retailgrowth-media'
  and retail_private.has_role(retail_private.media_path_shop(name),array['OWNER','EDITOR']));
create policy retailgrowth_media_delete on storage.objects for delete to authenticated
using (bucket_id = 'retailgrowth-media'
  and retail_private.has_role(retail_private.media_path_shop(name),array['OWNER','EDITOR']));
commit;
