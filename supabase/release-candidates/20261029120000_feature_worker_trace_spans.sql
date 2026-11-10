-- SOURCE-ONLY RELEASE CANDIDATE. Do NOT apply to hosted DEV through this PR.
-- Use a separately reviewed canonical migration + approval gate. The 31 canonical
-- historical versions must not be rewritten. No WineShopPOS resources.
begin;

create table retail_private.feature_worker_spans (
  id uuid primary key default gen_random_uuid(),
  shop_id uuid not null references public.shops(id) on delete cascade,
  job_id uuid not null,
  feature text not null check(feature in ('F2','F4')),
  operation text not null check(operation in (
    'planning.complete','planning.denied','planning.failed','planning.unconfigured',
    'render.complete','render.denied','render.failed')),
  status text not null check(status in ('SUCCEEDED','FAILED','DENIED','UNCONFIGURED')),
  attempt integer not null check(attempt between 1 and 5),
  elapsed_ms integer not null check(elapsed_ms between 0 and 1800000),
  metadata jsonb not null default '{}'::jsonb
    check (jsonb_typeof(metadata)='object' and octet_length(metadata::text)<=2000),
  recorded_at timestamptz not null default now(),
  unique(feature,job_id,attempt,operation)
);
create index feature_worker_spans_shop_job
on retail_private.feature_worker_spans(shop_id,feature,job_id,recorded_at desc);
alter table retail_private.feature_worker_spans enable row level security;
revoke all on retail_private.feature_worker_spans from public,anon,authenticated;
grant select,insert on retail_private.feature_worker_spans to service_role;
-- Only service-written verified terminal outcomes can create rows.
create function public.retail_feature_worker_append(
 p_feature text,p_job_id uuid,p_attempt integer,p_operation text,
 p_status text,p_elapsed_ms integer,p_metadata jsonb default '{}'::jsonb)
returns jsonb
language plpgsql volatile security definer set search_path='' as $fn$
declare
 v_shop uuid;
 v_status text;
 v_attempt integer;
 v_output uuid;
 v_id uuid;
 v_existing retail_private.feature_worker_spans%rowtype;
begin
 if (select auth.role()) is distinct from 'service_role' then
   raise exception 'WORKER_SPAN_SERVICE_ONLY' using errcode='42501';
 end if;
 if p_job_id is null or p_attempt is null or p_attempt not between 1 and 5
    or p_elapsed_ms is null or p_elapsed_ms not between 0 and 1800000
    or p_metadata is null or jsonb_typeof(p_metadata)<>'object'
    or octet_length(p_metadata::text)>2000
    or exists(select 1 from jsonb_object_keys(p_metadata) as keys(k)
              where k not in ('planner_mode','generated_days','duration_seconds',
                              'codec','video_width','video_height'))
 then raise exception 'INVALID_WORKER_SPAN' using errcode='22023'; end if;

 -- Match the exact service-side operation-specific field contract.
 if (p_operation='planning.complete' and
       ((select count(*) from jsonb_object_keys(p_metadata))<>2 or
        jsonb_typeof(p_metadata->'generated_days')<>'number' or
        p_metadata->>'planner_mode' not in ('foundry','dev_mock'))) or
    (p_operation='render.complete' and
       ((select count(*) from jsonb_object_keys(p_metadata))<>4 or
        jsonb_typeof(p_metadata->'duration_seconds')<>'number' or
        jsonb_typeof(p_metadata->'video_width')<>'number' or
        jsonb_typeof(p_metadata->'video_height')<>'number')) or
    (p_operation not in ('planning.complete','render.complete')
      and p_metadata<>'{}'::jsonb)
 then raise exception 'WORKER_SPAN_METADATA_MISMATCH' using errcode='22023'; end if;

 if p_feature='F2' and p_operation in ('planning.complete','planning.denied',
                                      'planning.failed','planning.unconfigured') then
   select shop_id,status,planning_attempts into v_shop,v_status,v_attempt
   from public.campaigns where id=p_job_id;
   if not found or v_shop is null then
     raise exception 'WORKER_JOB_NOT_FOUND' using errcode='42501';
   end if;
   if (p_operation='planning.complete' and p_status='SUCCEEDED'
       and v_status='DRAFT'
       and (select count(*) from public.campaign_days where campaign_id=p_job_id
            and shop_id=v_shop)=7
       and p_metadata->>'generated_days'='7'
       and p_metadata->>'planner_mode' in ('foundry','dev_mock')) then
     null;
   elsif p_operation='planning.denied' and p_status='DENIED' and v_status='FAILED' then
     null;
   elsif p_operation='planning.failed' and p_status='FAILED' and v_status='FAILED' then
     null;
   elsif p_operation='planning.unconfigured' and p_status='UNCONFIGURED'
       and v_status='FAILED' then
     null;
   else
     raise exception 'WORKER_TERMINAL_STATE_MISMATCH' using errcode='42501';
   end if;
 elsif p_feature='F4' and p_operation in ('render.complete','render.denied','render.failed') then
   select shop_id,status,attempts,output_asset_id
   into v_shop,v_status,v_attempt,v_output
   from public.render_jobs where id=p_job_id;
   if not found or v_shop is null then
     raise exception 'WORKER_JOB_NOT_FOUND' using errcode='42501';
   end if;
   if p_operation='render.complete' and p_status='SUCCEEDED'
       and v_status='SUCCEEDED' and v_output is not null
       and p_metadata->>'codec'='h264/aac'
       and p_metadata->>'video_width'='1080'
       and p_metadata->>'video_height'='1920'
       and (p_metadata->>'duration_seconds')::numeric between 29.8 and 30.2 then
     null;
   elsif p_operation='render.denied' and p_status='DENIED' and v_status='FAILED' then
     null;
   elsif p_operation='render.failed' and p_status='FAILED' and v_status='FAILED' then
     null;
   else
     raise exception 'WORKER_TERMINAL_STATE_MISMATCH' using errcode='42501';
   end if;
 else
   raise exception 'UNKNOWN_WORKER_FEATURE_OPERATION' using errcode='22023';
 end if;
 if v_attempt is null or v_attempt<>p_attempt then
   raise exception 'WORKER_ATTEMPT_MISMATCH' using errcode='42501';
 end if;
 insert into retail_private.feature_worker_spans(
   shop_id,job_id,feature,operation,status,attempt,elapsed_ms,metadata)
 values(v_shop,p_job_id,p_feature,p_operation,p_status,p_attempt,p_elapsed_ms,p_metadata)
 on conflict(feature,job_id,attempt,operation) do nothing
 returning id into v_id;
 if v_id is null then
   select * into v_existing from retail_private.feature_worker_spans
   where feature=p_feature and job_id=p_job_id and attempt=p_attempt
      and operation=p_operation;
   if not found or v_existing.status is distinct from p_status
      or v_existing.metadata is distinct from p_metadata
   then raise exception 'WORKER_SPAN_CONFLICT' using errcode='23505'; end if;
   v_id:=v_existing.id;
 end if;
 return jsonb_build_object('id',v_id,'shop_id',v_shop,'job_id',p_job_id,
    'feature',p_feature,'operation',p_operation,'status',p_status,
    'attempt',p_attempt,'persisted',true);
end;
$fn$;
revoke all on function public.retail_feature_worker_append(
 text,uuid,integer,text,text,integer,jsonb) from public,anon,authenticated;
grant execute on function public.retail_feature_worker_append(
 text,uuid,integer,text,text,integer,jsonb) to service_role;

-- Tenant-signed read is an explicit RPC. Browser never receives table grants.
create function public.retail_feature_worker_spans(
 p_shop_id uuid,p_job_id uuid,p_limit integer default 30)
returns jsonb language plpgsql stable security definer set search_path='' as $fn$
declare v_events jsonb;
begin
 if (select auth.role()) is distinct from 'authenticated' or
    (select auth.uid()) is null or p_shop_id is null or p_job_id is null or
    p_limit is null or p_limit not between 1 and 50 or
    not retail_private.has_role(p_shop_id,array['OWNER','EDITOR'])
 then raise exception 'WORKER_SPAN_READ_DENIED' using errcode='42501'; end if;
 select coalesce(jsonb_agg(to_jsonb(t) order by t.recorded_at,t.id),'[]'::jsonb)
 into v_events from (
   select id,shop_id,job_id,feature,operation,status,attempt,
          elapsed_ms,metadata,recorded_at
   from retail_private.feature_worker_spans
   where shop_id=p_shop_id and job_id=p_job_id
   order by recorded_at desc,id desc limit p_limit
 ) t;
 return jsonb_build_object('shop_id',p_shop_id,'job_id',p_job_id,
                           'source','trusted_backend_persisted','events',v_events);
end;
$fn$;
revoke all on function public.retail_feature_worker_spans(uuid,uuid,integer)
from public,anon,authenticated;
grant execute on function public.retail_feature_worker_spans(uuid,uuid,integer)
to authenticated;
comment on table retail_private.feature_worker_spans is
'Backend-only checked terminal job observations. Not user-generated browser QA events.';
commit;
