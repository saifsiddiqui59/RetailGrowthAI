-- Repair existing DEV poster dispatcher: public service RPCs are SECURITY INVOKER
-- and access the private outbox with service_role, which lacked schema USAGE.
-- Maintain row/table GRANTs and all existing RLS; no browser role receives access.
-- This is an additive RetailGrowthAI-only schema privilege migration.
begin;
grant usage on schema retail_private to service_role;
commit;
