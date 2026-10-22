-- RetailGrowthAI render-job retries and crash-safe worker leases.
begin;
alter table public.render_jobs
  add column render_lease_until timestamptz;
create index render_jobs_unfinished_idx
  on public.render_jobs(shop_id,render_lease_until)
  where status in ('QUEUED','RUNNING') and attempts<3;

create function public.claim_render_job(p_id uuid)
returns jsonb language plpgsql volatile security invoker set search_path = ''
as $$
declare claimed public.render_jobs%rowtype;
begin
  update public.render_jobs
     set status='RUNNING',
         attempts=attempts+1,
         render_lease_until=now()+interval '4 minutes',
         error_code=null
   where id=p_id and status in ('QUEUED','RUNNING') and attempts<3
     and (render_lease_until is null or render_lease_until <= now())
   returning * into claimed;
  if claimed.id is null then return null; end if;
  return to_jsonb(claimed);
end;
$$;
revoke all on function public.claim_render_job(uuid) from public, anon, authenticated;
grant execute on function public.claim_render_job(uuid) to service_role;
commit;
