-- RetailGrowthAI source-only worker time budget adjustment (approval-gated hosted migration).
-- Azure Flex Consumption host budget: 20 minutes; FFmpeg timeout: 780 seconds.
-- Both claim leases must outlive a full host invocation (25 minutes) to prevent
-- a second worker claiming the same job while the first one can still run.
-- Still requires an audited replay/outbox, poison handling and actual DEV benchmarks.
begin;

create or replace function public.claim_campaign_job(p_id uuid)
returns jsonb language plpgsql volatile security invoker set search_path = ''
as $$
declare claimed public.campaigns%rowtype;
begin
  update public.campaigns
     set planning_attempts = planning_attempts + 1,
         planning_lease_until = now() + interval '25 minutes',
         planning_error_code = null
   where id=p_id and status='PLANNING' and planning_attempts<3
     and (planning_lease_until is null or planning_lease_until <= now())
   returning * into claimed;
  if claimed.id is null then return null; end if;
  return to_jsonb(claimed);
end;
$$;

create or replace function public.claim_render_job(p_id uuid)
returns jsonb language plpgsql volatile security invoker set search_path = ''
as $$
declare claimed public.render_jobs%rowtype;
begin
  update public.render_jobs
     set status='RUNNING',
         attempts=attempts+1,
         render_lease_until=now()+interval '25 minutes',
         error_code=null
   where id=p_id and status in ('QUEUED','RUNNING') and attempts<3
     and (render_lease_until is null or render_lease_until <= now())
   returning * into claimed;
  if claimed.id is null then return null; end if;
  return to_jsonb(claimed);
end;
$$;

-- Preserve service-only execution for both existing SECURITY INVOKER functions.
revoke all on function public.claim_campaign_job(uuid) from public, anon, authenticated;
grant execute on function public.claim_campaign_job(uuid) to service_role;
revoke all on function public.claim_render_job(uuid) from public, anon, authenticated;
grant execute on function public.claim_render_job(uuid) to service_role;
commit;
