-- F4 v2 poison receipts, source-only; never changes legacy queue or
-- trusts a poisoned queue payload for tenant, billing or authorization.
begin;
create table retail_private.feature4_cpu_poison_receipts (
 fingerprint text primary key check(fingerprint ~ '^[0-9a-f]{64}$'),
 possible_job_id uuid,
 received_at timestamptz not null default now()
);
revoke all on retail_private.feature4_cpu_poison_receipts
  from public,anon,authenticated;
grant select on retail_private.feature4_cpu_poison_receipts to service_role;

create function public.feature4_record_cpu_poison(
 p_fingerprint text,p_job_id uuid default null)
returns boolean language plpgsql volatile security definer set search_path=''
as $f$
begin
 if p_fingerprint is null or p_fingerprint !~ '^[0-9a-f]{64}$'
 then return false; end if;
 insert into retail_private.feature4_cpu_poison_receipts(
     fingerprint,possible_job_id)
 values(p_fingerprint,p_job_id)
 on conflict (fingerprint) do nothing;
 -- Do NOT directly modify jobs from possibly malformed/attacker-sent payload.
 -- The separate bounded reconciler owns recovery after persisted evidence.
 return true;
end $f$;
revoke all on function public.feature4_record_cpu_poison(text,uuid)
 from public,anon,authenticated;
grant execute on function public.feature4_record_cpu_poison(text,uuid)
 to service_role;
commit;
