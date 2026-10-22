-- RetailGrowthAI: durable campaign planning persisted in existing PostgreSQL.
-- Apply to RetailGrowthAI DEV only, after coordinator approval; no cloud deployment in CI.
begin;
alter table public.campaigns
  add column media_asset_ids uuid[] not null default '{}'::uuid[],
  add column planning_attempts int not null default 0 check (planning_attempts between 0 and 3),
  add column planning_lease_until timestamptz,
  add column planning_error_code text,
  add constraint campaigns_media_ids_bounds check (cardinality(media_asset_ids) between 0 and 21);
create index campaigns_planning_claim_idx
  on public.campaigns(planning_lease_until,created_at)
  where status='PLANNING' and planning_attempts < 3;

-- Service-role-only atomic claim, SECURITY INVOKER (no privilege escalation).
create function public.claim_campaign_job(p_id uuid)
returns jsonb language plpgsql volatile security invoker set search_path = ''
as $$
declare claimed public.campaigns%rowtype;
begin
  update public.campaigns
     set planning_attempts = planning_attempts + 1,
         planning_lease_until = now() + interval '4 minutes',
         planning_error_code = null
   where id=p_id and status='PLANNING' and planning_attempts<3
     and (planning_lease_until is null or planning_lease_until <= now())
   returning * into claimed;
  if claimed.id is null then return null; end if;
  return to_jsonb(claimed);
end;
$$;
revoke all on function public.claim_campaign_job(uuid) from public, anon, authenticated;
grant execute on function public.claim_campaign_job(uuid) to service_role;
commit;
