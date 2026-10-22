-- Harden the RetailGrowthAI project and index foreign key relationships.
-- Supabase may pre-create the public RLS-auto-enable event-trigger helper.
-- Event-trigger functions are not browser APIs: revoke API-role execution if it exists.
begin;
do $$
begin
  if to_regprocedure('public.rls_auto_enable()') is not null then
    revoke execute on function public.rls_auto_enable() from public, anon, authenticated;
  end if;
end $$;

create index if not exists shops_owner_user_idx on public.shops(owner_user_id);
create index if not exists brand_kits_logo_tenant_idx on public.brand_kits(shop_id,logo_asset_id);
create index if not exists media_assets_creator_idx on public.media_assets(created_by);
create index if not exists campaigns_creator_idx on public.campaigns(created_by);
create index if not exists render_jobs_requester_idx on public.render_jobs(requested_by);
create index if not exists render_jobs_campaign_tenant_idx on public.render_jobs(shop_id,campaign_id);
create index if not exists render_jobs_day_tenant_idx on public.render_jobs(shop_id,day_id);
create index if not exists render_jobs_output_tenant_idx on public.render_jobs(shop_id,output_asset_id);
create index if not exists audit_logs_actor_idx on public.audit_logs(actor_user_id);
commit;
