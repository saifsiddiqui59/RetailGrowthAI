-- Feature4 v2 worker completion/failure SOURCE CANDIDATE, isolated SQL only.
-- Fail closed on NULL lease expiry: SQL UNKNOWN is not a valid claim.
-- Never infer output bytes from renderer testimony alone. Service worker must
-- first re-download uploaded object and check exact SHA-256.
begin;
create function public.feature4_fail_cpu_render(
 p_id uuid,p_token uuid,p_code text,p_permanent boolean default false)
returns boolean language plpgsql volatile security definer set search_path=''
as $f$
declare j public.feature4_cpu_render_jobs%rowtype;
        terminal boolean; sends integer;
begin
 if p_id is null or p_token is null or p_code is null or
    p_code !~ '^[A-Z_]{3,64}$' or p_permanent is null
 then return false; end if;
 select * into j from public.feature4_cpu_render_jobs where id=p_id for update;
 if not found or j.status<>'RUNNING' or
   j.render_claim_token is distinct from p_token or
   (j.render_lease_until is null or j.render_lease_until<=now()) then return false; end if;
 select attempts into sends from retail_private.feature4_cpu_outbox
   where job_id=p_id for update;
 terminal:=p_permanent or j.attempts>=3 or coalesce(sends,8)>=8;
 update public.feature4_cpu_render_jobs set
   status=case when terminal then 'FAILED' else 'QUEUED' end,
   error_code=p_code,render_claim_token=null,render_lease_until=null
   where id=p_id;
 update retail_private.feature4_cpu_outbox set
   state=case when terminal or attempts>=8 then 'DEAD' else 'PENDING' end,
   retry_after=now()+(pg_catalog.power(2,least(j.attempts,3))
       * interval '1 minute'),
   lease_token=null,lease_until=null where job_id=p_id;
 return true;
end $f$;
revoke all on function public.feature4_fail_cpu_render(uuid,uuid,text,boolean)
 from public,anon,authenticated;
grant execute on function public.feature4_fail_cpu_render(uuid,uuid,text,boolean)
 to service_role;

create function public.feature4_complete_cpu_render(
  p_id uuid,p_token uuid,p_path text,p_sha256 text)
returns boolean language plpgsql volatile security definer set search_path=''
as $f$
declare j public.feature4_cpu_render_jobs%rowtype;
        bytes bigint; asset uuid;
begin
 if p_id is null or p_token is null or
    p_sha256 is null or p_sha256 !~ '^[0-9a-f]{64}$'
 then return false; end if;
 select * into j from public.feature4_cpu_render_jobs where id=p_id for update;
 if not found or j.status<>'RUNNING' or
    j.render_claim_token is distinct from p_token or
    (j.render_lease_until is null or j.render_lease_until<=now()) or
    p_path is distinct from (j.shop_id::text||'/renders/'||
       j.id::text||'/'||p_token::text||'.mp4') or
    not retail_private.feature4_cpu_authorized(j.id)
 then return false; end if;
 select (o.metadata->>'size')::bigint into bytes from storage.objects o
  where o.bucket_id='retailgrowth-media' and o.name=p_path
    and o.metadata->>'mimetype'='video/mp4';
 if bytes is null or bytes<=1024 or bytes>83886080 then return false; end if;
 insert into public.media_assets(shop_id,created_by,storage_bucket,object_path,
    mime_type,source,license_name,attribution)
 values(j.shop_id,j.requested_by,'retailgrowth-media',p_path,'video/mp4',
    'GENERATED','owned','CPU video assembled from currently reviewed private media')
 returning id into asset;
 update public.feature4_cpu_render_jobs set
    status='SUCCEEDED',output_asset_id=asset,output_sha256=p_sha256,
    error_code=null,completed_at=now()
 where id=p_id and render_claim_token=p_token;
 return found;
end $f$;
revoke all on function public.feature4_complete_cpu_render(uuid,uuid,text,text)
 from public,anon,authenticated;
grant execute on function public.feature4_complete_cpu_render(uuid,uuid,text,text)
 to service_role;
commit;
