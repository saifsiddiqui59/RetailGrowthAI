-- Separate Feature4 v2 service-only outbox dispatcher SOURCE CANDIDATE.
-- Requires cpu_render_jobs and worker_claim candidates. NOT a hosted migration.
begin;

create function public.feature4_claim_cpu_outbox(p_limit integer default 10)
returns jsonb language plpgsql volatile security definer set search_path=''
as $f$
declare result jsonb;
begin
 if p_limit is null or p_limit not between 1 and 20 then
   raise exception 'invalid outbox batch' using errcode='22023'; end if;
 -- Row-level SKIP LOCKED prevents competing timers from double-claiming.
 with picked as (
   select o.id from retail_private.feature4_cpu_outbox o
   join public.feature4_cpu_render_jobs j on j.id=o.job_id
   where j.status in ('QUEUED','RUNNING') and o.attempts<8
     and o.retry_after<=now()
     and (o.state='PENDING' or
          (o.state='CLAIMED' and o.lease_until<now()))
   order by o.created_at,o.id limit p_limit for update of o skip locked
 ), changed as (
   update retail_private.feature4_cpu_outbox o set
     state='CLAIMED',attempts=o.attempts+1,
     lease_token=gen_random_uuid(),lease_until=now()+interval '2 minutes'
   from picked where picked.id=o.id
   returning o.id,o.job_id,o.lease_token
 )
 select coalesce(pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
   'id',id,'job_id',job_id,'lease_token',lease_token)),'[]'::jsonb)
 into result from changed;
 return result;
end $f$;
revoke all on function public.feature4_claim_cpu_outbox(integer)
 from public,anon,authenticated;
grant execute on function public.feature4_claim_cpu_outbox(integer) to service_role;

create function public.feature4_confirm_cpu_outbox(
 p_id uuid,p_lease_token uuid,p_sent boolean)
returns boolean language plpgsql volatile security definer set search_path=''
as $f$
declare n integer;
begin
 if p_id is null or p_lease_token is null or p_sent is null
 then return false; end if;
 update retail_private.feature4_cpu_outbox o set
   state=case when p_sent then 'SENT'
         when o.attempts>=8 then 'DEAD' else 'PENDING' end,
   delivered_at=case when p_sent then now() else o.delivered_at end,
   retry_after=case when p_sent then o.retry_after else
     now()+(pg_catalog.power(2,least(o.attempts,7))
            * interval '1 minute') end,
   lease_token=null,lease_until=null
 where o.id=p_id and o.state='CLAIMED'
   and o.lease_token=p_lease_token and o.lease_until>now()
 returning o.attempts into n;
 return found;
end $f$;
revoke all on function public.feature4_confirm_cpu_outbox(uuid,uuid,boolean)
 from public,anon,authenticated;
grant execute on function public.feature4_confirm_cpu_outbox(uuid,uuid,boolean) to service_role;

create function public.feature4_reconcile_cpu_render(p_limit integer default 20)
returns integer language plpgsql volatile security definer set search_path=''
as $f$
declare n integer;
begin
 if p_limit is null or p_limit not between 1 and 50 then
    raise exception 'invalid reconciliation batch' using errcode='22023'; end if;
 -- Lost queue ACK or crashed workers: reset expired claims.
 with picked as (
   select j.id,j.attempts,o.attempts as sends
   from public.feature4_cpu_render_jobs j
   join retail_private.feature4_cpu_outbox o on o.job_id=j.id
   where (j.status='RUNNING' and j.render_lease_until<now())
      or (j.status='QUEUED' and (
           (o.state='SENT' and o.delivered_at<now()-interval '5 minutes')
           -- A failed eighth send or lost eighth ACK must not strand a
           -- billable reservation as QUEUED with an undeliverable outbox.
           or (o.attempts>=8 and (
                 o.state='DEAD' or
                 (o.state='CLAIMED' and
                   (o.lease_until is null or o.lease_until<now()))))))
   order by j.created_at,j.id limit p_limit for update of j,o skip locked
 ), changed as (
   update public.feature4_cpu_render_jobs j set
     status=case when picked.attempts>=3 or picked.sends>=8
         then 'FAILED' else 'QUEUED' end,
     error_code=case when picked.attempts>=3 or picked.sends>=8
         then 'RETRY_EXHAUSTED' else 'LEASE_EXPIRED' end,
     render_claim_token=null,render_lease_until=null
   from picked where j.id=picked.id returning j.id,j.status
 ), reset as (
   update retail_private.feature4_cpu_outbox o set
     state=case when c.status='FAILED' or o.attempts>=8
         then 'DEAD' else 'PENDING' end,
     retry_after=now(),lease_token=null,lease_until=null
   from changed c where o.job_id=c.id returning o.id
 )
 select pg_catalog.count(*) into n from reset;
 return n;
end $f$;
revoke all on function public.feature4_reconcile_cpu_render(integer)
 from public,anon,authenticated;
grant execute on function public.feature4_reconcile_cpu_render(integer) to service_role;
commit;
