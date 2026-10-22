-- Workstream P: inspection only, for the explicitly named RetailGrowthAI DEV project.
-- Run ONLY after checking the connection points to jeearzffnjbvghwjjjrf.
-- Do not commit actual output containing account data, credentials, or identifiers.
select version, name
from supabase_migrations.schema_migrations
order by version;

select c.relname as public_table, c.relrowsecurity as rls_enabled
from pg_catalog.pg_class c
join pg_catalog.pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relkind = 'r'
order by c.relname;

select schemaname, tablename, policyname, roles, cmd
from pg_catalog.pg_policies
where schemaname = 'public'
order by tablename, policyname;

select grantee, table_name, privilege_type
from information_schema.role_table_grants
where table_schema = 'public' and grantee in ('anon','authenticated','service_role')
order by table_name, grantee, privilege_type;

select id, public, file_size_limit
from storage.buckets
where id = 'retailgrowth-media';

select n.nspname as function_schema, p.proname as function_name,
  p.prosecdef as security_definer, pg_catalog.pg_get_userbyid(p.proowner) as function_owner
from pg_catalog.pg_proc p
join pg_catalog.pg_namespace n on n.oid = p.pronamespace
where n.nspname in ('public','retail_private')
  and p.proname in (
    'claim_campaign_job','claim_render_job','save_campaign_day',
    'register_uploaded_image','claim_outbox_events','confirm_outbox_event',
    'complete_campaign_claim','fail_campaign_claim',
    'complete_render_claim','fail_render_claim',
    'record_poison_event','reconcile_stale_jobs','enqueue_new_job'
  )
order by function_schema, function_name;
