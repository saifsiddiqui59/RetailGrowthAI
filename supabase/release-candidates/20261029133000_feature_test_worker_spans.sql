-- SOURCE-ONLY release candidate for RetailGrowthAI DEV. NOT an applied migration.
-- Requires existing canonical Part1 campaigns/render_jobs/rights schema.
-- Browser-observed feature_test_events is unrelated and NEVER considered trusted.
-- Move to the approved canonical migrations inventory ONLY after review/backups.
begin;
create table public.feature_test_worker_spans (
  id uuid primary key default gen_random_uuid(),
  shop_id uuid not null references public.shops(id) on delete cascade,
  job_id uuid not null,
  feature text not null check (feature in ('F2','F4')),
  operation text not null check (operation in (
    'planning.complete','planning.denied','planning.failed','planning.unconfigured',
    'render.complete','render.denied','render.failed')),
  status text not null check (status in ('SUCCEEDED','DENIED','FAILED','UNCONFIGURED')),
  attempt smallint not null check (attempt between 1 and 3),
  elapsed_ms integer not null check (elapsed_ms between 0 and 1800000),
  metadata jsonb not null default '{}'::jsonb
    check (jsonb_typeof(metadata)='object' and octet_length(metadata::text) <= 1600),
  created_at timestamptz not null default now(),
  unique (shop_id,job_id,feature,operation,attempt)
);
create index feature_test_worker_spans_shop_job
 on public.feature_test_worker_spans(shop_id,job_id,created_at desc);
alter table public.feature_test_worker_spans enable row level security;
-- A signed active same-shop OWNER/EDITOR may only READ; never insert fabricated spans.
create policy feature_test_worker_spans_read on public.feature_test_worker_spans
 for select to authenticated using (
  retail_private.has_role(shop_id,array['OWNER','EDITOR'])
 );
revoke all on public.feature_test_worker_spans from public,anon,authenticated;
grant select on public.feature_test_worker_spans to authenticated;
grant select,insert on public.feature_test_worker_spans to service_role;

-- Defense in depth: even a service-authored insert must match the existing
-- authoritative job tenant, fenced attempt, DB result, and exact metadata.
create function retail_private.validate_feature_test_worker_span()
returns trigger language plpgsql security invoker set search_path = '' as $$
declare
  p public.campaigns%rowtype;
  r public.render_jobs%rowtype;
begin
  if new.feature='F2' then
    if new.operation not like 'planning.%' then
      raise exception 'Feature/operation mismatch' using errcode='22023';
    end if;
    select * into p from public.campaigns
      where id=new.job_id and shop_id=new.shop_id;
    if p.id is null or p.planning_attempts<>new.attempt then
      raise exception 'Worker campaign tenant/attempt mismatch' using errcode='42501';
    end if;
    if new.operation='planning.complete' then
      if new.status<>'SUCCEEDED' or p.status not in ('DRAFT','READY')
         or new.metadata <> pg_catalog.jsonb_build_object(
           'generated_days',7,'planner_mode',new.metadata->>'planner_mode')
         or coalesce(new.metadata->>'planner_mode','') not in ('foundry','dev_mock')
         or (select count(*) from public.campaign_days
             where shop_id=new.shop_id and campaign_id=new.job_id)<>7
      then raise exception 'Unverified seven-day completion' using errcode='22023'; end if;
    else
      if new.metadata<>'{}'::jsonb or
         (new.operation='planning.denied' and
          (new.status<>'DENIED' or p.status<>'FAILED' or p.planning_error_code<>'ACCESS_REVOKED')) or
         (new.operation='planning.unconfigured' and
          (new.status<>'UNCONFIGURED' or p.status<>'FAILED' or p.planning_error_code<>'FOUNDRY_NOT_CONFIGURED')) or
         (new.operation='planning.failed' and
          (new.status<>'FAILED' or p.planning_error_code<>'PLANNING_FAILED'))
      then raise exception 'Unverified planning denial/failure' using errcode='22023'; end if;
    end if;
  elsif new.feature='F4' then
    if new.operation not like 'render.%' then
      raise exception 'Feature/operation mismatch' using errcode='22023';
    end if;
    select * into r from public.render_jobs
      where id=new.job_id and shop_id=new.shop_id;
    if r.id is null or r.attempts<>new.attempt then
      raise exception 'Worker render tenant/attempt mismatch' using errcode='42501';
    end if;
    if new.operation='render.complete' then
      if new.status<>'SUCCEEDED' or r.status<>'SUCCEEDED'
         or r.output_asset_id is null
         or new.metadata <> pg_catalog.jsonb_build_object(
           'codec','h264/aac','video_width',1080,'video_height',1920,
           'duration_seconds',new.metadata->'duration_seconds')
         or pg_catalog.jsonb_typeof(new.metadata->'duration_seconds') <> 'number'
         or pg_catalog.abs((new.metadata->>'duration_seconds')::numeric-30)>0.12
      then raise exception 'Unverified private FFmpeg output' using errcode='22023'; end if;
    else
      if new.metadata<>'{}'::jsonb or
         (new.operation='render.denied' and
          (new.status<>'DENIED' or r.status<>'FAILED' or r.error_code<>'ACCESS_REVOKED')) or
         (new.operation='render.failed' and
          (new.status<>'FAILED' or r.error_code<>'RENDER_FAILED'))
      then raise exception 'Unverified render denial/failure' using errcode='22023'; end if;
    end if;
  else
    raise exception 'Unexpected feature' using errcode='22023';
  end if;
  return new;
end
$$;
revoke all on function retail_private.validate_feature_test_worker_span()
 from public,anon,authenticated;
grant execute on function retail_private.validate_feature_test_worker_span()
 to service_role;
create trigger feature_test_worker_span_verify
before insert on public.feature_test_worker_spans
for each row execute function retail_private.validate_feature_test_worker_span();
comment on table public.feature_test_worker_spans is
'Only a trusted service role can insert; trigger requires matching authoritative tenant/fenced job status. NOT browser-observed QA.';
commit;
