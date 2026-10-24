-- Part 2 isolated service-owned immutable outbound media staging, SOURCE ONLY.
-- Requires separately authorized P2 hosted migration + private service uploader.
-- Never allow browser writes/updates/deletes or publish from mutable P1 bucket.
begin;

insert into storage.buckets (id,name,public,file_size_limit)
values('retailgrowth-social-exports','retailgrowth-social-exports',
       false,83886080)
on conflict(id) do nothing;

-- Fail closed if a previously configured bucket has unsafe public access.
do $$
begin
  if not exists(
      select 1 from storage.buckets
       where id='retailgrowth-social-exports' and name=id and public=false
         and file_size_limit=83886080
  ) then
    raise exception 'unsafe existing social export bucket' using errcode='23514';
  end if;
end $$;

-- RESTRICTIVE row policy prevents any other permissive storage policy from
-- accidentally making exports editable/readable to anon or authenticated.
-- Service-role/backend bypass with create-only upload must own every object.
create policy p2_social_export_client_denial
  on storage.objects as restrictive for all to anon,authenticated
  using (bucket_id is distinct from 'retailgrowth-social-exports')
  with check (bucket_id is distinct from 'retailgrowth-social-exports');

commit;
