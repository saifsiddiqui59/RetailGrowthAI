-- Part 2 service-owned immutable exports WITHIN existing Part1 media bucket.
-- SOURCE ONLY. This pending P2 migration was never hosted and intentionally
-- REPLACES its earlier second-bucket proposal to preserve the project's
-- single-bucket contract and existing quota/storage infrastructure.
begin;

-- Fail closed unless Part1's original bucket remains private.
do $p2originalbucket$
begin
  if not exists(
    select 1 from storage.buckets b
      where b.id='retailgrowth-media' and b.name='retailgrowth-media'
        and b.public=false
  ) then
    raise exception 'Part1 private media bucket missing or public'
      using errcode='23514';
  end if;
end $p2originalbucket$;

-- Existing Part1 authenticated Storage policies permit edits/deletes under a
-- normal tenant prefix. Restrict the reserved service-only second path
-- component instead: <shop_uuid>/social-exports/<job_uuid>/<rev>/<sha>.mp4.
-- RESTRICTIVE policies compose with ALL present/future permissive policies.
-- Service-role can upload create-only with x-upsert:false and sign internally.
create policy p2_social_export_prefix_client_denial
  on storage.objects as restrictive for all to anon,authenticated
  using (bucket_id is distinct from 'retailgrowth-media'
         or split_part(name,'/',2) is distinct from 'social-exports')
  with check (bucket_id is distinct from 'retailgrowth-media'
              or split_part(name,'/',2) is distinct from 'social-exports');

commit;
