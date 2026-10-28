-- Feature3: signed retailer model import. SOURCE ONLY, hosted not deployed.
-- Import is never image verification, model approval, GPU permission or VTON.
begin;
create function public.feature3_import_pending_model(
 p_shop_id uuid,p_model_id uuid,p_media_asset_id uuid,
 p_source_kind text,p_label text,p_image_sha256 text,
 p_license_id text,p_license_evidence_sha256 text,
 p_attribution text,p_approved_uses text[]
) returns jsonb language plpgsql volatile security definer set search_path='' as $function$
declare
 actor uuid := (select auth.uid());
 src public.media_assets%rowtype;
 expected_key text;
 added uuid;
begin
 if actor is null or p_shop_id is null or p_model_id is null or p_media_asset_id is null
    or not exists(select 1 from public.shop_memberships sm
       where sm.shop_id=p_shop_id and sm.user_id=actor
         and sm.active and sm.role in ('OWNER','EDITOR'))
    or p_source_kind is null or p_source_kind not in
       ('retailer_licensed','created_ai','opensource_render')
    or p_label is null or length(trim(p_label)) not between 1 and 64
    or p_label ~ '[[:cntrl:]]'
    or p_image_sha256 is null or p_image_sha256 !~ '^[0-9a-f]{64}$'
    or p_license_id is null or p_license_id not in
       ('CC0-1.0','CC-BY-4.0','REVIEWED-COMMERCIAL')
    or p_license_evidence_sha256 is null
    or p_license_evidence_sha256 !~ '^[0-9a-f]{64}$'
    or p_attribution is null or length(p_attribution) > 200
    or p_attribution ~ '[[:cntrl:]]'
    or p_approved_uses is null or cardinality(p_approved_uses) not between 1 and 3
    or not (p_approved_uses <@ array['poster','try_on','video_reference']::text[])
    or (select count(distinct x) from unnest(p_approved_uses) as x)
          <> cardinality(p_approved_uses)
    or (p_license_id='CC-BY-4.0' and length(trim(p_attribution)) = 0)
 then return null; end if;
 -- Import deliberately supports only SHOP scope. A global platform
 -- model requires a separately audited curator workflow and media rights.
 expected_key:=p_shop_id::text||'/model-library/'||
              p_model_id::text||'/'||p_image_sha256||'.png';
 select * into src from public.media_assets
    where shop_id=p_shop_id and id=p_media_asset_id for share;
 if not found or src.storage_bucket <> 'retailgrowth-media'
    or src.object_path <> expected_key or src.mime_type <> 'image/png'
    or src.source not in ('UPLOAD','GENERATED')
    or src.license_name not in ('owned','cc0','commercial','royalty_free')
    or length(trim(coalesce(src.attribution,''))) < 10
    or (src.license_name <> 'owned'
       and (src.license_url is null or src.license_url not like 'https://%'))
 then return null; end if;
 -- Lower-cost tenant bound: protect from unbounded drafts. Serialize
 -- import per owning shop to avoid concurrent count-based overrun.
 perform 1 from public.shops where id=p_shop_id for update;
 if not found or (select count(*) from public.feature3_models
     where owner_shop_id=p_shop_id) >= 30 then return null; end if;
 insert into public.feature3_models(
   model_id,owner_shop_id,created_by,media_asset_id,scope,status,source_kind,
   label,image_sha256,license_id,license_evidence_sha256,rights_verified,
   synthetic_adult,attribution,approved_uses,rights_revision)
 values(p_model_id,p_shop_id,actor,p_media_asset_id,'shop','PENDING_REVIEW',
   p_source_kind,trim(p_label),p_image_sha256,p_license_id,
   p_license_evidence_sha256,false,true,p_attribution,p_approved_uses,1)
 on conflict(model_id) do nothing returning model_id into added;
 if added is null then return null; end if;
 return jsonb_build_object('shop_id',p_shop_id,'model_id',added,
   'media_asset_id',p_media_asset_id,'status','PENDING_REVIEW',
   'rights_revision',1,'rights_verified',false,
   'evidence_verified',false,'gpu_authorized',false,
   'registered',true);
end
$function$;
revoke all on function public.feature3_import_pending_model(
 uuid,uuid,uuid,text,text,text,text,text,text,text[]
) from public,anon,authenticated;
grant execute on function public.feature3_import_pending_model(
 uuid,uuid,uuid,text,text,text,text,text,text,text[]
) to authenticated;
commit;
