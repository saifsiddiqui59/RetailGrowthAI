-- Additive Feature #3 catalog + local v2 poster DESIGN persistence (source only).
-- Rebased timestamp AFTER already-applied 20261026194000 Feature2 ledger.\n-- No third-party approval, GPU, queue, export or paid cloud action.
-- Runtime must retain v1 poster_drafts/poster_jobs unchanged.
begin;

create table public.feature3_models (
  model_id uuid primary key,
  owner_shop_id uuid not null references public.shops(id) on delete cascade,
  created_by uuid not null references auth.users(id),
  media_asset_id uuid not null,
  scope text not null check(scope in ('shop','platform')),
  status text not null default 'PENDING_REVIEW'
    check(status in ('PENDING_REVIEW','APPROVED','REJECTED','REVOKED')),
  source_kind text not null check(source_kind in ('opensource_render','created_ai','retailer_licensed')),
  label text not null check(length(trim(label)) between 1 and 64),
  image_sha256 text not null check(image_sha256 ~ '^[0-9a-f]{64}$'),
  license_id text not null check(license_id in ('CC0-1.0','CC-BY-4.0','REVIEWED-COMMERCIAL')),
  license_evidence_sha256 text not null check(license_evidence_sha256 ~ '^[0-9a-f]{64}$'),
  rights_verified boolean not null default false,
  synthetic_adult boolean not null default true check(synthetic_adult is true),
  attribution text not null default '' check(length(attribution) <= 200),
  approved_uses text[] not null default array['poster']::text[]
    check(approved_uses <@ array['poster','try_on','video_reference']::text[]
          and cardinality(approved_uses) between 1 and 3),
  rights_revision integer not null default 1 check(rights_revision >= 1),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  foreign key(owner_shop_id,media_asset_id)
    references public.media_assets(shop_id,id),
  unique(owner_shop_id,model_id),
  constraint f3_model_approved_rights check (
    status <> 'APPROVED' or
    (rights_verified and
     (license_id <> 'CC-BY-4.0' or length(trim(attribution)) > 0))
  )
);
create index f3_models_owner_scope on public.feature3_models(owner_shop_id,scope,status);
alter table public.feature3_models enable row level security;
revoke all on table public.feature3_models from public,anon,authenticated;
grant select on table public.feature3_models to authenticated;
grant all on table public.feature3_models to service_role;
-- A platform-wide entry only reveals metadata, not the owner's media bytes.
-- Actual private image materialization requires a distinct per-request shop grant.
create policy f3_models_visible on public.feature3_models
for select to authenticated using (
 (scope='shop' and retail_private.has_role(owner_shop_id,array['OWNER','EDITOR','VIEWER']))
 or (scope='platform' and status='APPROVED' and rights_verified and
   exists(select 1 from public.shop_memberships m where m.user_id=(select auth.uid()) and m.active))
);

create table public.feature3_poster_designs (
  id uuid primary key default gen_random_uuid(),
  shop_id uuid not null,
  campaign_id uuid not null,
  day_id uuid not null,
  created_by uuid not null references auth.users(id),
  variation_of uuid,
  revision integer not null default 1 check(revision between 1 and 1000000),
  status text not null default 'DRAFT' check(status in ('DRAFT','APPROVED','REJECTED')),
  design jsonb not null,
  server_document_sha256 text not null check(server_document_sha256 ~ '^[0-9a-f]{64}$'),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(shop_id,id),
  foreign key(shop_id,campaign_id) references public.campaigns(shop_id,id) on delete cascade,
  foreign key(shop_id,day_id) references public.campaign_days(shop_id,id) on delete cascade,
  foreign key(shop_id,variation_of) references public.feature3_poster_designs(shop_id,id),
  constraint f3_design_document_schema check(
    design->>'schema'='retailgrowth.poster.v2' and
    design->>'shop_id'=shop_id::text)
);
create index f3_design_day on public.feature3_poster_designs(shop_id,day_id,updated_at desc);
alter table public.feature3_poster_designs enable row level security;
revoke all on table public.feature3_poster_designs from public,anon,authenticated;
grant select on table public.feature3_poster_designs to authenticated;
grant all on table public.feature3_poster_designs to service_role;
create policy f3_design_member_read on public.feature3_poster_designs
for select to authenticated
using(retail_private.has_role(shop_id,array['OWNER','EDITOR','VIEWER']));

-- Strict JSON shape + bounds; only server validates/commits trusted design bytes.
create function retail_private.feature3_valid_design(d jsonb, shop uuid)
returns boolean language plpgsql stable security definer set search_path='' as $$
declare
  layer jsonb;
  kind text;
  k text;
  expected_keys text[];
  ids text[] := array[]::text[];
begin
  if d is null or jsonb_typeof(d) is distinct from 'object'
   or pg_catalog.octet_length(d::text)>16384
   or (select array_agg(key order by key) from jsonb_object_keys(d) as key) is distinct from
      array['background','format','layers','schema','shop_id','template']
   or d->>'schema' is distinct from 'retailgrowth.poster.v2'
   or d->>'shop_id' is distinct from shop::text
   or coalesce(d->>'format' in ('square','portrait','story'),false) is not true
   or coalesce(d->>'template' in
      ('fashion','luxury','streetwear','ethnic','festival','restaurant','general','new_arrivals','clearance','seasonal'),false) is not true
   or coalesce(d->>'background' ~ '^#[0-9a-fA-F]{6}$',false) is not true
   or jsonb_typeof(d->'layers') is distinct from 'array'
   or jsonb_array_length(d->'layers') not between 1 and 24 then
    return false;
  end if;
  for layer in select value from jsonb_array_elements(d->'layers') as value loop
    kind := layer->>'type';
    if kind='text' then
      expected_keys := array['bold','color','font_size','h','id','text','type','w','x','y'];
    elsif kind='rect' then
      expected_keys := array['color','h','id','type','w','x','y'];
    elsif kind='image' then
      expected_keys := array['asset_id','h','id','type','w','x','y'];
    else
      return false;
    end if;
    if jsonb_typeof(layer) is distinct from 'object'
      or coalesce(layer->>'id' ~ '^[A-Za-z0-9_-]{1,48}$',false) is not true
      or ids @> array[layer->>'id']
      or (select array_agg(key order by key) from jsonb_object_keys(layer) as key)
          is distinct from expected_keys
    then return false; end if;
    ids := ids || (layer->>'id');
    foreach k in array array['x','y','w','h'] loop
      if jsonb_typeof(layer->k) is distinct from 'number'
       or (layer->>k)::numeric < 0 or (layer->>k)::numeric > 1
       or (k in ('w','h') and (layer->>k)::numeric < .01) then
        return false;
      end if;
    end loop;
    if (layer->>'x')::numeric + (layer->>'w')::numeric > 1.00001
       or (layer->>'y')::numeric + (layer->>'h')::numeric > 1.00001 then return false; end if;
    if kind='text' and (
        layer->>'text' is null or length(trim(layer->>'text')) not between 1 and 160
        or layer->>'text' ~ '[[:cntrl:]]'
        or coalesce(layer->>'color' ~ '^#[0-9a-fA-F]{6}$',false) is not true
        or jsonb_typeof(layer->'font_size') is distinct from 'number'
        or (layer->>'font_size')::numeric not between 12 and 150
        or (layer->>'font_size')::numeric <> trunc((layer->>'font_size')::numeric)
        or jsonb_typeof(layer->'bold') is distinct from 'boolean'
      ) then return false; end if;
    if kind='rect' and
       coalesce(layer->>'color' ~ '^#[0-9a-fA-F]{6}$',false) is not true
       then return false; end if;
    if kind='image' and
       coalesce(layer->>'asset_id' ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',false) is not true
       then return false; end if;
  end loop;
  return true;
exception when invalid_text_representation or numeric_value_out_of_range then return false;
end $$;
revoke all on function retail_private.feature3_valid_design(jsonb,uuid) from public,anon,authenticated;


-- CAS-only browser write; never mutate APPROVED designs or render/publish.
-- On uncertain transport failure read user-RLS design by ID before retrying.
create function public.save_feature3_poster_design(
 p_shop_id uuid,p_campaign_id uuid,p_day_id uuid,p_design jsonb,
 p_id uuid default null,p_expected_revision int default 0,p_variation_of uuid default null
) returns jsonb language plpgsql volatile security definer set search_path='' as $$
declare actor uuid := (select auth.uid());
  current_row public.feature3_poster_designs%rowtype;
  source public.feature3_poster_designs%rowtype;
  result_id uuid;
  server_sha text;
  item jsonb;
  asset uuid;
begin
  if actor is null
     or not retail_private.has_role(p_shop_id,array['OWNER','EDITOR'])
     or p_expected_revision is null or p_expected_revision not between 0 and 1000000
     or p_shop_id is null or p_campaign_id is null or p_day_id is null
     or not retail_private.feature3_valid_design(p_design,p_shop_id) then return null; end if;
  -- Keep server-side approval/campaign-day semantics authoritative.
  if not exists(select 1 from public.campaigns c join public.campaign_days d
      on d.shop_id=c.shop_id and d.campaign_id=c.id
      where c.shop_id=p_shop_id and c.id=p_campaign_id
       and c.status='DRAFT' and d.id=p_day_id and d.review_status='DRAFT')
    then return null; end if;
  -- Per-client metadata writes require an active trial/subscription lock.
  perform 1 from public.shop_subscriptions s where s.shop_id=p_shop_id
    and s.status in ('TRIAL','ACTIVE')
    and now()>=s.valid_from and now()<s.valid_until
    and now()>=s.period_start and now()<s.period_end for update;
  if not found then return null; end if;
  for item in select value from jsonb_array_elements(p_design->'layers') as value loop
    if item->>'type'='image' then
      asset := (item->>'asset_id')::uuid;
      if not exists (select 1 from public.media_assets a where a.shop_id=p_shop_id
         and a.id=asset and a.storage_bucket='retailgrowth-media'
         and a.mime_type in ('image/png','image/jpeg','image/webp')
         and a.license_name in ('owned','cc0','royalty_free','commercial')
         and length(trim(coalesce(a.attribution,'')))>=10
         and (a.license_name='owned' or a.license_url like 'https://%'))
      then return null; end if;
    end if;
  end loop;
  -- This is the Postgres JSONB digest, NOT the Python canonical JSON SHA.
  -- Coordinator must reconcile digests in the render pipeline before enabling it.
  server_sha := encode(pg_catalog.sha256(pg_catalog.convert_to(p_design::text,'UTF8')),'hex');
  if p_variation_of is not null then
     if p_id is not null or p_expected_revision<>0 then return null; end if;
     select * into source from public.feature3_poster_designs
       where id=p_variation_of and shop_id=p_shop_id
         and campaign_id=p_campaign_id and day_id=p_day_id for update;
     if not found or source.status not in ('DRAFT','APPROVED') then return null; end if;
  end if;
  if p_id is null then
    if p_expected_revision<>0 then return null; end if;
    if (select count(*) from public.feature3_poster_designs
        where shop_id=p_shop_id and campaign_id=p_campaign_id)>=50 then return null; end if;
    insert into public.feature3_poster_designs
      (shop_id,campaign_id,day_id,created_by,variation_of,design,server_document_sha256)
    values(p_shop_id,p_campaign_id,p_day_id,actor,p_variation_of,p_design,server_sha)
      returning id into result_id;
    return jsonb_build_object('design_id',result_id,'revision',1,'server_document_sha256',server_sha);
  end if;
  if p_variation_of is not null then return null; end if;
  select * into current_row from public.feature3_poster_designs
    where id=p_id and shop_id=p_shop_id
     and campaign_id=p_campaign_id and day_id=p_day_id for update;
  if not found or current_row.status<>'DRAFT'
     or current_row.revision<>p_expected_revision
     or current_row.revision>=1000000 then return null; end if;
  update public.feature3_poster_designs
    set design=p_design,server_document_sha256=server_sha,
        revision=revision+1,updated_at=now()
    where id=current_row.id returning id into result_id;
  return jsonb_build_object('design_id',result_id,'revision',p_expected_revision+1,
                            'server_document_sha256',server_sha);
end $$;
revoke all on function public.save_feature3_poster_design(uuid,uuid,uuid,jsonb,uuid,int,uuid)
  from public,anon,authenticated;
grant execute on function public.save_feature3_poster_design(uuid,uuid,uuid,jsonb,uuid,int,uuid)
  to authenticated;

-- Not yet part of the v1 renderer/job queue or signed download APIs.
commit;
