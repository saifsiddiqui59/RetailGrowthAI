-- RetailGrowthAI-only draft-save RPC. Do NOT apply to WineShopPOS.
-- Only authenticated OWNER/EDITOR can change editable fields of DRAFT days.
-- The server validates the full campaign v1 contract before invoking this RPC.
begin;

-- Browser access to direct day mutations would bypass optimistic concurrency and
-- the parent DRAFT gate; all writes must pass through this restricted RPC.
revoke update(topic,linkedin,instagram,review_status)
  on public.campaign_days from authenticated;

create function public.save_campaign_day(
  p_shop_id uuid, p_campaign_id uuid, p_day_id uuid,
  p_expected jsonb, p_changes jsonb
)
returns boolean
language plpgsql volatile security definer set search_path = ''
as $$
declare
  current_day public.campaign_days%rowtype;
  active_campaign public.campaigns%rowtype;
  updated_count integer;
begin
  if (select auth.uid()) is null
     or not retail_private.has_role(p_shop_id, array['OWNER','EDITOR']) then
    return false;
  end if;
  if p_expected is null or p_changes is null
     or jsonb_typeof(p_expected) <> 'object'
     or jsonb_typeof(p_changes) <> 'object'
     or not (p_expected ?& array['topic','linkedin','instagram'])
     or not (p_changes ?& array['topic','linkedin','instagram'])
     or (select count(*) from jsonb_object_keys(p_changes)) <> 3
     or jsonb_typeof(p_changes->'topic') <> 'string'
     or length(trim(p_changes->>'topic')) not between 1 and 140
     or jsonb_typeof(p_changes->'linkedin') <> 'object'
     or jsonb_typeof(p_changes->'instagram') <> 'object'
     or length(p_changes::text) > 20000 then
    return false;
  end if;

  -- A single transaction protects the checked parent and day against edits to
  -- non-DRAFT campaigns; UPDATE below compares original editable values.
  select * into active_campaign from public.campaigns
   where id = p_campaign_id and shop_id = p_shop_id and status = 'DRAFT'
   for share;
  if not found then return false; end if;

  select * into current_day from public.campaign_days
   where id = p_day_id and campaign_id = p_campaign_id and shop_id = p_shop_id
     and review_status = 'DRAFT'
   for update;
  if not found then return false; end if;

  if current_day.topic <> p_expected->>'topic'
     or current_day.linkedin <> p_expected->'linkedin'
     or current_day.instagram <> p_expected->'instagram' then
    return false;
  end if;
  if exists (
    select 1 from public.render_jobs r
     where r.shop_id = p_shop_id and r.day_id = p_day_id
       and r.status in ('QUEUED','RUNNING')
  ) then
    return false;
  end if;

  update public.campaign_days
    set topic = trim(p_changes->>'topic'),
        linkedin = p_changes->'linkedin',
        instagram = p_changes->'instagram',
        review_status = 'DRAFT'
   where id = p_day_id and campaign_id = p_campaign_id and shop_id = p_shop_id;
  get diagnostics updated_count = row_count;
  return updated_count = 1;
end;
$$;

revoke all on function public.save_campaign_day(uuid,uuid,uuid,jsonb,jsonb)
 from public, anon, authenticated;
grant execute on function public.save_campaign_day(uuid,uuid,uuid,jsonb,jsonb)
 to authenticated;
commit;
