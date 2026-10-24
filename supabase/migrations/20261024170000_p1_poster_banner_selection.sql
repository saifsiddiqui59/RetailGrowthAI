-- Part 1 explicit reviewed-banner selection. Additive; no publishing side effects.
begin;
create function public.select_poster_banner(
    p_poster_id uuid, p_expected_instagram jsonb)
returns boolean language plpgsql volatile security definer set search_path = '' as $$
declare p public.poster_drafts%rowtype;
        d public.campaign_days%rowtype;
        object_key text;
begin
 if (select auth.uid()) is null or (select auth.role()) is distinct from 'authenticated'
   or p_poster_id is null or p_expected_instagram is null
   or jsonb_typeof(p_expected_instagram) <> 'object' then return false; end if;
 select * into p from public.poster_drafts where id=p_poster_id for update;
 if not found or p.status<>'READY' or p.output_asset_id is null
    or not retail_private.has_role(p.shop_id,array['OWNER','EDITOR']) then return false; end if;
 select * into d from public.campaign_days
    where id=p.day_id and campaign_id=p.campaign_id and shop_id=p.shop_id for update;
 if not found or d.review_status<>'DRAFT' or d.instagram is distinct from p_expected_instagram
   or not exists (select 1 from public.campaigns c
      where c.id=p.campaign_id and c.shop_id=p.shop_id and c.status='DRAFT') then return false; end if;
 if not exists(select 1 from public.poster_jobs j where j.poster_id=p.id
   and j.shop_id=p.shop_id and j.revision=p.revision and j.status='SUCCEEDED'
   and j.output_asset_id=p.output_asset_id) then return false; end if;
 select a.object_path into object_key from public.media_assets a
   where a.id=p.output_asset_id and a.shop_id=p.shop_id
     and a.storage_bucket='retailgrowth-media' and a.mime_type='image/png'
     and a.source='GENERATED' and a.license_name='owned'
     and a.object_path like p.shop_id::text||'/posters/'||p.id::text||'/%';
 if object_key is null then return false; end if;
 -- The originating media must still be registered and commercially licensed.
 if not exists(select 1 from public.media_assets a
   where a.id=p.source_asset_id and a.shop_id=p.shop_id
   and a.license_name in ('owned','cc0','royalty_free','commercial')
   and length(trim(coalesce(a.attribution,'')))>=10) then return false; end if;
 update public.campaign_days set instagram=jsonb_set(
   d.instagram, '{banner_asset_id}', to_jsonb(p.output_asset_id::text), true)
 where id=d.id and shop_id=p.shop_id and instagram=p_expected_instagram;
 return found;
end $$;
revoke all on function public.select_poster_banner(uuid,jsonb)
 from public, anon, authenticated;
grant execute on function public.select_poster_banner(uuid,jsonb) to authenticated;
commit;
