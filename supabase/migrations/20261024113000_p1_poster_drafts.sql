-- Part 1 poster draft metadata only. This migration does not create render jobs,
-- public media, paid usage or any publishing path. Apply ONLY to RetailGrowthAI
-- after separate approved DEV gate and disposable security regressions.
begin;

create table public.poster_drafts (
  id uuid primary key default gen_random_uuid(),
  shop_id uuid not null,
  campaign_id uuid not null,
  day_id uuid not null,
  created_by uuid not null references auth.users(id),
  source_asset_id uuid not null,
  logo_asset_id uuid,
  template text not null check (template in ('editorial','bold','minimal')),
  format text not null check (format in ('square','portrait')),
  business_name text not null check (length(trim(business_name)) between 1 and 70),
  accent_color text not null check (accent_color ~ '^#[0-9A-Fa-f]{6}$'),
  background_color text not null check (background_color ~ '^#[0-9A-Fa-f]{6}$'),
  offer_text text check (offer_text is null or length(trim(offer_text)) between 1 and 110),
  idempotency_key text not null check (idempotency_key ~ '^[0-9a-f]{64}$'),
  status text not null default 'DRAFT' check (status in ('DRAFT','RENDERING','READY','FAILED')),
  revision integer not null default 1 check (revision > 0),
  output_asset_id uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  foreign key (shop_id,campaign_id) references public.campaigns(shop_id,id) on delete cascade,
  foreign key (shop_id,day_id) references public.campaign_days(shop_id,id) on delete cascade,
  foreign key (shop_id,source_asset_id) references public.media_assets(shop_id,id),
  foreign key (shop_id,logo_asset_id) references public.media_assets(shop_id,id),
  foreign key (shop_id,output_asset_id) references public.media_assets(shop_id,id),
  unique (shop_id,id),
  unique (shop_id,idempotency_key)
);
create index poster_drafts_shop_campaign on public.poster_drafts(shop_id,campaign_id,created_at desc);
create index poster_drafts_shop_day on public.poster_drafts(shop_id,day_id,created_at desc);

alter table public.poster_drafts enable row level security;
revoke all on table public.poster_drafts from public, anon, authenticated;
grant select on public.poster_drafts to authenticated;
grant all on public.poster_drafts to service_role;
create policy poster_drafts_member_read on public.poster_drafts
  for select to authenticated
  using (retail_private.has_role(shop_id,array['OWNER','EDITOR','VIEWER']));

-- Even a malicious authenticated client cannot INSERT fake output links, update
-- readiness, bypass rights or claim another tenant. No direct write grants.
create function public.create_poster_draft(
  p_shop_id uuid, p_campaign_id uuid, p_day_id uuid,
  p_source_asset_id uuid, p_logo_asset_id uuid,
  p_template text, p_format text, p_business_name text,
  p_accent_color text, p_background_color text, p_offer_text text
)
returns uuid language plpgsql volatile security definer set search_path = ''
as $$
declare
  actor uuid := (select auth.uid());
  allowed boolean;
  source_ok boolean;
  logo_ok boolean;
  fingerprint text;
  result_id uuid;
begin
  -- Check the active owner/editor JWT, not caller-supplied claimed actor IDs.
  if (select auth.role()) is distinct from 'authenticated'
     or actor is null or p_shop_id is null
     or not retail_private.has_role(p_shop_id,array['OWNER','EDITOR']) then
    return null;
  end if;

  -- Input and length guards before any DB writes or costly work.
  if p_template is null or p_template not in ('editorial','bold','minimal')
     or p_format is null or p_format not in ('square','portrait')
     or p_business_name is null or length(trim(p_business_name)) not between 1 and 70
     or p_business_name ~ '[[:cntrl:]]'
     or p_accent_color is null or p_accent_color !~ '^#[0-9A-Fa-f]{6}$'
     or p_background_color is null or p_background_color !~ '^#[0-9A-Fa-f]{6}$'
     or (p_offer_text is not null and
         (length(trim(p_offer_text)) not between 1 and 110
          or p_offer_text ~ '[[:cntrl:]]')) then
    return null;
  end if;

  -- The source MUST be included in the *saved* campaign storyboard.
  -- Editing browser-local JSON cannot authorize arbitrary new media IDs.
  select exists (
    select 1 from public.campaigns c
    join public.campaign_days d on d.campaign_id = c.id and d.shop_id = c.shop_id
    where c.shop_id=p_shop_id and c.id=p_campaign_id
      and c.status='DRAFT' and d.id=p_day_id and d.review_status='DRAFT'
      and exists (
        select 1 from jsonb_array_elements(
          case when jsonb_typeof(d.instagram #> '{reel,storyboard}')='array'
               then d.instagram #> '{reel,storyboard}'
               else '[]'::jsonb end
        ) as segments(asset)
        where segments.asset->>'asset_id'=p_source_asset_id::text
      )
  ) into allowed;
  if not allowed then return null; end if;

  -- Declared commercial rights + same-shop source/image are necessary;
  -- independent license evidence review is still required before publishing.
  select exists (
    select 1 from public.media_assets a
     where a.id=p_source_asset_id and a.shop_id=p_shop_id
       and a.storage_bucket='retailgrowth-media'
       and a.mime_type in ('image/png','image/jpeg','image/webp')
       and a.license_name in ('owned','cc0','commercial','royalty_free')
       and length(trim(coalesce(a.attribution,''))) >= 10
       and (a.license_name='owned' or coalesce(a.license_url,'') ~ '^https://')
  ) into source_ok;
  if not source_ok then return null; end if;

  if p_logo_asset_id is not null then
    select exists(
      select 1 from public.media_assets a
      where a.id=p_logo_asset_id and a.shop_id=p_shop_id
        and a.storage_bucket='retailgrowth-media'
        and a.mime_type in ('image/png','image/jpeg','image/webp')
        and a.license_name in ('owned','cc0','commercial','royalty_free')
        and length(trim(coalesce(a.attribution,''))) >= 10
        and (a.license_name='owned' or coalesce(a.license_url,'') ~ '^https://')
    ) into logo_ok;
    if not logo_ok then return null; end if;
  end if;

  -- Serialize same-shop draft creation against the trusted entitlement row.
  -- A hard cap on metadata prevents unbounded client-side spam; it does not
  -- count as a new billable render or change the existing quota ledger.
  perform 1 from public.shop_subscriptions s
   where s.shop_id=p_shop_id and s.status in ('TRIAL','ACTIVE')
     and now() between s.valid_from and s.valid_until
     and now() between s.period_start and s.period_end
   for update;
  if not found then return null; end if;

  fingerprint := encode(pg_catalog.sha256(pg_catalog.convert_to(
    jsonb_build_object('actor',actor,'shop',p_shop_id,'campaign',p_campaign_id,
      'day',p_day_id,'source',p_source_asset_id,'logo',p_logo_asset_id,
      'template',p_template,'format',p_format,'brand',trim(p_business_name),
      'accent',p_accent_color,'background',p_background_color,
      'offer',nullif(trim(p_offer_text),''))::text, 'UTF8')), 'hex');

  -- Idempotent previews of the *same* parameters always reuse one draft.
  select id into result_id from public.poster_drafts
   where shop_id=p_shop_id and idempotency_key=fingerprint;
  if result_id is not null then return result_id; end if;
  if (select count(*) from public.poster_drafts
      where shop_id=p_shop_id and campaign_id=p_campaign_id) >= 21 then
    return null;
  end if;

  insert into public.poster_drafts
    (shop_id,campaign_id,day_id,created_by,source_asset_id,logo_asset_id,
     template,format,business_name,accent_color,background_color,
     offer_text,idempotency_key)
  values
    (p_shop_id,p_campaign_id,p_day_id,actor,p_source_asset_id,p_logo_asset_id,
     p_template,p_format,trim(p_business_name),p_accent_color,p_background_color,
     nullif(trim(p_offer_text),''),fingerprint)
  returning id into result_id;
  return result_id;
end;
$$;
revoke all on function public.create_poster_draft(uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,text)
  from public, anon, authenticated;
grant execute on function public.create_poster_draft(uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,text)
  to authenticated;

-- Generated asset linking, role recheck, worker claim, revision save and
-- private signed download are deliberately NOT enabled by this migration.
commit;
