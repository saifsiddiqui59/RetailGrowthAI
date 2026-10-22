-- RetailGrowthAI Part 1 foundation. Apply ONLY to an isolated RetailGrowthAI Supabase project.
-- Auth is managed by Supabase Auth. No WineShopPOS database or resources are referenced.
begin;
create extension if not exists pgcrypto;
create schema if not exists retail_private;
revoke all on schema retail_private from public, anon;
grant usage on schema retail_private to authenticated;

create table public.shops (
  id uuid primary key default gen_random_uuid(),
  owner_user_id uuid not null references auth.users(id),
  name text not null check (length(trim(name)) between 1 and 140),
  slug text not null unique check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$' and length(slug) between 3 and 60),
  timezone text not null default 'Asia/Kolkata',
  created_at timestamptz not null default now()
);
create table public.shop_memberships (
  shop_id uuid not null references public.shops(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('OWNER','EDITOR','VIEWER')),
  active boolean not null default true,
  created_at timestamptz not null default now(),
  primary key (shop_id, user_id)
);
create index shop_memberships_user_active on public.shop_memberships (user_id, shop_id) where active;

-- Only compares the authenticated JWT subject to membership rows. Never accepts a caller-supplied user id.
-- SECURITY DEFINER is required to avoid recursive membership RLS. Keep it outside exposed schemas.
create function retail_private.has_role(target_shop uuid, allowed_roles text[])
returns boolean language sql stable security definer set search_path = ''
as $$
  select (select auth.uid()) is not null and exists (
    select 1 from public.shop_memberships m
    where m.shop_id = target_shop
      and m.user_id = (select auth.uid())
      and m.active and m.role = any(allowed_roles)
  );
$$;
revoke all on function retail_private.has_role(uuid, text[]) from public, anon;
grant execute on function retail_private.has_role(uuid, text[]) to authenticated;

create table public.business_profiles (
  shop_id uuid primary key references public.shops(id) on delete cascade,
  business_name text not null check (length(trim(business_name)) between 1 and 140),
  category text not null default 'other',
  description text not null default '',
  brand_voice text not null default '',
  city text not null default '',
  website_url text,
  contact_email text,
  updated_at timestamptz not null default now()
);

-- The first OWNER membership/profile is inserted transactionally with the shop.
create function retail_private.bootstrap_shop()
returns trigger language plpgsql security definer set search_path = ''
as $$
begin
  if new.owner_user_id is distinct from (select auth.uid()) then
    raise exception 'shop owner must be the signed-in user' using errcode = '42501';
  end if;
  insert into public.shop_memberships(shop_id,user_id,role)
    values (new.id,new.owner_user_id,'OWNER');
  insert into public.business_profiles(shop_id,business_name)
    values (new.id,new.name);
  return new;
end;
$$;
revoke all on function retail_private.bootstrap_shop() from public, anon, authenticated;
create trigger bootstrap_shop_after_insert after insert on public.shops
for each row execute function retail_private.bootstrap_shop();

create table public.brand_kits (
  id uuid primary key default gen_random_uuid(),
  shop_id uuid not null references public.shops(id) on delete cascade,
  name text not null default 'Default',
  primary_color text,
  secondary_color text,
  logo_asset_id uuid,
  created_at timestamptz not null default now(),
  unique (shop_id,id)
);
create index brand_kits_shop on public.brand_kits(shop_id);

create table public.media_assets (
  id uuid primary key default gen_random_uuid(),
  shop_id uuid not null references public.shops(id) on delete cascade,
  created_by uuid not null references auth.users(id),
  storage_bucket text not null default 'retailgrowth-media' check (storage_bucket = 'retailgrowth-media'),
  object_path text not null,
  mime_type text not null,
  source text not null check (source in ('UPLOAD','STOCK','GENERATED')),
  license_name text,
  license_url text,
  attribution text,
  created_at timestamptz not null default now(),
  unique (shop_id,id),
  unique (storage_bucket,object_path),
  check (object_path like (shop_id::text || '/%')),
  check (length(object_path) < 500)
);
create index media_assets_shop on public.media_assets(shop_id);
alter table public.brand_kits add constraint brand_kits_logo_tenant
  foreign key (shop_id,logo_asset_id) references public.media_assets(shop_id,id);

create table public.campaigns (
  id uuid primary key default gen_random_uuid(),
  shop_id uuid not null references public.shops(id) on delete cascade,
  created_by uuid not null references auth.users(id),
  brief text not null check (length(trim(brief)) between 1 and 10000),
  duration_days integer not null default 7 check (duration_days between 1 and 7),
  start_date date not null,
  timezone text not null default 'Asia/Kolkata',
  language text not null default 'en-IN',
  platforms text[] not null default array['linkedin','instagram']::text[],
  offer jsonb,
  status text not null default 'PLANNING'
    check (status in ('PLANNING','DRAFT','READY','FAILED')),
  created_at timestamptz not null default now(),
  unique (shop_id,id),
  check (platforms <@ array['linkedin','instagram']::text[] and cardinality(platforms) between 1 and 2)
);
create index campaigns_shop_recent on public.campaigns(shop_id,created_at desc);
create table public.campaign_days (
  id uuid primary key default gen_random_uuid(),
  campaign_id uuid not null,
  shop_id uuid not null,
  day_index integer not null check (day_index between 1 and 7),
  scheduled_date date not null,
  topic text not null,
  linkedin jsonb not null default '{}'::jsonb,
  instagram jsonb not null default '{}'::jsonb,
  review_status text not null default 'DRAFT' check (review_status in ('DRAFT','APPROVED','REJECTED')),
  created_at timestamptz not null default now(),
  foreign key (shop_id,campaign_id) references public.campaigns(shop_id,id) on delete cascade,
  unique (shop_id,id),
  unique (campaign_id,day_index)
);
create index campaign_days_shop_campaign on public.campaign_days(shop_id,campaign_id);

create table public.render_jobs (
  id uuid primary key default gen_random_uuid(),
  shop_id uuid not null,
  campaign_id uuid not null,
  day_id uuid not null,
  requested_by uuid not null references auth.users(id),
  preset text not null check (preset = 'instagram_reel_30s'),
  status text not null default 'QUEUED' check (status in ('QUEUED','RUNNING','SUCCEEDED','FAILED')),
  idempotency_key text not null check (length(idempotency_key) between 1 and 128),
  attempts integer not null default 0 check (attempts between 0 and 3),
  output_asset_id uuid,
  error_code text,
  created_at timestamptz not null default now(),
  foreign key (shop_id,campaign_id) references public.campaigns(shop_id,id) on delete cascade,
  foreign key (shop_id,day_id) references public.campaign_days(shop_id,id),
  foreign key (shop_id,output_asset_id) references public.media_assets(shop_id,id),
  unique (shop_id,idempotency_key)
);
create index render_jobs_shop_recent on public.render_jobs(shop_id,created_at desc);

-- Backend-written append-only billing/audit data; browsers receive SELECT only.
create table public.usage_events (
  id uuid primary key default gen_random_uuid(),
  shop_id uuid not null references public.shops(id) on delete cascade,
  job_id uuid,
  kind text not null,
  units numeric(14,4) not null check (units >= 0),
  created_at timestamptz not null default now(),
  unique(shop_id,job_id,kind),
  foreign key (shop_id,job_id) references public.render_jobs(shop_id,id)
);
create index usage_events_shop_recent on public.usage_events(shop_id,created_at desc);
create table public.audit_logs (
  id uuid primary key default gen_random_uuid(),
  shop_id uuid not null references public.shops(id) on delete cascade,
  actor_user_id uuid references auth.users(id),
  action text not null,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index audit_logs_shop_recent on public.audit_logs(shop_id,created_at desc);

-- All public entities deny by default; policies below are affirmative and shop-scoped.
alter table public.shops enable row level security;
alter table public.shop_memberships enable row level security;
alter table public.business_profiles enable row level security;
alter table public.brand_kits enable row level security;
alter table public.media_assets enable row level security;
alter table public.campaigns enable row level security;
alter table public.campaign_days enable row level security;
alter table public.render_jobs enable row level security;
alter table public.usage_events enable row level security;
alter table public.audit_logs enable row level security;

create policy shops_read on public.shops for select to authenticated
using (retail_private.has_role(id,array['OWNER','EDITOR','VIEWER']));
create policy shops_create on public.shops for insert to authenticated
with check (owner_user_id = (select auth.uid()));
create policy shops_edit on public.shops for update to authenticated
using (retail_private.has_role(id,array['OWNER']))
with check (retail_private.has_role(id,array['OWNER']));

create policy members_read on public.shop_memberships for select to authenticated
using (user_id = (select auth.uid()) or retail_private.has_role(shop_id,array['OWNER']));
create policy members_invite on public.shop_memberships for insert to authenticated
with check (role in ('EDITOR','VIEWER') and retail_private.has_role(shop_id,array['OWNER']));
create policy members_edit on public.shop_memberships for update to authenticated
using (role in ('EDITOR','VIEWER') and retail_private.has_role(shop_id,array['OWNER']))
with check (role in ('EDITOR','VIEWER') and retail_private.has_role(shop_id,array['OWNER']));
create policy members_remove on public.shop_memberships for delete to authenticated
using (role in ('EDITOR','VIEWER') and retail_private.has_role(shop_id,array['OWNER']));

create policy profiles_read on public.business_profiles for select to authenticated
using (retail_private.has_role(shop_id,array['OWNER','EDITOR','VIEWER']));
create policy profiles_edit on public.business_profiles for update to authenticated
using (retail_private.has_role(shop_id,array['OWNER','EDITOR']))
with check (retail_private.has_role(shop_id,array['OWNER','EDITOR']));

create policy brand_read on public.brand_kits for select to authenticated
using (retail_private.has_role(shop_id,array['OWNER','EDITOR','VIEWER']));
create policy brand_create on public.brand_kits for insert to authenticated
with check (retail_private.has_role(shop_id,array['OWNER','EDITOR']));
create policy brand_edit on public.brand_kits for update to authenticated
using (retail_private.has_role(shop_id,array['OWNER','EDITOR']))
with check (retail_private.has_role(shop_id,array['OWNER','EDITOR']));
create policy brand_remove on public.brand_kits for delete to authenticated
using (retail_private.has_role(shop_id,array['OWNER','EDITOR']));

create policy assets_read on public.media_assets for select to authenticated
using (retail_private.has_role(shop_id,array['OWNER','EDITOR','VIEWER']));
create policy assets_create on public.media_assets for insert to authenticated
with check (created_by = (select auth.uid())
  and retail_private.has_role(shop_id,array['OWNER','EDITOR']));
create policy assets_edit on public.media_assets for update to authenticated
using (retail_private.has_role(shop_id,array['OWNER','EDITOR']))
with check (retail_private.has_role(shop_id,array['OWNER','EDITOR']));
create policy assets_remove on public.media_assets for delete to authenticated
using (retail_private.has_role(shop_id,array['OWNER','EDITOR']));

create policy campaigns_read on public.campaigns for select to authenticated
using (retail_private.has_role(shop_id,array['OWNER','EDITOR','VIEWER']));
create policy campaigns_create on public.campaigns for insert to authenticated
with check (created_by = (select auth.uid())
  and retail_private.has_role(shop_id,array['OWNER','EDITOR']));
create policy campaigns_edit on public.campaigns for update to authenticated
using (retail_private.has_role(shop_id,array['OWNER','EDITOR']))
with check (retail_private.has_role(shop_id,array['OWNER','EDITOR']));
create policy days_read on public.campaign_days for select to authenticated
using (retail_private.has_role(shop_id,array['OWNER','EDITOR','VIEWER']));
create policy days_edit on public.campaign_days for update to authenticated
using (retail_private.has_role(shop_id,array['OWNER','EDITOR']))
with check (retail_private.has_role(shop_id,array['OWNER','EDITOR']));
create policy jobs_read on public.render_jobs for select to authenticated
using (retail_private.has_role(shop_id,array['OWNER','EDITOR','VIEWER']));
create policy usage_read on public.usage_events for select to authenticated
using (retail_private.has_role(shop_id,array['OWNER']));
create policy audit_read on public.audit_logs for select to authenticated
using (retail_private.has_role(shop_id,array['OWNER']));

-- Table grants alone are not row security: RLS AND column-level grants are both required.
revoke all on public.shops, public.shop_memberships, public.business_profiles,
  public.brand_kits, public.media_assets, public.campaigns, public.campaign_days,
  public.render_jobs, public.usage_events, public.audit_logs from anon, authenticated;
grant select, insert on public.shops to authenticated;
grant update(name,slug,timezone) on public.shops to authenticated;
grant select, insert, delete on public.shop_memberships to authenticated;
grant update(role,active) on public.shop_memberships to authenticated;
grant select on public.business_profiles to authenticated;
grant update(business_name,category,description,brand_voice,city,website_url,contact_email,updated_at)
  on public.business_profiles to authenticated;
grant select, insert, delete on public.brand_kits to authenticated;
grant update(name,primary_color,secondary_color,logo_asset_id) on public.brand_kits to authenticated;
grant select, insert, delete on public.media_assets to authenticated;
grant update(license_name,license_url,attribution) on public.media_assets to authenticated;
grant select, insert on public.campaigns to authenticated;
grant update(brief,start_date,timezone,language,platforms,offer) on public.campaigns to authenticated;
grant select on public.campaign_days to authenticated;
grant update(topic,linkedin,instagram,review_status) on public.campaign_days to authenticated;
grant select on public.render_jobs, public.usage_events, public.audit_logs to authenticated;

-- Protect rows of FUTURE public tables by explicit migration review, not permissive defaults.
commit;
