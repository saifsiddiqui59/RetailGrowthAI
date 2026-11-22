-- Feature4 service-only CPU worker claim/authorization SOURCE CANDIDATE.
-- Depends on reviewed_cpu_plans and cpu_render_jobs; disposable CI only.
-- Never apply to hosted DEV/PROD or change legacy v1 render claims.
-- Required JSON fields must be null-safe: a missing approval is never allowed.
begin;
create function retail_private.feature4_cpu_authorized(p_id uuid)
returns boolean language plpgsql stable security definer set search_path=''
as $f$
declare j public.feature4_cpu_render_jobs%rowtype;
        p public.feature4_creative_plans%rowtype;
        item jsonb; a public.media_assets%rowtype; digest text;
begin
 select * into j from public.feature4_cpu_render_jobs where id=p_id;
 if not found then return false; end if;
 select * into p from public.feature4_creative_plans where id=j.plan_id
   and shop_id=j.shop_id and campaign_id=j.campaign_id;
 if not found or p.state<>'APPROVED' or p.revoked_at is not null
   or p.review_sha256 is distinct from j.approved_review_sha256
   or p.reviewed_by is null or p.approved_direction->>'review_hash' is distinct from p.review_sha256
   or p.approved_direction->>'approval_id' is distinct from p.id::text
   or p.approved_direction->>'shop_id' is distinct from j.shop_id::text
   or p.approved_direction->>'campaign_id' is distinct from j.campaign_id::text
   or p.approved_direction->>'version' is distinct from 'creative_direction_v1'
   or p.approved_direction->'approved' is distinct from 'true'::jsonb
   or p.approved_direction->'script'->'approved' is distinct from 'true'::jsonb
   or pg_catalog.jsonb_typeof(p.media_snapshot) is distinct from 'array'
   or pg_catalog.jsonb_array_length(p.media_snapshot) not between 1 and 12
   or pg_catalog.jsonb_array_length(p.media_snapshot) is distinct from cardinality(p.media_asset_ids)
 then return false; end if;
 digest:=pg_catalog.encode(extensions.digest(
   pg_catalog.convert_to('rgai-f2-f4-approved-v1','UTF8')||
   pg_catalog.decode('00','hex')||
   pg_catalog.convert_to(retail_private.python_json_v1(
      p.approved_direction-'review_hash'),'UTF8'),'sha256'),'hex');
 if digest is distinct from j.approved_review_sha256 then return false; end if;
 if not exists(select 1 from public.shop_memberships m where
     m.shop_id=j.shop_id and m.user_id=p.reviewed_by and m.active
     and m.role in ('OWNER','EDITOR'))
   or not exists(select 1 from public.shop_memberships m where
     m.shop_id=j.shop_id and m.user_id=j.requested_by and m.active
     and m.role in ('OWNER','EDITOR'))
   or not exists(select 1 from public.campaigns c where
     c.id=j.campaign_id and c.shop_id=j.shop_id and c.status in ('DRAFT','READY'))
 then return false; end if;
 if p.approved_direction ? 'source_reel' then
   if p.approved_direction->>'day_id' is null
     or p.approved_direction->>'day_id' !~
       '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
     or not exists(select 1 from public.campaign_days d
       where d.id=(p.approved_direction->>'day_id')::uuid
       and d.shop_id=j.shop_id and d.campaign_id=j.campaign_id
       and d.review_status='DRAFT'
       and d.instagram->'reel'=p.approved_direction->'source_reel')
   then return false; end if;
 end if;
 for item in select value from pg_catalog.jsonb_array_elements(p.media_snapshot) loop
   if pg_catalog.jsonb_typeof(item)<>'object'
     or item->>'id' !~
       '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
   then return false; end if;
   select * into a from public.media_assets where id=(item->>'id')::uuid
     and shop_id=j.shop_id;
   if not found or not a.id=any(p.media_asset_ids)
     or a.source<>'UPLOAD' or a.storage_bucket<>'retailgrowth-media'
     or pg_catalog.lower(a.license_name)<>'owned'
     or a.mime_type not in ('image/png','image/jpeg','image/webp')
     or pg_catalog.left(a.object_path,pg_catalog.length(j.shop_id::text)+9)
           <> j.shop_id::text||'/uploads/'
     or item<>pg_catalog.jsonb_build_object(
       'id',a.id,'shop_id',a.shop_id,'path',a.object_path,
       'mime',a.mime_type,'source',a.source,'license',a.license_name)
   then return false; end if;
 end loop;
 return true;
end $f$;
revoke all on function retail_private.feature4_cpu_authorized(uuid)
  from public,anon,authenticated;
grant execute on function retail_private.feature4_cpu_authorized(uuid) to service_role;

create function public.feature4_claim_cpu_render(p_id uuid)
returns jsonb language plpgsql volatile security definer set search_path=''
as $f$
declare j public.feature4_cpu_render_jobs%rowtype;
begin
 if p_id is null then return null; end if;
 select * into j from public.feature4_cpu_render_jobs where id=p_id for update;
 if not found or j.status in ('SUCCEEDED','FAILED')
   or (j.status='RUNNING' and j.render_lease_until>now())
 then return null; end if;
 if j.attempts>=3 then
   update public.feature4_cpu_render_jobs set status='FAILED',
      error_code='RETRY_EXHAUSTED',render_claim_token=null,render_lease_until=null
      where id=p_id;
   return null;
 end if;
 if not retail_private.feature4_cpu_authorized(p_id) then
   update public.feature4_cpu_render_jobs set status='FAILED',
     error_code='ACCESS_REVOKED',render_claim_token=null,render_lease_until=null
     where id=p_id;
   return null;
 end if;
 update public.feature4_cpu_render_jobs set status='RUNNING',
   attempts=attempts+1,render_claim_token=gen_random_uuid(),
   render_lease_until=now()+interval '25 minutes',error_code=null
   where id=p_id returning * into j;
 return pg_catalog.to_jsonb(j)||pg_catalog.jsonb_build_object(
   'preset','feature4_reel_v1');
end $f$;
revoke all on function public.feature4_claim_cpu_render(uuid)
 from public,anon,authenticated;
grant execute on function public.feature4_claim_cpu_render(uuid) to service_role;

create function public.feature4_cpu_claim_current(p_id uuid,p_token uuid)
returns boolean language sql stable security definer set search_path=''
as $f$
 select exists(
   select 1 from public.feature4_cpu_render_jobs j where j.id=p_id
     and j.status='RUNNING' and j.render_claim_token=p_token
     and j.render_lease_until>now()
     and retail_private.feature4_cpu_authorized(j.id))
$f$;
revoke all on function public.feature4_cpu_claim_current(uuid,uuid)
 from public,anon,authenticated;
grant execute on function public.feature4_cpu_claim_current(uuid,uuid) to service_role;
commit;
