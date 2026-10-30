-- SOURCE-ONLY, TRANSACTION-SAFE PROPOSAL. Do not apply to hosted DEV/PROD.
-- Offline disposable Postgres tests load this file within BEGIN ... ROLLBACK.
-- This is NOT an applied Supabase migration or a public Node HTTP route.
-- Copyright RetailGrowthAI contributors.

-- Python json.dumps(obj, sort_keys=True, separators=(',', ':')) uses
-- sorted keys and ensure_ascii=True by default. Postgres jsonb::text does NOT.
-- Deterministic serializer for the frozen Reel v1 types (integers, text,
-- boolean, null, arrays and objects). Recursively encode Unicode surrogate
-- pairs to match Python's default serializer, including emojis and Hindi.
create function retail_private.python_json_v1(p_value pg_catalog.jsonb)
returns pg_catalog.text language plpgsql immutable security invoker set search_path = ''
as $function$
declare
  kind pg_catalog.text;
  result pg_catalog.text;
  txt pg_catalog.text;
  ch pg_catalog.text;
  key pg_catalog.text;
  item pg_catalog.jsonb;
  cp pg_catalog.int4;
  hi pg_catalog.int4;
  lo pg_catalog.int4;
  i pg_catalog.int4;
  sep pg_catalog.text := '';
begin
  if p_value is null then return null; end if;
  kind := pg_catalog.jsonb_typeof(p_value);
  if kind='null' then return 'null'; end if;
  if kind='boolean' or kind='number' then return p_value::pg_catalog.text; end if;
  if kind='array' then
    result := '[';
    for item in select value from pg_catalog.jsonb_array_elements(p_value) loop
      result := result || sep || retail_private.python_json_v1(item);
      sep := ',';
    end loop;
    return result || ']';
  end if;
  if kind='object' then
    result := '{';
    for key,item in
      select entry.key, entry.value from pg_catalog.jsonb_each(p_value) entry
      order by entry.key collate "C"
    loop
      result := result || sep ||
        retail_private.python_json_v1(pg_catalog.to_jsonb(key)) || ':' ||
        retail_private.python_json_v1(item);
      sep := ',';
    end loop;
    return result || '}';
  end if;
  if kind <> 'string' then raise exception 'unsupported JSON type'; end if;
  txt := p_value #>> '{}';
  result := pg_catalog.chr(34);
  for i in 1..pg_catalog.char_length(txt) loop
    ch := pg_catalog.substr(txt,i,1);
    cp := pg_catalog.ascii(ch);
    if cp=34 or cp=92 then
      result := result || pg_catalog.chr(92) || ch;
    elsif cp=8 then result := result || pg_catalog.chr(92) || 'b';
    elsif cp=9 then result := result || pg_catalog.chr(92) || 't';
    elsif cp=10 then result := result || pg_catalog.chr(92) || 'n';
    elsif cp=12 then result := result || pg_catalog.chr(92) || 'f';
    elsif cp=13 then result := result || pg_catalog.chr(92) || 'r';
    elsif cp<32 or cp>=128 then
      if cp<=65535 then
        result := result || pg_catalog.chr(92) || 'u' ||
          pg_catalog.lpad(pg_catalog.to_hex(cp),4,'0');
      else
        cp := cp-65536;
        hi := 55296 + (cp / 1024);
        lo := 56320 + (cp % 1024);
        result := result || pg_catalog.chr(92) || 'u' ||
          pg_catalog.lpad(pg_catalog.to_hex(hi),4,'0') ||
          pg_catalog.chr(92) || 'u' ||
          pg_catalog.lpad(pg_catalog.to_hex(lo),4,'0');
      end if;
    else result := result || ch;
    end if;
  end loop;
  return result || pg_catalog.chr(34);
end
$function$;

revoke all on function retail_private.python_json_v1(pg_catalog.jsonb)
  from public, anon, authenticated;

-- Hardened caller RPC. Caller supplies ONLY two UUIDs. The database resolves
-- all identities, shop, saved storyboard, source licensing and Python digest.
-- Privileged definer lives ONLY in non-exposed retail_private, because render_jobs INSERT is service-only.
-- PostgreSQL quota BEFORE INSERT and outbox AFTER INSERT remain unchanged.
create function retail_private.request_reel_render_job_internal(p_campaign_id pg_catalog.uuid,p_day_id pg_catalog.uuid)
returns pg_catalog.jsonb language plpgsql volatile security definer set search_path = ''
as $function$
declare
  actor pg_catalog.uuid := (select auth.uid());
  campaign public.campaigns%rowtype;
  day public.campaign_days%rowtype;
  reel pg_catalog.jsonb;
  scenes pg_catalog.jsonb;
  shot pg_catalog.jsonb;
  aid pg_catalog.uuid;
  music pg_catalog.uuid;
  ids pg_catalog.uuid[] := array[]::pg_catalog.uuid[];
  media public.media_assets%rowtype;
  offset_secs pg_catalog.int4 := 0;
  duration pg_catalog.int4;
  n pg_catalog.int4 := 0;
  key pg_catalog.text;
  job_id pg_catalog.uuid;
  job_state pg_catalog.text;
begin
  if p_campaign_id is null or p_day_id is null or actor is null
     or (select auth.jwt())->>'role' is distinct from 'authenticated'
     or actor::pg_catalog.text is distinct from (select auth.jwt())->>'sub'
     or (select auth.jwt())->>'is_anonymous' = 'true' then return null;
  end if;

  -- Locks serialize concurrent same-campaign requests before unique-key check
  -- and before existing quota/outbox triggers. No tentative duplicate charge.
  select * into campaign from public.campaigns c
  where c.id=p_campaign_id and c.status='DRAFT' for update;
  if not found or not retail_private.has_role(campaign.shop_id,array['OWNER','EDITOR']) then
    return null;
  end if;
  select * into day from public.campaign_days d
  where d.id=p_day_id and d.campaign_id=campaign.id
    and d.shop_id=campaign.shop_id and d.review_status='DRAFT' for share;
  if not found then return null; end if;

  reel := day.instagram->'reel';
  if pg_catalog.jsonb_typeof(reel)<>'object' or
     (select count(*) from pg_catalog.jsonb_object_keys(reel))<>5 or
     reel->>'aspect_ratio'<>'9:16' or reel->>'duration_seconds'<>'30' or
     pg_catalog.jsonb_typeof(reel->'storyboard')<>'array' or
     pg_catalog.jsonb_typeof(reel->'cta')<>'string' or
     pg_catalog.char_length(reel->>'cta') not between 1 and 100 then
    return null;
  end if;
  if (reel ?& array['duration_seconds','aspect_ratio','storyboard','music_asset_id','cta']) is not true then return null; end if;
  scenes := reel->'storyboard';
  if pg_catalog.jsonb_array_length(scenes) not between 1 and 30 then return null; end if;
  for shot in select value from pg_catalog.jsonb_array_elements(scenes) loop
    if (shot ?& array['start_seconds','duration_seconds','asset_id','overlay_text']) is not true or
       pg_catalog.jsonb_typeof(shot)<>'object' or
       (select count(*) from pg_catalog.jsonb_object_keys(shot))<>4 or
       pg_catalog.jsonb_typeof(shot->'start_seconds')<>'number' or
       pg_catalog.jsonb_typeof(shot->'duration_seconds')<>'number' or
       (shot->>'start_seconds') !~ '^(0|[1-9][0-9]*)$' or
       (shot->>'duration_seconds') !~ '^[1-9][0-9]*$' or
       pg_catalog.jsonb_typeof(shot->'overlay_text')<>'string' or
       pg_catalog.char_length(shot->>'overlay_text') not between 1 and 100 then
      return null;
    end if;
    duration := (shot->>'duration_seconds')::pg_catalog.int4;
    if (shot->>'start_seconds')::pg_catalog.int4 <> offset_secs or
       duration<1 or duration>30 then return null; end if;
    if (shot->>'asset_id') !~
      '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' then return null; end if;
    aid := (shot->>'asset_id')::pg_catalog.uuid;
    ids := pg_catalog.array_append(ids,aid);
    offset_secs := offset_secs+duration;
  end loop;
  if offset_secs<>30 then return null; end if;
  if reel->'music_asset_id' <> 'null'::pg_catalog.jsonb then
    if pg_catalog.jsonb_typeof(reel->'music_asset_id')<>'string' or
       (reel->>'music_asset_id') !~
       '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' then
      return null;
    end if;
    music := (reel->>'music_asset_id')::pg_catalog.uuid;
    -- A single asset cannot simultaneously be an IMAGE storyboard frame and
    -- an AUDIO music source; the old combined ID loop otherwise classified
    -- that shared source by music MIME and could accept audio as an image.
    if music = any(ids) then return null; end if;
    ids := pg_catalog.array_append(ids,music);
  end if;

  -- Enforce real saved source media under row locks, never client-provided URLs.
  if pg_catalog.cardinality(ids)>31 then return null; end if;
  for aid in select distinct x from pg_catalog.unnest(ids) x loop
    n := n+1;
    if n>21 then return null; end if;
    select * into media from public.media_assets a
      where a.id=aid and a.shop_id=campaign.shop_id for share;
    if not found or media.storage_bucket<>'retailgrowth-media' or
       media.object_path not like campaign.shop_id::pg_catalog.text || '/%' or
       (media.license_name in ('owned','cc0','royalty_free','commercial')) is not true or
       pg_catalog.length(pg_catalog.btrim(coalesce(media.attribution,'')))<10 or
       (media.license_name<>'owned' and
         (media.license_url is null or media.license_url !~ '^https://[^[:space:]]{4,}$')) or
       (aid=music and media.mime_type not in
         ('audio/mpeg','audio/mp3','audio/wav','audio/x-wav','audio/aac','audio/mp4')) or
       (aid is distinct from music and media.mime_type not in
         ('image/png','image/jpeg','image/webp')) then
      return null;
    end if;
  end loop;

  -- Exact compatibility: Python hash over [user_id,campaign_id,day_id,reel],
  -- sorted compact JSON and ensure_ascii=True; no client-supplied digest.
  key := pg_catalog.encode(extensions.digest(
      pg_catalog.convert_to(retail_private.python_json_v1(
        pg_catalog.jsonb_build_array(actor::pg_catalog.text,
          campaign.id::pg_catalog.text,day.id::pg_catalog.text,reel)), 'UTF8'),
      'sha256'),'hex');
  select j.id,j.status into job_id,job_state from public.render_jobs j
    where j.shop_id=campaign.shop_id and j.idempotency_key=key;
  if found then
    return pg_catalog.jsonb_build_object('job_id',job_id,'status',job_state);
  end if;
  -- No manual ledger or Queue API: existing SQL triggers reserve usage and
  -- write the outbox within this exact transaction, rolling back on failure.
  insert into public.render_jobs(shop_id,campaign_id,day_id,requested_by,
      preset,status,idempotency_key)
    values(campaign.shop_id,campaign.id,day.id,actor,'instagram_reel_30s','QUEUED',key)
    returning id,status into job_id,job_state;
  return pg_catalog.jsonb_build_object('job_id',job_id,'status',job_state);
end
$function$;

-- The privileged implementation is in NON-EXPOSED retail_private only.
-- Authenticated callers can execute it through the narrow public SECURITY
-- INVOKER wrapper, which carries no elevated privilege of its own.
revoke all on function retail_private.request_reel_render_job_internal(pg_catalog.uuid,pg_catalog.uuid)
  from public, anon, authenticated;
grant execute on function retail_private.request_reel_render_job_internal(pg_catalog.uuid,pg_catalog.uuid)
  to authenticated;

create function public.request_reel_render_job(p_campaign_id pg_catalog.uuid,p_day_id pg_catalog.uuid)
returns pg_catalog.jsonb language sql volatile security invoker set search_path = ''
as $wrapper$
  select retail_private.request_reel_render_job_internal(p_campaign_id,p_day_id)
$wrapper$;

revoke all on function public.request_reel_render_job(pg_catalog.uuid,pg_catalog.uuid)
  from public, anon, authenticated;
grant execute on function public.request_reel_render_job(pg_catalog.uuid,pg_catalog.uuid)
  to authenticated;
