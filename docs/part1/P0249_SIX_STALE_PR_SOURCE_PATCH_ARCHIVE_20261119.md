# Issue #249 — exact six-stale-PR patch archive (2026-11-19)

**Nonexecuting historical source archive only**: full unchanged PR file diff hunks and original exact head SHAs. Does NOT merge protected code, resolve gateway #249, settle Y1 ZIP #650, claim tenant/rights or deploy anything. Current main contains newer security code; do NOT wholesale merge old heads.

| Original PR | Exact head | Paths | Unfinished handoff |
|---|---|---:|---|
| [#356](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/356) | `753954847e936d2869d5521b09e3a01cd414f20b` | 7 | Private render SQL proposal needs security review; NOT deployed |
| [#639](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/639) | `14c0417e32903923e79dd15de1332caba8247d85` | 7 | ROOT queue exact-render/overlap behavior needs signed runtime tests |
| [#668](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/668) | `d0814c492fef18b2dc948e309470f73687685d3a` | 9 | OFF-by-default Node same-origin candidate NOT deployed/cut over |
| [#676](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/676) | `ad112c4ee4d552e5dea374f2f7014d1055ac4458` | 8 | Two-shop ROOT approval still needs live signed test |
| [#679](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/679) | `39b943e28c1f74cdd96b0a0f1c09867b9892319b` | 4 | Header/redirect fence needs current-transport security review |
| [#955](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/955) | `6fedbba1befa1deb11eb928ad420e035133c47bd` | 4 | Historical Y1/JWT canonical doc checkpoint, NOT hosted acceptance |

## Original full GitHub source patch hunks

## PR #356 — HEAD 753954847e936d2869d5521b09e3a01cd414f20b
https://github.com/saifsiddiqui59/RetailGrowthAI/pull/356/files

### docs/DECISIONS.md
~~~~diff
@@ -462,3 +462,6 @@
 ## 2026-10-26 — Feature2 uncertain-POST compatibility boundary (deployed DEV)
 - Optional canonical UUID `submission_id` is validated inside the existing authenticated DRAFT POST and persisted only as correlation data within backend-generated immutable nonpublishable JSON; legacy POST remains supported. The client preflights signed-in user-RLS history, makes one POST and on possible lost gateway acknowledgement rereads only that user's shop-scoped five latest drafts. Confirm success exclusively for a unique matching nonce/tenant/embedded campaign shop/trend/review DRAFT; otherwise explicitly report unknown outcome. Never automatically retry a possibly committed POST, confer publishing rights, or use a browser service-role token.
 - This app-layer mitigation is **not** server-side idempotency nor an Azure #249 resolution. Future collision-proof submissions need separately reviewed SQL uniqueness, safe same-key/same-payload semantics and tested concurrency, without adding paid resources.
+
+## 2026-10-26 — Narrow privately privileged SQL, preserve Python digest and no paid hosting
+- The Reel intent SQL proposal verified in disposable CI uses a **non-exposed** `retail_private.request_reel_render_job_internal` SECURITY DEFINER called by a public **SECURITY INVOKER** wrapper; no broad authenticated INSERT on `render_jobs`. It explicitly checks original Supabase actor, active OWNER/EDITOR, DRAFT 30-second storyboard and exact nullable-safe licensed media, then serializes under campaign lock and reuses existing Python `sha256(json.dumps(...,sort_keys=True,separators=(',',':')))` keys (including Unicode) before using the existing quota/outbox triggers. Avoid second queue/ledger or paid Node plan. Security review and hosted migration remain separate gates; no service-role key in Free SWA.
~~~~

### docs/NEXT_TASK.md
~~~~diff
@@ -648,3 +648,8 @@ NaN
 **P0 remaining:** actual owner completes legitimate business city/category and registers licensed image (live DEV currently has zero) before genuine authenticated Google RSS recommendation → single POST → persisted GET/history can be accepted. Negative VIEWER/foreign shop/expired JWT and genuine mobile sign-in remain. Do not impersonate the retailer, invent details or confuse synthetic Playwright with hosted E2E.
 **P0 parallel:** Azure Flex gateway issue #249 intermittent no-first-byte/503 still OPEN. Separate small Node SWA HTTP facade work stays unregistered, Python Queue/FFmpeg intact, no paid always-ready changes.
 **P1:** next UTC day's scheduled 05:15 trend timer claim must be observed for real; source freshness/fencing and quota monitored. Truly concurrent exactly-once draft writes would require reviewed per-tenant/actor server-side uniqueness/payload-consistency SQL. Bounded user-RLS readback cannot guarantee a late or beyond-page commit.
+
+## 2026-10-26 — #249 next gate after verified disposable SQL and main reconciliation
+- **DONE locally in disposable CI:** #40321452358 4/4 PASS, including Python canonical Unicode/hash reuse, exact quota/outbox on edited Reel, no direct INSERT grant, explicit NULL-license denial, private-schema SECURITY DEFINER implementation/public SECURITY INVOKER wrapper. This code has NOT been migrated to hosted DEV.
+- **NEXT:** review the SQL proposal with coordinator, generate an exact new versioned migration via approved Supabase migration process, validate existing DEV security advisors and staged privileges, then apply only against authorized RetailGrowthAI DEV and verify read-only catalog; never alter PROD/WineShopPOS or change trial entitlements. Concurrency/race and 3rd-render quota test in disposable database should precede enabling any customer traffic.
+- **LATER:** mount secure Node API POST only in isolated Free SWA staging, independently verify Supabase JWT transport + real owner/VIEWER/foreign/expired sessions and upload→campaign→poster→30s MP4→signed download with cleanup; only then replace live Flex HTTP origin. No paid always-ready. #249 stays OPEN.
~~~~

### docs/PROJECT_STATE.md
~~~~diff
@@ -712,3 +712,7 @@ See docs/NEXT_TASK.md. Live integrations and cloud deployment remain blocked by
 - Protected existing-resource [DEV release #40319956057](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40319956057) both Functions and Free SWA jobs SUCCESS. Existing Central India Function App indexed 24 Functions with no missing expected triggers, anonymous Feature2 returned 401, already completed shared RSS daily claim was not fetched again, and live [Free /trends SPA](https://purple-dune-06b5da200.2.azurestaticapps.net/trends) served successfully via HTTPS. No Azure plan/GPU/Supabase migration/paid API/PROD/WineShopPOS changes.
 - Signed DRAFT POST now accepts optional canonical UUID `submission_id`, persisted in nonpublishable backend-validated tenant DRAFT JSON. On ambiguous Azure acknowledgement, React never blindly replays the POST: signed user-RLS readback confirms exactly one matching nonce/shop/embedded shop/trend/DRAFT row or shows outcome UNCONFIRMED. Simulated React browser lost-ACK tests pass. This is not database atomic idempotency and does not fix Azure Flex #249.
 - Final live DEV read-only Supabase audit after release: 20 migrations, one India snapshot with 10 Google RSS signals, zero customer draft records, one shop, zero registered licensed media. Real owner-JWT draft creation and re-opening require legitimate business city/category and owned licensed image; do not invent profile/media values or claim mocked Playwright as hosted owner E2E.
+
+## 2026-10-26 — Verified disposable #249 Reel SQL source, reconciled with concurrent Feature2 main
+- Existing Free SWA Node Reel client was merged via [PR #351](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/351) after 4/4 CI; its POST remains unregistered. Independent disposable [#40321452358](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40321452358) PASSED 4/4 on SQL proposal/test: canonical Python Unicode SHA-256, reuse of legacy Python job without duplicate reservation/outbox, edit creates exactly one new job, VIEWER/foreign/unlicensed/anon denied. The test uncovered and fixed an actual SQL NULL-license authorization bug; assertions read private outbox only under the disposable DB privileged test role. Narrow implementation lives in non-exposed `retail_private` SECURITY DEFINER, public callable wrapper is SECURITY INVOKER, PUBLIC/anon EXEC revoked, no broad authenticated `render_jobs` INSERT.
+- The validated SQL remains **source-only and unapplied** at `experiments/secure-node-http/sql/request_reel_render_job.proposal.sql` with disposable BEGIN/ROLLBACK tests `tests/security/poster_reel_intent_negative.sql`; reconciled atop latest `main` without Feature2 edits. NO DEV/PROD schema changes, billing changes, WineShopPOS edits, paid capacity or customer traffic. Original HTTP issue #249 remains OPEN pending reviewed versioned migration, hosted auth/SWA transport and protected E2E.
~~~~

### docs/WORK_LOG.md
~~~~diff
@@ -328,3 +328,5 @@ Use scripts/checkpoint.sh after completing a task.
 - Continued exact current RetailGrowthAI state and read mandatory AGENTS/PROJECT_STATE/NEXT_TASK/DECISIONS/WORK_LOG. Found that UI falsely said DRAFT save failed on ambiguous Azure #249 transport error, risking duplicate content. Feature #2 isolated PR #350 added backward-compatible signed POST nonce, caller-JWT+RLS pre-read and bounded post-error reconciliation without retry, Python and JS validation tests and simulated-browser Playwright confirmed-commit/unknown-result tests. Fixed a synchronous-vs-async JS test assertion without relaxing validation. Exact PR CI [#40318607322](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40318607322) 4/4 passed.
 - Coordinator reconciled 9 Feature2-owned paths and shared state/next/decisions/worklog plus one-shot workflow against latest main, merged [PR #352](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/352) at `14edc9eb` after exact CI [#40319569053](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40319569053) 4/4. Closed duplicate worker PR #350 to prevent double merge.
 - Main CI [#40319956341](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40319956341) 4/4 PASS. Actual existing-resource protected DEV [release #40319956057](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40319956057) both jobs SUCCESS, 24 Functions indexed, expected anonymous 401, shared RSS already claimed no duplicate external fetch, existing Free SWA served /trends HTTPS. Live read-only DB audit: 20 versioned migrations, one 10-signal snapshot, one shop, no customer drafts and no licensed media. Real authenticated owner E2E and Azure Flex #249 remain open. No PROD, WineShopPOS, new billed resources, schema writes or account-profile mutations.
+
+- 2026-10-26: Continued #249 with low-cost existing Supabase/Free SWA plan. Merged PR #351 source-only Reel client after 4/4 PR CI. Developed and tested an **unapplied** two-UUID Reel intent SQL implementation with private-schema elevated code/public invoker wrapper; disposable Postgres run [#40321452358](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40321452358) four green checks, including legacy Python emoji/Hindi idempotency, no duplicate job/quota/outbox, edited Reel new exact job, VIEWER/foreign/unlicensed/anon denial. Corrected test-only private outbox read, delimiter formatting, and security-significant NULL-license SQL bug before all green. Original PR #353 hit shared-doc merge conflicts as Feature2 advanced main; reconciled same two tested source files and appended truthful handoff on a fresh branch from current main. No hosted DEV SQL migration, new Azure paid capacity, live Node POST route, PROD, or WineShopPOS modification. #249 remains OPEN for approved migration, concurrency checks and signed-in E2E.
~~~~

### docs/part1/P0_249_RENDER_INTENT_RPC_SECURITY_PLAN.md
~~~~diff
@@ -39,3 +39,7 @@ Create a reviewed **one-function, caller-authorized render-intent RPC** instead
 - Source-only Node adapter PRs [#338](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/338), [#341](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/341), [#345](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/345) delivered authenticated GET parity, private downloads, poster DB RPC writes, campaign planning and draft day CAS source. These Node writes are **unregistered/not deployed**.
 - Real Free SWA synthetic Node preview #40295844516 tested 200/401/404/200 in ~0.65–1.88s. This is not a secure retailer endpoint or proof of repeated reliability over many days.
 - **Azure issue #249 remains OPEN:** original Python Flex had 4/6 read-only post-TLS client timeouts on #40291064533, prior actual gateway 503s. No root cause confirmed, no new plan/always-ready spend, no support case filed at owner's direction, and no PROD/WineShopPOS changes.
+
+## 2026-10-26 — Verified code and next integration gate
+- Reviewed source-only SQL: `experiments/secure-node-http/sql/request_reel_render_job.proposal.sql`. Privileged implementation is hidden in `retail_private`; public `request_reel_render_job` is SECURITY INVOKER with only two UUID inputs, and anon/PUBLIC EXECUTE explicitly revoked. Python-compatible sorted compact ensure_ascii=True Unicode digest verified against existing Python-created job. License checks reject NULL explicitly (`IN (...) IS NOT TRUE`) to avoid a SQL three-valued logic bypass.
+- Test `tests/security/poster_reel_intent_negative.sql` is auto-run by existing `poster*.sql` disposable CI and wrapped in BEGIN/ROLLBACK. [Run #40321452358](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40321452358) 4/4 PASS, including actual SQL function execution and exact job/reservation/outbox counters. No hosted migration. After coordinator security review, generate a versioned migration, stage to existing RetailGrowthAI DEV only, and re-verify grants/advisors; separately verify concurrent retry/quota exhaustion and authenticated end-to-end on isolated Free SWA staging. Keep #249 OPEN.
~~~~

### experiments/secure-node-http/sql/request_reel_render_job.proposal.sql
~~~~diff
@@ -0,0 +1,234 @@
+-- SOURCE-ONLY, TRANSACTION-SAFE PROPOSAL. Do not apply to hosted DEV/PROD.
+-- Offline disposable Postgres tests load this file within BEGIN ... ROLLBACK.
+-- This is NOT an applied Supabase migration or a public Node HTTP route.
+-- Copyright RetailGrowthAI contributors.
+
+-- Python json.dumps(obj, sort_keys=True, separators=(',', ':')) uses
+-- sorted keys and ensure_ascii=True by default. Postgres jsonb::text does NOT.
+-- Deterministic serializer for the frozen Reel v1 types (integers, text,
+-- boolean, null, arrays and objects). Recursively encode Unicode surrogate
+-- pairs to match Python's default serializer, including emojis and Hindi.
+create function retail_private.python_json_v1(p_value pg_catalog.jsonb)
+returns pg_catalog.text language plpgsql immutable security invoker set search_path = ''
+as $function$
+declare
+  kind pg_catalog.text;
+  result pg_catalog.text;
+  txt pg_catalog.text;
+  ch pg_catalog.text;
+  key pg_catalog.text;
+  item pg_catalog.jsonb;
+  cp pg_catalog.int4;
+  hi pg_catalog.int4;
+  lo pg_catalog.int4;
+  i pg_catalog.int4;
+  sep pg_catalog.text := '';
+begin
+  if p_value is null then return null; end if;
+  kind := pg_catalog.jsonb_typeof(p_value);
+  if kind='null' then return 'null'; end if;
+  if kind='boolean' or kind='number' then return p_value::pg_catalog.text; end if;
+  if kind='array' then
+    result := '[';
+    for item in select value from pg_catalog.jsonb_array_elements(p_value) loop
+      result := result || sep || retail_private.python_json_v1(item);
+      sep := ',';
+    end loop;
+    return result || ']';
+  end if;
+  if kind='object' then
+    result := '{';
+    for key,item in
+      select entry.key, entry.value from pg_catalog.jsonb_each(p_value) entry
+      order by entry.key collate "C"
+    loop
+      result := result || sep ||
+        retail_private.python_json_v1(pg_catalog.to_jsonb(key)) || ':' ||
+        retail_private.python_json_v1(item);
+      sep := ',';
+    end loop;
+    return result || '}';
+  end if;
+  if kind <> 'string' then raise exception 'unsupported JSON type'; end if;
+  txt := p_value #>> '{}';
+  result := pg_catalog.chr(34);
+  for i in 1..pg_catalog.char_length(txt) loop
+    ch := pg_catalog.substr(txt,i,1);
+    cp := pg_catalog.ascii(ch);
+    if cp=34 or cp=92 then
+      result := result || pg_catalog.chr(92) || ch;
+    elsif cp=8 then result := result || pg_catalog.chr(92) || 'b';
+    elsif cp=9 then result := result || pg_catalog.chr(92) || 't';
+    elsif cp=10 then result := result || pg_catalog.chr(92) || 'n';
+    elsif cp=12 then result := result || pg_catalog.chr(92) || 'f';
+    elsif cp=13 then result := result || pg_catalog.chr(92) || 'r';
+    elsif cp<32 or cp>=128 then
+      if cp<=65535 then
+        result := result || pg_catalog.chr(92) || 'u' ||
+          pg_catalog.lpad(pg_catalog.to_hex(cp),4,'0');
+      else
+        cp := cp-65536;
+        hi := 55296 + (cp / 1024);
+        lo := 56320 + (cp % 1024);
+        result := result || pg_catalog.chr(92) || 'u' ||
+          pg_catalog.lpad(pg_catalog.to_hex(hi),4,'0') ||
+          pg_catalog.chr(92) || 'u' ||
+          pg_catalog.lpad(pg_catalog.to_hex(lo),4,'0');
+      end if;
+    else result := result || ch;
+    end if;
+  end loop;
+  return result || pg_catalog.chr(34);
+end
+$function$;
+
+revoke all on function retail_private.python_json_v1(pg_catalog.jsonb)
+  from public, anon, authenticated;
+
+-- Hardened caller RPC. Caller supplies ONLY two UUIDs. The database resolves
+-- all identities, shop, saved storyboard, source licensing and Python digest.
+-- Privileged definer lives ONLY in non-exposed retail_private, because render_jobs INSERT is service-only.
+-- PostgreSQL quota BEFORE INSERT and outbox AFTER INSERT remain unchanged.
+create function retail_private.request_reel_render_job_internal(p_campaign_id pg_catalog.uuid,p_day_id pg_catalog.uuid)
+returns pg_catalog.jsonb language plpgsql volatile security definer set search_path = ''
+as $function$
+declare
+  actor pg_catalog.uuid := (select auth.uid());
+  campaign public.campaigns%rowtype;
+  day public.campaign_days%rowtype;
+  reel pg_catalog.jsonb;
+  scenes pg_catalog.jsonb;
+  shot pg_catalog.jsonb;
+  aid pg_catalog.uuid;
+  music pg_catalog.uuid;
+  ids pg_catalog.uuid[] := array[]::pg_catalog.uuid[];
+  media public.media_assets%rowtype;
+  offset_secs pg_catalog.int4 := 0;
+  duration pg_catalog.int4;
+  n pg_catalog.int4 := 0;
+  key pg_catalog.text;
+  job_id pg_catalog.uuid;
+  job_state pg_catalog.text;
+begin
+  if p_campaign_id is null or p_day_id is null or actor is null
+     or pg_catalog.current_setting('request.jwt.claim.role',true) is distinct from 'authenticated'
+     or (select auth.jwt())->>'is_anonymous' = 'true' then return null;
+  end if;
+
+  -- Locks serialize concurrent same-campaign requests before unique-key check
+  -- and before existing quota/outbox triggers. No tentative duplicate charge.
+  select * into campaign from public.campaigns c
+  where c.id=p_campaign_id and c.status='DRAFT' for update;
+  if not found or not retail_private.has_role(campaign.shop_id,array['OWNER','EDITOR']) then
+    return null;
+  end if;
+  select * into day from public.campaign_days d
+  where d.id=p_day_id and d.campaign_id=campaign.id
+    and d.shop_id=campaign.shop_id and d.review_status='DRAFT' for share;
+  if not found then return null; end if;
+
+  reel := day.instagram->'reel';
+  if pg_catalog.jsonb_typeof(reel)<>'object' or
+     (select count(*) from pg_catalog.jsonb_object_keys(reel))<>5 or
+     reel->>'aspect_ratio'<>'9:16' or reel->>'duration_seconds'<>'30' or
+     pg_catalog.jsonb_typeof(reel->'storyboard')<>'array' or
+     pg_catalog.jsonb_typeof(reel->'cta')<>'string' or
+     pg_catalog.char_length(reel->>'cta') not between 1 and 100 then
+    return null;
+  end if;
+  if (reel ?& array['duration_seconds','aspect_ratio','storyboard','music_asset_id','cta']) is not true then return null; end if;
+  scenes := reel->'storyboard';
+  if pg_catalog.jsonb_array_length(scenes) not between 1 and 30 then return null; end if;
+  for shot in select value from pg_catalog.jsonb_array_elements(scenes) loop
+    if (shot ?& array['start_seconds','duration_seconds','asset_id','overlay_text']) is not true or
+       pg_catalog.jsonb_typeof(shot)<>'object' or
+       (select count(*) from pg_catalog.jsonb_object_keys(shot))<>4 or
+       pg_catalog.jsonb_typeof(shot->'start_seconds')<>'number' or
+       pg_catalog.jsonb_typeof(shot->'duration_seconds')<>'number' or
+       (shot->>'start_seconds') !~ '^(0|[1-9][0-9]*)$' or
+       (shot->>'duration_seconds') !~ '^[1-9][0-9]*$' or
+       pg_catalog.jsonb_typeof(shot->'overlay_text')<>'string' or
+       pg_catalog.char_length(shot->>'overlay_text') not between 1 and 100 then
+      return null;
+    end if;
+    duration := (shot->>'duration_seconds')::pg_catalog.int4;
+    if (shot->>'start_seconds')::pg_catalog.int4 <> offset_secs or
+       duration<1 or duration>30 then return null; end if;
+    if (shot->>'asset_id') !~
+      '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' then return null; end if;
+    aid := (shot->>'asset_id')::pg_catalog.uuid;
+    ids := pg_catalog.array_append(ids,aid);
+    offset_secs := offset_secs+duration;
+  end loop;
+  if offset_secs<>30 then return null; end if;
+  if reel->'music_asset_id' <> 'null'::pg_catalog.jsonb then
+    if pg_catalog.jsonb_typeof(reel->'music_asset_id')<>'string' or
+       (reel->>'music_asset_id') !~
+       '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' then
+      return null;
+    end if;
+    music := (reel->>'music_asset_id')::pg_catalog.uuid;
+    ids := pg_catalog.array_append(ids,music);
+  end if;
+
+  -- Enforce real saved source media under row locks, never client-provided URLs.
+  if pg_catalog.cardinality(ids)>31 then return null; end if;
+  for aid in select distinct x from pg_catalog.unnest(ids) x loop
+    n := n+1;
+    if n>21 then return null; end if;
+    select * into media from public.media_assets a
+      where a.id=aid and a.shop_id=campaign.shop_id for share;
+    if not found or media.storage_bucket<>'retailgrowth-media' or
+       media.object_path not like campaign.shop_id::pg_catalog.text || '/%' or
+       (media.license_name in ('owned','cc0','royalty_free','commercial')) is not true or
+       pg_catalog.length(pg_catalog.btrim(coalesce(media.attribution,'')))<10 or
+       (media.license_name<>'owned' and
+         (media.license_url is null or media.license_url !~ '^https://[^[:space:]]{4,}$')) or
+       (aid=music and media.mime_type not in
+         ('audio/mpeg','audio/mp3','audio/wav','audio/x-wav','audio/aac','audio/mp4')) or
+       (aid is distinct from music and media.mime_type not in
+         ('image/png','image/jpeg','image/webp')) then
+      return null;
+    end if;
+  end loop;
+
+  -- Exact compatibility: Python hash over [user_id,campaign_id,day_id,reel],
+  -- sorted compact JSON and ensure_ascii=True; no client-supplied digest.
+  key := pg_catalog.encode(extensions.digest(
+      pg_catalog.convert_to(retail_private.python_json_v1(
+        pg_catalog.jsonb_build_array(actor::pg_catalog.text,
+          campaign.id::pg_catalog.text,day.id::pg_catalog.text,reel)), 'UTF8'),
+      'sha256'),'hex');
+  select j.id,j.status into job_id,job_state from public.render_jobs j
+    where j.shop_id=campaign.shop_id and j.idempotency_key=key;
+  if found then
+    return pg_catalog.jsonb_build_object('job_id',job_id,'status',job_state);
+  end if;
+  -- No manual ledger or Queue API: existing SQL triggers reserve usage and
+  -- write the outbox within this exact transaction, rolling back on failure.
+  insert into public.render_jobs(shop_id,campaign_id,day_id,requested_by,
+      preset,status,idempotency_key)
+    values(campaign.shop_id,campaign.id,day.id,actor,'instagram_reel_30s','QUEUED',key)
+    returning id,status into job_id,job_state;
+  return pg_catalog.jsonb_build_object('job_id',job_id,'status',job_state);
+end
+$function$;
+
+-- The privileged implementation is in NON-EXPOSED retail_private only.
+-- Authenticated callers can execute it through the narrow public SECURITY
+-- INVOKER wrapper, which carries no elevated privilege of its own.
+revoke all on function retail_private.request_reel_render_job_internal(pg_catalog.uuid,pg_catalog.uuid)
+  from public, anon, authenticated;
+grant execute on function retail_private.request_reel_render_job_internal(pg_catalog.uuid,pg_catalog.uuid)
+  to authenticated;
+
+create function public.request_reel_render_job(p_campaign_id pg_catalog.uuid,p_day_id pg_catalog.uuid)
+returns pg_catalog.jsonb language sql volatile security invoker set search_path = ''
+as $wrapper$
+  select retail_private.request_reel_render_job_internal(p_campaign_id,p_day_id)
+$wrapper$;
+
+revoke all on function public.request_reel_render_job(pg_catalog.uuid,pg_catalog.uuid)
+  from public, anon, authenticated;
+grant execute on function public.request_reel_render_job(pg_catalog.uuid,pg_catalog.uuid)
+  to authenticated;
~~~~

### tests/security/poster_reel_intent_negative.sql
~~~~diff
@@ -0,0 +1,233 @@
+-- GitHub Actions disposable local Supabase Postgres ONLY, never hosted DEV/PROD.
+-- Existing CI executes tests/security/poster*.sql inside a disposable database.
+-- Everything, including the PROPOSED SQL functions and fixtures, ROLLS BACK.
+\set ON_ERROR_STOP on
+begin;
+\i experiments/secure-node-http/sql/request_reel_render_job.proposal.sql
+
+-- The Python hash serializer must match ensure_ascii=True (incl. emoji/Hindi).
+do $$
+declare serialised text;
+begin
+  serialised:=retail_private.python_json_v1('{"z":"हिंदी","a":"🎉"}'::jsonb);
+  if serialised <> '{"a":"\ud83c\udf89","z":"\u0939\u093f\u0902\u0926\u0940"}' then
+    raise exception 'Python Unicode/sorted-key canonicalization mismatch: %',serialised;
+  end if;
+  if has_function_privilege('anon','public.request_reel_render_job(uuid,uuid)','EXECUTE') then
+    raise exception 'anonymous can execute privileged Reel SQL RPC';
+  end if;
+  if not has_function_privilege('authenticated','public.request_reel_render_job(uuid,uuid)','EXECUTE') then
+    raise exception 'authenticated cannot execute narrowed Reel SQL RPC';
+  end if;
+  if exists (
+    select 1 from pg_catalog.pg_proc p
+    join pg_catalog.pg_namespace n on n.oid=p.pronamespace
+    where n.nspname='public' and p.proname='request_reel_render_job'
+      and p.prosecdef
+  ) then raise exception 'exposed public Reel RPC must NOT be security definer'; end if;
+  if not exists (
+    select 1 from pg_catalog.pg_proc p
+    join pg_catalog.pg_namespace n on n.oid=p.pronamespace
+    where n.nspname='retail_private' and p.proname='request_reel_render_job_internal'
+      and p.prosecdef
+  ) then raise exception 'private implementation needs scoped definer for DB INSERT'; end if;
+  if has_table_privilege('authenticated','public.render_jobs','INSERT') then
+    raise exception 'unreviewed broad authenticated render_jobs INSERT grant';
+  end if;
+end $$;
+
+insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
+values
+('11111111-1111-4111-8111-111111111111','00000000-0000-0000-0000-000000000000',
+ 'authenticated','authenticated','reel-rpc-owner@example.invalid','!',now(),now()),
+('22222222-2222-4222-8222-222222222222','00000000-0000-0000-0000-000000000000',
+ 'authenticated','authenticated','reel-rpc-viewer@example.invalid','!',now(),now()),
+('99999999-9999-4999-8999-999999999999','00000000-0000-0000-0000-000000000000',
+ 'authenticated','authenticated','reel-rpc-foreign@example.invalid','!',now(),now());
+
+set local role authenticated;
+select set_config('request.jwt.claim.role','authenticated',true);
+select set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',true);
+insert into public.shops(id,owner_user_id,name,slug) values
+('33333333-3333-4333-8333-333333333333',
+ '11111111-1111-4111-8111-111111111111','Reel RPC isolated shop','rg-reel-rpc-ci');
+insert into public.shop_memberships(shop_id,user_id,role) values
+('33333333-3333-4333-8333-333333333333',
+ '22222222-2222-4222-8222-222222222222','VIEWER');
+
+reset role;
+select set_config('request.jwt.claim.role','service_role',true);
+insert into public.campaigns(id,shop_id,created_by,brief,start_date) values
+('44444444-4444-4444-8444-444444444444',
+ '33333333-3333-4333-8333-333333333333',
+ '11111111-1111-4111-8111-111111111111',
+ 'Disposable test, no actual video generation','2026-11-01');
+update public.campaigns set status='DRAFT'
+ where id='44444444-4444-4444-8444-444444444444';
+insert into public.media_assets(id,shop_id,created_by,object_path,mime_type,source,
+   license_name,attribution) values
+('55555555-5555-4555-8555-555555555555',
+ '33333333-3333-4333-8333-333333333333',
+ '11111111-1111-4111-8111-111111111111',
+ '33333333-3333-4333-8333-333333333333/uploads/55555555-5555-4555-8555-555555555555.png',
+ 'image/png','UPLOAD','owned','Retail owner-created and reviewed'),
+('66666666-6666-4666-8666-666666666666',
+ '33333333-3333-4333-8333-333333333333',
+ '11111111-1111-4111-8111-111111111111',
+ '33333333-3333-4333-8333-333333333333/uploads/66666666-6666-4666-8666-666666666666.png',
+ 'image/png','UPLOAD',null,'Unreviewed media');
+
+insert into public.campaign_days(id,campaign_id,shop_id,day_index,scheduled_date,
+  topic,linkedin,instagram) values
+('88888888-8888-4888-8888-888888888888',
+ '44444444-4444-4444-8444-444444444444',
+ '33333333-3333-4333-8333-333333333333',
+ 1,'2026-11-01','Fashion sale',
+ '{"post_text":"Shop Diwali","hashtags":["#Diwali"]}'::jsonb,
+ '{"caption":"Diwali Sale","banner_asset_id":null,"reel":{"duration_seconds":30,"aspect_ratio":"9:16","storyboard":[{"asset_id":"55555555-5555-4555-8555-555555555555","overlay_text":"Festival 🎉 हिंदी","start_seconds":0,"duration_seconds":30}],"music_asset_id":null,"cta":"आज Shop now"}}'::jsonb);
+
+-- Worker-side legacy job from Python's exact SHA-256 compact sorted JSON
+-- must be FOUND, not charged again or duplicated, on Node/client request.
+insert into public.render_jobs(id,shop_id,campaign_id,day_id,requested_by,preset,
+  status,idempotency_key) values
+('77777777-7777-4777-8777-777777777777',
+ '33333333-3333-4333-8333-333333333333',
+ '44444444-4444-4444-8444-444444444444',
+ '88888888-8888-4888-8888-888888888888',
+ '11111111-1111-4111-8111-111111111111',
+ 'instagram_reel_30s','QUEUED',
+ '73593202305f3dec115aaf8e851e5aac9045fb751b3587641b9ec5713efcb3c6');
+
+set local role authenticated;
+select set_config('request.jwt.claim.role','authenticated',true);
+select set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',true);
+do $$
+declare result jsonb;
+begin
+  result:=public.request_reel_render_job(
+   '44444444-4444-4444-8444-444444444444',
+   '88888888-8888-4888-8888-888888888888');
+  if result->>'job_id'<>'77777777-7777-4777-8777-777777777777' or
+     result->>'status'<>'QUEUED' then
+    raise exception 'legacy Python digest not reused: %',result;
+  end if;
+  result:=public.request_reel_render_job(
+   '44444444-4444-4444-8444-444444444444',
+   '88888888-8888-4888-8888-888888888888');
+  if result->>'job_id'<>'77777777-7777-4777-8777-777777777777' then
+    raise exception 'same Reel input double queued despite Python key';
+  end if;
+  if (select count(*) from public.render_jobs)<>1 then
+    raise exception 'legacy identical request created a duplicate render row';
+  end if;
+end $$;
+
+-- Private quota and outbox are intentionally INVISIBLE to authenticated users.
+-- Assert under disposable-test postgres identity only; never grant them SELECT.
+reset role;
+do $$
+begin
+  if (select count(*) from public.shop_usage_reservations where operation='render')<>1 or
+     (select count(*) from public.job_outbox where kind='render')<>1 then
+    raise exception 'legacy identical request double billed/outboxed';
+  end if;
+end $$;
+set local role authenticated;
+select set_config('request.jwt.claim.role','authenticated',true);
+-- Forbidden VIEWER/foreign user cannot cause any additional job or usage.
+select set_config('request.jwt.claim.sub','22222222-2222-4222-8222-222222222222',true);
+do $$
+begin
+  if public.request_reel_render_job(
+     '44444444-4444-4444-8444-444444444444',
+     '88888888-8888-4888-8888-888888888888') is not null then
+    raise exception 'VIEWER requested a privileged Reel job';
+  end if;
+end $$;
+select set_config('request.jwt.claim.sub','99999999-9999-4999-8999-999999999999',true);
+do $$
+begin
+  if public.request_reel_render_job(
+     '44444444-4444-4444-8444-444444444444',
+     '88888888-8888-4888-8888-888888888888') is not null then
+    raise exception 'foreign shop requested private render';
+  end if;
+end $$;
+
+-- One edited storyboard produces ONE fresh job/reservation/outbox.
+reset role;
+select set_config('request.jwt.claim.role','service_role',true);
+update public.campaign_days set instagram=jsonb_set(instagram,
+  '{reel,cta}','"Edited CTA"'::jsonb)
+ where id='88888888-8888-4888-8888-888888888888';
+set local role authenticated;
+select set_config('request.jwt.claim.role','authenticated',true);
+select set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',true);
+do $$
+declare a jsonb; b jsonb;
+begin
+  a:=public.request_reel_render_job(
+    '44444444-4444-4444-8444-444444444444',
+    '88888888-8888-4888-8888-888888888888');
+  b:=public.request_reel_render_job(
+    '44444444-4444-4444-8444-444444444444',
+    '88888888-8888-4888-8888-888888888888');
+  if a->>'job_id' is null or a->>'job_id'='77777777-7777-4777-8777-777777777777'
+     or b->>'job_id' is distinct from a->>'job_id' then
+    raise exception 'edited Reel job not new-and-idempotent';
+  end if;
+  if (select count(*) from public.render_jobs)<>2 then
+    raise exception 'same modified Reel inserted duplicate jobs';
+  end if;
+end $$;
+
+reset role;
+do $$
+begin
+  if (select count(*) from public.shop_usage_reservations where operation='render')<>2 or
+     (select count(*) from public.job_outbox where kind='render')<>2 then
+    raise exception 'not exactly one subscription unit and outbox per edited job';
+  end if;
+end $$;
+-- Editing to unlicensed (but same-shop) source cannot bypass rights.
+reset role;
+select set_config('request.jwt.claim.role','service_role',true);
+update public.campaign_days set instagram=jsonb_set(instagram,
+  '{reel,storyboard,0,asset_id}',
+  '"66666666-6666-4666-8666-666666666666"'::jsonb)
+ where id='88888888-8888-4888-8888-888888888888';
+set local role authenticated;
+select set_config('request.jwt.claim.role','authenticated',true);
+select set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',true);
+do $$
+begin
+  if public.request_reel_render_job(
+    '44444444-4444-4444-8444-444444444444',
+    '88888888-8888-4888-8888-888888888888') is not null then
+    raise exception 'unlicensed source allowed new render';
+  end if;
+end $$;
+
+-- Validate strict SQL privileges: no anonymous entry or direct user inserts.
+set local role anon;
+select set_config('request.jwt.claim.role','anon',true);
+select set_config('request.jwt.claim.sub','',true);
+do $$
+declare denied boolean:=false;
+begin
+  begin
+    perform public.request_reel_render_job(
+      '44444444-4444-4444-8444-444444444444',
+      '88888888-8888-4888-8888-888888888888');
+  exception when insufficient_privilege then denied:=true; end;
+  if not denied then raise exception 'anonymous render RPC reachable'; end if;
+end $$;
+
+reset role;
+do $$
+begin
+  if (select count(*) from public.render_jobs)<>2 then
+    raise exception 'denied source bypass inserted another job'; end if;
+end $$;
+rollback;
+\echo 'PASS: Python SHA256 Unicode parity, legacy Reel deduplication, user/tenant denial, one quota/outbox per new job, no hosted writes'
~~~~

## PR #639 — HEAD 14c0417e32903923e79dd15de1332caba8247d85
https://github.com/saifsiddiqui59/RetailGrowthAI/pull/639/files

### docs/DECISIONS.md
~~~~diff
@@ -954,3 +954,15 @@
 
 ## 2026-10-29 — Separate immutable model-review proof from media labels
 - Use a service-role-only read RPC to derive current model proof from immutable independent `retail_private.feature3_model_evidence`, latest `feature3_model_review_events` and current APPROVED catalogue/media SHA; browser, declared media `license_name` or synthetic files never grant commercial reuse, consent or GPU. Source bridge accepts only seven fields and requires current revision+approval. Unreviewed source and non-model product/garment images fail closed until separately reviewed. The SQL source is intentionally not deployed and must undergo DB owner/versioning approval before runtime wiring.
+
+## 2026-10-29 — #249 ROOT canary queue response fence is fail-closed and source-only
+- Preserve genuine operator-signed ROOT review, mandatory audited approval and one-at-a-time, newly created `rgai-canary-<12hex>-[ab]@example.invalid` synthetic test identities. A successful onboarding HTTP reply alone cannot prove React rendered it. Await equality of actual signed pending-list RPC email order and visible DOM; reject malformed/duplicate/oversized replies and multiple independent fresh canary-A runs. No blind approve, SQL bypass, stored password, automatic protected workflow dispatch or customer route change. This change reduces operator test ambiguity but does not repair Azure Functions Python Flex HTTP 503; actual live canary and CI remain separate evidence gates.
+
+## 2026-10-29 — #249 only a click-created pending RPC proves queue freshness
+- A successful HTTP response from the correct Supabase endpoint is insufficient when two same-URL list requests overlap. The local ROOT operator's initial queue open and subsequent refresh must each bind to their own newly observed Playwright `Request`, its exact `Response`, and equivalent current React rows. Reject unrelated in-flight responses and malformed/failing reads before audited decisions. Source-only and fail-closed, with all customer/ROOT grants unchanged; original Azure 503 remains independent.
+
+## 2026-10-29 — Audited ROOT decision must have a matching server ACK
+- A React success toast and detached queue row alone are not evidence a particular newly created canary user was actually approved. Before accepting a ROOT decision in the local Playwright operator helper, require the exact intended existing HTTPS `retail_platform_review_onboarding` POST, strict `p_approve=true`, UUID-v4 account, fixed reason and response for that same request. Fail closed on missing/unconfirmed results; no automatic privileged POST retry, SQL escalation, or generic provider fallback. Keep operator-controlled approvals and separate Azure #249 host diagnosis.
+
+## 2026-10-29 — #249 verified queue email and UUID must bind to approval POST
+- When privileged ROOT approval is operated through a local browser helper, do not trust a well-formed arbitrary approval UUID: use the signed current PENDING queue response's exact `email -> user_id` association. Require a unique canonical UUIDv4 for every pending row and no duplicate IDs/emails; bind the clicked synthetic canary email to the `p_user_id` in its newly initiated audited POST. A mismatching request/response must stop without duplicate privileged mutation. No grants/bypass, new API/schema, cloud budget, live E2E or production change; Issue #249 original 503 is distinct.
~~~~

### docs/NEXT_TASK.md
~~~~diff
@@ -1277,3 +1277,18 @@ Detailed handoff: `docs/feature3/PRE_GPU_READINESS_20261028.md`. No WineShopPOS
 
 ## 2026-10-29 — Feature3 current rights authority remaining live gates
 - Exact-head four-job CI and coordinator review for `feat/feature3-reviewed-model-authority-20261029`; integrate only after green tests and independent postmerge main CI. Source connects private image proof to an exact service-only current-model review RPC, but the SQL implementation is **proposal not installed**: DB owner must review/security-test/version and authorize release, checking latest APPROVED event, immutable legal-source evidence, consent and media hash. A product/garment license-review authority is separately required and default-denied. No real live model source proof, GPU, queued render, paid inference, PROD or WineShopPOS actions can be claimed from these tests.
+
+## 2026-10-29 — Issue #249 next independent operator + platform gates (after response fence candidate)
+- Verify exact branch-head all four CI jobs for `fix/p0249-root-queue-response-fence-20261029`, review and coordinator-merge only if green, then inspect independent postmerge main CI. Its code removes the remaining fixed-delay stale-DOM risk and refuses simultaneous canary-A candidate runs; source tests are **not** hosted proof.
+- Authorized DEV operator: from an Internet-connected Windows machine run the existing [ROOT Playwright runbook](part1/P0_249_LOCAL_ROOT_PLAYWRIGHT_RUNBOOK.md) using genuinely signed-in Platform Admin. Intentional `--approve-test-only --dispatch-dev-canary` initiates one protected `node-poster-reel` run with exact freshly created synthetic users, no unrelated approvals. Inspect actual run logs for signed multi-tenant rights denials, private PNG/30s H.264/AAC output, cleanup and measured reliability; don't replay uncertain POSTs. The previous five-minute approval window timed out and cleanup passed.
+- Separately obtain incident-timestamp Azure HTTP ingress -> host/worker causal evidence for the original Python Flex 9/20 pre-handler ~61s 503; no automatic cost, settings, production routing or security gate changes before proven fix. Keep #249 OPEN.
+
+## 2026-10-29 — #249 request-bound ROOT queue follow-up
+- Current open source PR #639 also fixes a second initial-queue/Refresh overlap race: each button uses the new request object and its own response, and ARMED only follows the fully rendered initial list. Reverify all four CI jobs for the **final changed head**, coordinator review and integration, then run a real owner-authorized DEV two-shop canary from an Internet-connected operator machine. No workflow-dispatch, paid hosting, Azure runtime repair or source CI can replace that signed test.
+
+## 2026-10-29 — #249 after audited ROOT approval ACK fencing
+- Review latest #639 exact-head CI (all 4 jobs), coordinator merge only after green and independent main postmerge CI. Latest operator helper now requires actual click-created audited approval POST and its matching positive HTTP acknowledgement, not just a transient React toast; ambiguous ACK means stop and inspect private approval state manually, never blindly repeat.
+- Launch genuine protected DEV Node poster/Reel canary only from owner-authenticated Internet-connected ROOT Playwright machine with explicit workflow dispatch and one synthetic two-shop run. Verify actual banner selection, 30s private MP4, negative cross-tenant permissions, full fixture cleanup, and repeat reliability. Independently obtain original Python Flex ingress→worker trace or record `AZURE_INTERNAL_TRACE_REQUIRED`; don't claim a 503 fix or reroute traffic.
+
+## 2026-10-29 — #249 account identity binding pending CI and live proof
+- On Issue #249 branch PR #639, verify new exact-head 4/4 CI after binding actual verified ROOT queue `email->user_id` to the audited approval POST; require unique valid UUIDv4, no duplicate account IDs, exact selected synthetic email and no retry of uncertain decision. Reconcile parallel new `main` changes without dropping other feature work, coordinator-only merge and independent postmerge CI. Only an owner-authenticated Internet-connected local ROOT browser with explicitly dispatched protected DEV test can prove actual two-shop approvals, private PNG/30s MP4, cross-tenant negative and cleanup. Original Flex HTTP group/root 503 still needs internal Azure correlation; do not claim repaired or alter paid hosting/PROD/WineShopPOS.
~~~~

### docs/PROJECT_STATE.md
~~~~diff
@@ -1296,3 +1296,17 @@ See docs/NEXT_TASK.md. Live integrations and cloud deployment remain blocked by
 
 ## 2026-10-29 — Feature3 service-only current model approval authority (source-only)
 - Added strict backend `Feature3ApprovedModelReviewAuthority` to join the already-merged real private Storage SHA/Pillow media proof with an exact current approved-model review verdict read by POST-only service RPC. Denies unknown product/garment rights, stale model revision, revoked/foreign approval, fabricated licence or source. All source tests use fake review responses, not a real legal verifier. The proposed SQL function **is not deployed or added as migration**; no production current approval authority exists until owner review/DB approval. [Handoff](feature3/CURRENT_REVIEWED_MODEL_AUTHORITY_20261029.md). No GPU, cloud or WineShopPOS changes.
+
+## 2026-10-29 — Issue #249 ROOT pending-queue response/DOM fence (PR candidate, SOURCE ONLY)
+- Continued latest merged Playwright helper #633; reviewed actual `PlatformAdmin.jsx` async `listPlatformOnboardingRequests('PENDING')` and `frontend/src/lib/supabase.js` RPC list semantics. A fixed 100ms UI sleep after an accepted HTTPS RPC is **not** a causal React render guarantee; source candidate `fix/p0249-root-queue-response-fence-20261029` parses the exact successful bounded ROOT pending-list JSON, fails closed on malformed/duplicate email replies, and waits for actual visible React rows to equal the received ordered list before considering an account for audited approval. When multiple fresh unrelated synthetic canary A accounts are visible, the operator fails closed rather than choosing alphabetically. Added offline negative tests; CI and PR merge evidence must be verified separately.
+- No authorized ROOT browser decision, new protected workflow dispatch, signed private poster/30s MP4, Azure diagnostic repair, capacity/app config, hosted SQL, default origin cutover, PROD or WineShopPOS. Original Azure Python Flex gateway ~61s 503 remains OPEN; latest live accepted test still #40834600937 failed at five-minute approval and cleaned fixtures. Operator must run on a network-connected Windows machine using exact current main and real ROOT UI only after source review/merge.
+
+## 2026-10-29 — #249 initial ROOT queue request identity hardening (source-only)
+- Additional source review found the actual `Review requests` React effect starts an asynchronous initial pending-list read, so immediately clicking `Refresh queue` can overlap two same-URL HTTP requests. The prior `expect_response` predicate could mistake the older in-flight reply for a refresh. Updated the Playwright operator helper to await the specific `expect_request` emitted by each clicked button and inspect *that request's own* `response()`. `open_pending_queue` now completes the initial queue and exact DOM render before ARMED, and refreshes separately fence request -> successful reply -> exact displayed rows. Tests stub two UI actions, absent/bad/foreign HTTP response and malformed JSON; no signed live canary occurred.
+
+## 2026-10-29 — #249 audited ROOT decision ACK source verification (no live acceptance)
+- Extended the already open #639 operator-only Playwright helper to verify the exact new HTTPS POST `retail_platform_review_onboarding` initiated by the selected Approve button, strict UUID-v4 target and `p_approve=true` plus fixed approved reason, and the originating request's successful HTTP response before claiming a UI row removal/approval. Malformed, redirected/foreign, non-2xx or missing acknowledgments fail closed with no blind replay of a privileged decision. Added Python mocks of exact request payload, foreign/mismatched response and UI causal ordering. Does not change ROOT privileges or DB approval itself.
+- Source-only candidate; GitHub final exact-head 4/4 CI must be checked again. Real ROOT browser run, actual two-shop poster/30s Reel media, Azure HTTP gateway cause, cloud SQL and paid/deployment operations remain unverified. #249 stays OPEN; no WineShopPOS, PROD or customer route mutation.
+
+## 2026-10-29 — #249 exact pending account ID-to-audited approval fence (source only)
+- Inspected real `PlatformAdmin.jsx` pending review rows (`user_id`, `email`) and `supabase.js` `retail_platform_review_onboarding(p_user_id, p_approve, p_reason)`. Previous #639 helper checked the approval UUID was valid but did not compare it to the exact selected pending email's server-supplied `user_id`. Added strict UUIDv4/account mapping validation to each successful current ROOT queue response; duplicate email or user ID fails closed. UI row rendering and exact request/response fences remain required. Approved decision POST must now carry the identical UUID to the clicked synthetic email. Added negative tests for wrong-target valid UUID, bad/missing IDs and reused IDs. No browser customer credentials/SQL privilege, hosted run, paid capacity or original Python Azure 503 fix. Latest CI pending; #249 remains open.
~~~~

### docs/WORK_LOG.md
~~~~diff
@@ -713,3 +713,11 @@ Use scripts/checkpoint.sh after completing a task.
 
 
 - 2026-10-29 Resumed Feature3 task after interruption: live main already contains private source byte reader, output evidence and default-OFF Blob preview, with latest 4/4 main CI. Implemented the next missing backend `Feature3ApprovedModelReviewAuthority` and approved-model-only GPU-OFF preflight factory, strict POST-only service transport and offline actual HTTP Request tests for foreign, revoked, forged digest and non-model denials; wrote model-evidence release handoff. The executable SQL proposal could not be submitted through the tool; **no migration/version or hosted DB write was executed**. External legal review evidence and actual DEV role acceptance remain pending. No GPU or WineShopPOS.
+
+- 2026-10-29 — Resumed OPEN Azure Issue #249 against latest merged #633 and actual ROOT/React code. Found residual 100ms fixed-delay race after queue RPC; source branch `fix/p0249-root-queue-response-fence-20261029` now parses genuine successful 40-item bounded pending RPC and waits for exact visible ordered UI rows, plus fail-closed ambiguous simultaneous synthetic canary A selection. Added pure Python mocked-response/DOM and negative tests. This is source only pending exact-head CI/PR review/postmerge evidence. Last actual protected run #40834600937 failed at ROOT approval timeout and cleaned up; no new manual workflow or positive signed media, no original Azure Python ingress 503 diagnosis/fix, no hosted resources or WineShopPOS.
+
+- 2026-10-29 — Continued #249 PR #639 past clean conflict-free rebase. Identified overlapping initial React pending queue load and manually triggered Refresh could both hit the exact same URL; response-event-only selector was not sufficient request identity. Updated source to use click-generated `Page.expect_request` plus `Request.response()`, await initial data+DOM before declaring ARMED and preserve exact response→UI equality; added separate mocked initial/refresh/foreign/failed request tests. Source PR head CI and coordinator merge pending; no actual ROOT/browser canary, private PNG/30s Reel, Azure diagnostics, cloud changes, PROD or WineShopPOS.
+
+- 2026-10-29 — Independent issue #249 source continuation on clean open #639 (previous exact 4/4 source CI). Verified actual React `reviewRequest` calls current audited Supabase `retail_platform_review_onboarding`, then sets toast/queue state. Patched Playwright `approve_exact_row` to require button-scoped audited POST request body and its own positive HTTP response before UI confirmation; rejects wrong account UUID, false approval, incorrect reason, missing/foreign/error ACK. Added mocked positive/negative and sequencing tests; documented source-only gates. No privileged live approvals, new protected canary, original Azure 503 resolution, paid resources, PROD or WineShopPOS changes.
+
+- 2026-10-29 — Continued Issue #249 PR #639 after reviewing real React onboarding rows and Supabase RPC parameters. Found residual identity gap: valid random UUID in audited POST was not linked back to the selected synthetic `email`; patched local ROOT Playwright operator to parse and strictly validate all queue UUIDv4 email/user_id associations, reject duplicate IDs and bind exact selected ID into verified approval RPC. Added offline unit regressions for malicious/missing/duplicate IDs and wrong-target approval; original signed HTTP queue/readback and no-retry gates unchanged. Source only, no DEV operator approvals, cloud tests, Azure resource settings, paid plan or WineShopPOS.
~~~~

### docs/part1/P0_249_LOCAL_ROOT_PLAYWRIGHT_RUNBOOK.md
~~~~diff
@@ -17,3 +17,19 @@ The repository now has the *optional*, zero-cloud-change script `scripts/ops/p02
 5. Verify GitHub's **actual live** signed-JWT, tenant-negative, private poster, 30s MP4, license, rights and cleanup markers independently. A local `CANARY_BOTH_ROOT_UI_APPROVALS_COMPLETE=true` statement is **not** proof the media end-to-end passed. Keep Issue #249 open unless the original Python Flex gateway 503 also has a separate proven resolution.
 
 **Security and failure handling:** Explicit `--approve-test-only` is mandatory, and optional `--dispatch-dev-canary` must also be supplied to start a workflow. This script does not automatically dispatch the GitHub workflow, start Azure resources, change subscription, operate on PROD/WineShopPOS, store screenshots, print the password, bypass ROOT permissions or use a service-role SQL write. If DNS/Playwright Chromium is blocked, or if the operator's account lacks real platform access, it fails closed. Never run this helper on a shared/untrusted computer, and rotate any testing password already disclosed in chat. `uv` is the repo's existing Python environment manager; offline eligibility tests are in `tests/infra/test_p0249_root_canary_playwright.py`.
+
+## 2026-10-29 response-fence source continuation (not a live run)
+
+After review and merge of the standalone `fix/p0249-root-queue-response-fence-20261029` branch, the local watcher no longer assumes a fixed 100ms delay means the ROOT React approval rows are current. Each Refresh queue requires the exact successful DEV Supabase onboarding-list HTTP response, bounded valid JSON and visible row-by-row equality before selecting an exact fresh canary. It aborts if two independent fresh canary-A runs appear simultaneously; operate one protected run at a time. It still requires a real authenticated ROOT browser and intentional operator dispatch. This source-only improvement has no actual hosted approval/MP4 evidence and makes no change to the unresolved original Python Flex 503.
+
+## 2026-10-29 local watcher request-identity follow-up (not hosted proof)
+
+The initial **Review requests** click now waits for its own DEV signed pending-list request, successful corresponding reply and exact React rows before displaying ARMED. Subsequent **Refresh queue** waits for a separate newly emitted request and its own reply, never whichever earlier same-URL response happens to arrive first. This prevents a queued initial-load response from masquerading as a successful refresh; it does not skip the five-minute ROOT window or approve arbitrary pending accounts. The protected live E2E still requires normal operator authentication and manual intentional dispatch after reviewed main integration.
+
+## 2026-10-29 — Audited UI approval acknowledgement check
+
+The local helper now considers the selected synthetic ROOT **Approve** action confirmed only after its exact `/rest/v1/rpc/retail_platform_review_onboarding` request has the expected `p_approve=true` UUID-v4 payload, fixed audit reason and an accepted HTTP response tied to that request, followed by UI removal and confirmation. Missing/uncertain ACKs fail closed. Do not press Approve repeatedly after a timeout; inspect the signed ROOT onboarding state and cleaned test run rather than replaying a potentially committed decision. This source change is not an actual authorized operator run, a test user approval, a protected 30s Reel, or a diagnosis of the unrelated Python Flex 503.
+
+## 2026-10-29 — Exact pending-account UUID binding (source only)
+
+The local script now reads the current pending ROOT RPC's `user_id` and `email` together, not only displayed names. Reject invalid/non-v4/missing/duplicated UUIDs or duplicate emails; after the exact selected synthetic email row is clicked, the audited `retail_platform_review_onboarding` POST must use **that same user UUID** before the server's successful response and React confirmation count. A valid but different UUID is never accepted as proof of the test account's approval. Source/CI review is not an actual signed DEV run or a waiver of five-minute ROOT approval, media rights, private 30s Reel or unresolved original Python Flex 503. Use only the coordinator-merged main after full four-job CI and keep credentials in local interactive prompts.
~~~~

### scripts/ops/p0249_root_canary_playwright.py
~~~~diff
@@ -35,43 +35,148 @@ def eligible_canary(email: str, baseline: set[str], prefix: str | None) -> bool:
     return match.group(1) == prefix and match.group(2) == "b"
 
 
+def choose_pending_candidate(pending: set[str], baseline: set[str],
+                             approved: set[str], prefix: str | None) -> str | None:
+    """Reject ambiguous parallel canary A runs instead of approving a stranger's test."""
+    candidates = sorted(e for e in pending
+                        if eligible_canary(e, baseline | approved, prefix))
+    if not candidates:
+        return None
+    if prefix is None and len(candidates) != 1:
+        raise RuntimeError("Multiple fresh canary runs visible; no ROOT decisions made")
+    return candidates[0]
+
+
 def read_pending(page) -> set[str]:
     """Use the same ROOT-only React approval queue used by a human operator."""
     return set(page.locator(".platform-review-item strong").all_inner_texts())
 
 
-def is_onboarding_queue_reply(response) -> bool:
-    """Identify only the real authenticated ROOT queue RPC response."""
+def is_onboarding_queue_request(request) -> bool:
+    """Match only a new request to the real DEV signed ROOT list RPC."""
     from urllib.parse import urlsplit
-    url = urlsplit(response.url)
+    url = urlsplit(request.url)
     return (url.scheme == "https"
             and url.hostname == "jeearzffnjbvghwjjjrf.supabase.co"
             and url.path == "/rest/v1/rpc/retail_platform_onboarding_requests"
-            and response.request.method == "POST")
+            and request.method == "POST")
+
+
+def is_onboarding_queue_reply(response) -> bool:
+    """Retain response validation for a request's own completed HTTP reply."""
+    return (is_onboarding_queue_request(response.request)
+            and response.url == response.request.url)
 
 
-def refresh_pending(page) -> set[str]:
-    # A hidden loading spinner alone is NOT a sync barrier: React may not
-    # mount the pending state until after the original click returns. Wait
-    # for the actual signed platform API reply before inspecting DOM rows.
-    with page.expect_response(is_onboarding_queue_reply, timeout=15_000) as result:
-        page.get_by_role("button", name="Refresh queue").click()
-    response = result.value
-    if not response.ok:
+def pending_response_for_click(page, button_name: str):
+    # Await a REQUEST initiated AFTER this specific button click, not the
+    # RESPONSE from an older in-flight queue load with an identical URL.
+    with page.expect_request(is_onboarding_queue_request, timeout=15_000) as result:
+        page.get_by_role("button", name=button_name).click()
+    request = result.value
+    response = request.response()
+    if response is None or not is_onboarding_queue_reply(response) or not response.ok:
         raise RuntimeError("ROOT approval queue HTTP request failed; no decisions made")
+    return response
+
+
+def verified_pending_rows(page, response) -> set[str]:
+    # An HTTP reply is not a React render barrier. Parse only the exact
+    # request's successful ROOT response, then match displayed rows to it.
+    try:
+        items = response.json()
+    except (ValueError, TypeError) as exc:
+        raise RuntimeError("ROOT queue response is not valid JSON") from exc
+    from uuid import UUID
+    def valid_user_id(value):
+        if not isinstance(value, str):
+            return False
+        try:
+            parsed = UUID(value)
+        except ValueError:
+            return False
+        return parsed.version == 4 and str(parsed) == value
+
+    if not isinstance(items, list) or len(items) > 40 or any(
+        not isinstance(item, dict)
+        or not isinstance(item.get("email"), str)
+        or not item["email"]
+        or not valid_user_id(item.get("user_id"))
+        for item in items
+    ):
+        raise RuntimeError("ROOT queue response has invalid email/user mapping")
+    expected = [item["email"] for item in items]
+    user_ids = [item["user_id"] for item in items]
+    if len(set(expected)) != len(expected) or len(set(user_ids)) != len(user_ids):
+        raise RuntimeError("ROOT queue contains duplicate identities; no decisions made")
     page.get_by_text("Loading pending retailer requests…", exact=True).wait_for(
         state="hidden", timeout=15_000)
-    # React's resolved Promise updates the row state on a subsequent render.
-    # Give it one browser event-loop turn, never read stale rows immediately
-    # from a response event that fires before its React Promise settles.
-    page.wait_for_timeout(100)
-    error = page.locator(".platform-approvals [role='alert']")
-    if error.count():
-        raise RuntimeError("ROOT approval queue failed to load; no decisions made")
-    return read_pending(page)
+    # Current React component uses RPC array order; fixed sleeps can still
+    # show the older list when an initial and refresh fetch overlap.
+    page.wait_for_function(
+        """expected => {
+          const root = document.querySelector('.platform-approvals');
+          if (!root || root.querySelector('[role="alert"]')) return false;
+          const loading = [...root.querySelectorAll('[role="status"]')]
+            .some(node => node.textContent.includes('Loading pending retailer requests'));
+          const shown = [...root.querySelectorAll('.platform-review-item strong')]
+            .map(node => node.textContent.trim());
+          return !loading && shown.length === expected.length
+            && shown.every((email, index) => email === expected[index]);
+        }""",
+        arg=expected, timeout=15_000,
+    )
+    if read_pending(page) != set(expected):
+        raise RuntimeError("Rendered ROOT queue differs from verified response")
+    return {item["email"]: item["user_id"] for item in items}
+
+
+def open_pending_queue(page) -> dict[str, str]:
+    """Fully synchronize the initial ROOT list before first refresh."""
+    return verified_pending_rows(page, pending_response_for_click(page, "Review requests"))
+
+
+def refresh_pending(page) -> dict[str, str]:
+    """Match the refresh button's OWN request, response and rendered rows."""
+    return verified_pending_rows(page, pending_response_for_click(page, "Refresh queue"))
+
+
+def is_onboarding_approval_request(request) -> bool:
+    """Only the audited DEV ROOT decision RPC, never another POST."""
+    from urllib.parse import urlsplit
+    url = urlsplit(request.url)
+    return (url.scheme == "https"
+            and url.hostname == "jeearzffnjbvghwjjjrf.supabase.co"
+            and url.path == "/rest/v1/rpc/retail_platform_review_onboarding"
+            and request.method == "POST")
+
+
+def verified_approval_reply(request, expected_user_id: str):
+    """A UI toast alone cannot attest which audited approval was accepted."""
+    from uuid import UUID
+    if not is_onboarding_approval_request(request):
+        raise RuntimeError("Wrong ROOT decision RPC; stop without retry")
+    try:
+        body = request.post_data_json
+        user_id = body["p_user_id"]
+        if (not isinstance(body, dict) or set(body) !=
+                {"p_user_id", "p_approve", "p_reason"}
+                or body["p_approve"] is not True
+                or body["p_reason"] != DECISION_REASON
+                or not isinstance(user_id, str)
+                or UUID(user_id).version != 4
+                or str(UUID(user_id)) != user_id
+                or user_id != expected_user_id):
+            raise ValueError("invalid approval request")
+    except (AttributeError, KeyError, TypeError, ValueError) as exc:
+        raise RuntimeError("Audited ROOT approval request mismatch; stop without retry") from exc
+    reply = request.response()
+    if reply is None or reply.request != request or not reply.ok:
+        raise RuntimeError("ROOT approval HTTP result uncertain; stop without retry")
+    return reply
 
 
-def approve_exact_row(page, email: str) -> None:
+def approve_exact_row(page, email: str, expected_user_id: str) -> None:
     """Interact with the audited ROOT approval form; no REST/SQL shortcuts."""
     rows = page.locator(".platform-review-item")
     matching = rows.filter(has=page.locator("strong", has_text=email))
@@ -80,7 +185,11 @@ def approve_exact_row(page, email: str) -> None:
     matching.get_by_role("button", name="Review account").click()
     matching.get_by_label("Decision reason").fill(DECISION_REASON)
     matching.get_by_role("checkbox", name="I verified this account request and authorize the decision.").check()
-    matching.get_by_role("button", name="Approve", exact=True).click()
+    # Bind the button's own request to its accepted response. Never retry a
+    # possibly committed privileged decision after a missing/failed HTTP ACK.
+    with page.expect_request(is_onboarding_approval_request, timeout=15_000) as decision:
+        matching.get_by_role("button", name="Approve", exact=True).click()
+    verified_approval_reply(decision.value, expected_user_id)
     matching.wait_for(state="detached", timeout=15_000)
     if page.get_by_text("Retailer onboarding approved.", exact=True).count() == 0:
         raise RuntimeError("No audited UI approval confirmation; stop without retry")
@@ -119,8 +228,7 @@ def operator_run(page, email: str, password: str, poll_seconds: float = 4,
         login.click()
     # An authenticated non-ROOT account fails here; never grant ROOT via SQL.
     page.get_by_role("heading", name="Retailer signup approvals").wait_for(timeout=30_000)
-    page.get_by_role("button", name="Review requests").click()
-    baseline = refresh_pending(page)
+    baseline = set(open_pending_queue(page))
     print("ARMED: ROOT authenticated. Start the GitHub node-poster-reel manual DEV canary now.", flush=True)
     print("Previously pending accounts excluded: " + str(len(baseline)), flush=True)
     if dispatch:
@@ -130,13 +238,11 @@ def operator_run(page, email: str, password: str, poll_seconds: float = 4,
     approved: set[str] = set()
     while time.monotonic() < deadline:
         pending = refresh_pending(page)
-        candidates = sorted(e for e in pending
-                            if eligible_canary(e, baseline | approved, prefix))
-        if candidates:
-            target = candidates[0]
+        target = choose_pending_candidate(pending, baseline, approved, prefix)
+        if target:
             found = CANARY_RE.fullmatch(target)
             assert found is not None
-            approve_exact_row(page, target)
+            approve_exact_row(page, target, pending[target])
             approved.add(target)
             if prefix is None:
                 prefix = found.group(1)
~~~~

### tests/infra/test_p0249_root_canary_playwright.py
~~~~diff
@@ -40,6 +40,21 @@ def test_only_new_two_shop_example_invalid_marker_allowed(self):
         self.assertFalse(MOD.eligible_canary("rgai-canary-deadbeefdead-b@example.invalid",
                                             set(), "47c4fd8f5eb5"))
 
+    def test_parallel_fresh_canaries_fail_closed_before_any_approval(self):
+        a = "rgai-canary-47c4fd8f5eb5-a@example.invalid"
+        b = "rgai-canary-47c4fd8f5eb5-b@example.invalid"
+        other_a = "rgai-canary-deadbeefdead-a@example.invalid"
+        self.assertIsNone(MOD.choose_pending_candidate(set(), set(), set(), None))
+        self.assertEqual(MOD.choose_pending_candidate({a, b}, set(), set(), None), a)
+        with self.assertRaisesRegex(RuntimeError, "Multiple fresh canary runs"):
+            MOD.choose_pending_candidate({a, other_a}, set(), set(), None)
+        self.assertEqual(
+            MOD.choose_pending_candidate({b, other_a}, set(), {a}, "47c4fd8f5eb5"),
+            b,
+        )
+        self.assertIsNone(
+            MOD.choose_pending_candidate({a, other_a}, {a}, set(), "47c4fd8f5eb5"))
+
     def test_source_denies_db_bypass_and_embedded_credentials(self):
         source = TARGET.read_text(encoding="utf-8")
         ast.parse(source)
@@ -53,83 +68,224 @@ def test_source_denies_db_bypass_and_embedded_credentials(self):
                            "Ppp#2020"):
             self.assertNotIn(prohibited, source)
 
-    def test_refresh_waits_for_real_root_rpc_before_reading_new_rows(self):
-        """Regression: a React loading-hidden check alone can read old rows."""
+    def test_both_queue_buttons_bind_to_their_own_new_request_and_render(self):
+        """Regression: opening the queue can leave an older GET in flight."""
         target = "rgai-canary-012345abcdef-a@example.invalid"
-        calls = []
+        target_id = "123e4567-e89b-42d3-a456-426614174000"
+        url = "https://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/rpc/retail_platform_onboarding_requests"
+        for button, operation in [("Review requests", MOD.open_pending_queue),
+                                  ("Refresh queue", MOD.refresh_pending)]:
+            with self.subTest(button=button):
+                calls = []
 
-        class FakePage:
-            def expect_response(self, predicate, *, timeout):
-                calls.append(("expect", timeout))
-                reply = SimpleNamespace(
-                    url="https://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/rpc/retail_platform_onboarding_requests",
-                    request=SimpleNamespace(method="POST"), ok=True)
-                assert predicate(reply)
-                class Waiter:
-                    value = reply
-                    def __enter__(self):
-                        return self
-                    def __exit__(self, *_):
-                        calls.append(("response", "ok"))
-                return Waiter()
+                class Page:
+                    def expect_request(self, predicate, *, timeout):
+                        calls.append(("expect-request", timeout))
+                        request = SimpleNamespace(url=url, method="POST")
+                        assert predicate(request)
+                        reply = SimpleNamespace(url=url, request=request, ok=True,
+                                                json=lambda: [{"email": target, "user_id": target_id}])
+                        def own_response():
+                            calls.append(("own-response", None))
+                            return reply
+                        request.response = own_response
+                        class Waiter:
+                            value = request
+                            def __enter__(self): return self
+                            def __exit__(self, *_): return False
+                        return Waiter()
+                    def get_by_role(self, role, *, name):
+                        assert (role, name) == ("button", button)
+                        return SimpleNamespace(click=lambda: calls.append(("click", name)))
+                    def get_by_text(self, text, *, exact):
+                        assert text == "Loading pending retailer requests…" and exact
+                        return SimpleNamespace(wait_for=lambda **k: calls.append(("hidden", k["state"])))
+                    def wait_for_function(self, js, *, arg, timeout):
+                        assert "shown.every((email, index) => email === expected[index])" in js
+                        assert "platform-review-item strong" in js
+                        assert 'role="alert"' in js
+                        assert arg == [target] and timeout == 15_000
+                        calls.append(("fence", tuple(arg)))
+                    def locator(self, selector):
+                        assert selector == ".platform-review-item strong"
+                        assert ("own-response", None) in calls
+                        assert ("fence", (target,)) in calls
+                        calls.append(("rows", None))
+                        return SimpleNamespace(all_inner_texts=lambda: [target])
 
-            def get_by_role(self, role, *, name):
-                assert (role, name) == ("button", "Refresh queue")
-                return SimpleNamespace(click=lambda: calls.append(("click", None)))
-
-            def get_by_text(self, text, *, exact):
-                assert text == "Loading pending retailer requests…"
-                assert exact
-                return SimpleNamespace(wait_for=lambda **k: calls.append(("hidden", k["state"])))
-
-            def wait_for_timeout(self, ms):
-                calls.append(("render", ms))
-
-            def locator(self, selector):
-                if selector == ".platform-approvals [role='alert']":
-                    return SimpleNamespace(count=lambda: 0)
-                assert selector == ".platform-review-item strong"
-                # Reading the newly created row BEFORE response finished is
-                # the regression: the old list must never be accepted.
-                assert ("response", "ok") in calls
-                assert ("render", 100) in calls
-                calls.append(("rows", None))
-                return SimpleNamespace(all_inner_texts=lambda: [target])
-
-        self.assertEqual(MOD.refresh_pending(FakePage()), {target})
-        self.assertEqual([entry[0] for entry in calls],
-                         ["expect", "click", "response", "hidden", "render", "rows"])
-
-    def test_refresh_denies_failed_rpc_and_wrong_route_or_method(self):
-        reply = SimpleNamespace(
-            url="https://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/rpc/retail_platform_onboarding_requests",
-            request=SimpleNamespace(method="POST"), ok=False)
+                self.assertEqual(operation(Page()), {target: target_id})
+                self.assertEqual([x[0] for x in calls],
+                                 ["expect-request", "click", "own-response",
+                                  "hidden", "fence", "rows"])
+
+    def test_request_predicate_and_failed_own_reply_fail_closed(self):
+        url = "https://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/rpc/retail_platform_onboarding_requests"
+        request = SimpleNamespace(url=url, method="POST")
+        reply = SimpleNamespace(url=url, request=request, ok=False)
+        self.assertTrue(MOD.is_onboarding_queue_request(request))
         self.assertTrue(MOD.is_onboarding_queue_reply(reply))
         for path, method in [
             ("https://evil.example.invalid/rest/v1/rpc/retail_platform_onboarding_requests", "POST"),
             ("http://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/rpc/retail_platform_onboarding_requests", "POST"),
             ("https://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/rpc/retail_platform_review_onboarding", "POST"),
-            (reply.url, "GET"),
+            (url, "GET"),
         ]:
             with self.subTest(path=path, method=method):
+                other = SimpleNamespace(url=path, method=method)
+                self.assertFalse(MOD.is_onboarding_queue_request(other))
                 self.assertFalse(MOD.is_onboarding_queue_reply(
-                    SimpleNamespace(url=path, request=SimpleNamespace(method=method))))
+                    SimpleNamespace(url=path, request=other)))
+        for failed_response in (None, reply, SimpleNamespace(
+            url="https://evil.example.invalid", request=request, ok=True)):
+            with self.subTest(response=repr(failed_response)):
+                request.response = lambda: failed_response
+                class Page:
+                    def expect_request(self, predicate, *, timeout):
+                        assert predicate(request)
+                        class Waiter:
+                            value = request
+                            def __enter__(self): return self
+                            def __exit__(self, *_): return False
+                        return Waiter()
+                    def get_by_role(self, *_args, **_kwargs):
+                        return SimpleNamespace(click=lambda: None)
+                    def get_by_text(self, *_args, **_kwargs):
+                        raise AssertionError("No DOM read after failed own response")
+                with self.assertRaisesRegex(RuntimeError, "HTTP request failed"):
+                    MOD.refresh_pending(Page())
+
+    def test_refresh_denies_malformed_queue_response_before_dom_read(self):
+        url = "https://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/rpc/retail_platform_onboarding_requests"
         class Page:
-            def expect_response(self, predicate, *, timeout):
-                assert predicate(reply)
+            def __init__(self, payload): self.payload = payload
+            def expect_request(self, predicate, *, timeout):
+                request = SimpleNamespace(url=url, method="POST")
+                reply = SimpleNamespace(url=url, request=request, ok=True,
+                                        json=lambda: self.payload)
+                request.response = lambda: reply
+                assert predicate(request)
                 class Waiter:
-                    value = reply
-                    def __enter__(self):
-                        return self
-                    def __exit__(self, *_):
-                        return False
+                    value = request
+                    def __enter__(self): return self
+                    def __exit__(self, *_): return False
                 return Waiter()
-            def get_by_role(self, role, *, name):
+            def get_by_role(self, *_args, **_kwargs):
                 return SimpleNamespace(click=lambda: None)
             def get_by_text(self, *_args, **_kwargs):
-                raise AssertionError("No DOM read after bad HTTP response")
-        with self.assertRaisesRegex(RuntimeError, "HTTP request failed"):
-            MOD.refresh_pending(Page())
+                raise AssertionError("No DOM read after invalid RPC body")
+            def wait_for_function(self, *_args, **_kwargs):
+                raise AssertionError("No DOM wait after invalid RPC body")
+        for payload in [{}, "text", [{"email": ""}], [{"email": 19}],
+                        [{"email": "same"}, {"email": "same"}], [{}],
+                        [{"email": "valid"}] * 41,
+                        [{"email": "x", "user_id": "not-uuid"}],
+                        [{"email": "x", "user_id": 4}],
+                        [{"email": "x", "user_id": "123e4567-e89b-12d3-a456-426614174000"}],
+                        [{"email": "a", "user_id": "123e4567-e89b-42d3-a456-426614174000"},
+                         {"email": "b", "user_id": "123e4567-e89b-42d3-a456-426614174000"}]]:
+            with self.subTest(payload=payload):
+                with self.assertRaisesRegex(RuntimeError, "queue"):
+                    MOD.refresh_pending(Page(payload))
+
+    def test_audited_root_approval_requires_exact_request_body_and_own_ack(self):
+        path = "https://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/rpc/retail_platform_review_onboarding"
+        user_id = "123e4567-e89b-42d3-a456-426614174000"
+        body = {"p_user_id": user_id, "p_approve": True,
+                "p_reason": MOD.DECISION_REASON}
+        req = SimpleNamespace(url=path, method="POST", post_data_json=body)
+        reply = SimpleNamespace(request=req, ok=True)
+        req.response = lambda: reply
+        self.assertTrue(MOD.is_onboarding_approval_request(req))
+        self.assertIs(MOD.verified_approval_reply(req, user_id), reply)
+        with self.assertRaisesRegex(RuntimeError, "mismatch"):
+            MOD.verified_approval_reply(req, "223e4567-e89b-42d3-a456-426614174000")
+        for bad in [
+            dict(body, p_approve=False),
+            dict(body, p_reason="wrong audit reason"),
+            dict(body, p_user_id="not-a-uuid"),
+            dict(body, p_user_id="123e4567-e89b-12d3-a456-426614174000"),
+            dict(body, extra="unapproved"),
+            {"p_approve": True},
+            None,
+        ]:
+            req.post_data_json = bad
+            with self.subTest(body=repr(bad)):
+                with self.assertRaisesRegex(RuntimeError, "mismatch"):
+                    MOD.verified_approval_reply(req, user_id)
+        req.post_data_json = body
+        for bad in [None, SimpleNamespace(request=req, ok=False),
+                    SimpleNamespace(request=SimpleNamespace(), ok=True)]:
+            req.response = lambda: bad
+            with self.subTest(response=repr(bad)):
+                with self.assertRaisesRegex(RuntimeError, "uncertain"):
+                    MOD.verified_approval_reply(req, user_id)
+        for url, method in [(path.replace("supabase.co", "evil.invalid"), "POST"),
+                            (path, "GET"),
+                            (path.replace("review_onboarding", "onboarding_requests"), "POST")]:
+            req.url, req.method = url, method
+            self.assertFalse(MOD.is_onboarding_approval_request(req))
+            with self.assertRaisesRegex(RuntimeError, "Wrong ROOT decision"):
+                MOD.verified_approval_reply(req, user_id)
+
+    def test_ui_approval_waits_for_bound_http_ack_before_considering_row_done(self):
+        path = "https://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/rpc/retail_platform_review_onboarding"
+        user_id = "123e4567-e89b-42d3-a456-426614174000"
+        email = "rgai-canary-012345abcdef-a@example.invalid"
+        calls = []
+        request = SimpleNamespace(
+            url=path, method="POST",
+            post_data_json={"p_user_id": user_id, "p_approve": True,
+                            "p_reason": MOD.DECISION_REASON})
+        response = SimpleNamespace(request=request, ok=True)
+        def own_reply():
+            calls.append("ack")
+            return response
+        request.response = own_reply
+
+        class FakeRow:
+            def __init__(self, texts): self.texts = texts
+            def filter(self, *, has):
+                calls.append("filter")
+                return self
+            def count(self): return 1
+            def locator(self, name):
+                assert name == "strong"
+                return SimpleNamespace(inner_text=lambda: email)
+            def get_by_role(self, role, *, name, **kwargs):
+                if role == "checkbox":
+                    assert name == "I verified this account request and authorize the decision."
+                    return SimpleNamespace(check=lambda: calls.append("check"))
+                assert role == "button"
+                return SimpleNamespace(click=lambda: calls.append("click-"+name))
+            def get_by_label(self, name):
+                return SimpleNamespace(fill=lambda value: calls.append("fill"),
+                                       check=lambda: calls.append("check"))
+            def wait_for(self, *, state, timeout):
+                assert state == "detached" and timeout == 15_000
+                assert "ack" in calls
+                calls.append("detach")
+
+        class Page:
+            def locator(self, name, **kwargs):
+                if name == "strong":
+                    return SimpleNamespace()
+                assert name == ".platform-review-item"
+                return FakeRow([])
+            def expect_request(self, predicate, *, timeout):
+                assert timeout == 15_000 and predicate(request)
+                calls.append("expect")
+                class Waiter:
+                    value = request
+                    def __enter__(self): return self
+                    def __exit__(self, *_): return False
+                return Waiter()
+            def get_by_text(self, value, *, exact):
+                assert (value, exact) == ("Retailer onboarding approved.", True)
+                return SimpleNamespace(count=lambda: 1)
+
+        MOD.approve_exact_row(Page(), email, user_id)
+        self.assertLess(calls.index("ack"), calls.index("detach"))
+        self.assertEqual(calls.count("click-Approve"), 1)
 
     def test_dispatch_only_uses_existing_gh_auth_and_protected_choice(self):
         with patch.object(MOD.subprocess, "run") as run:
~~~~

## PR #668 — HEAD d0814c492fef18b2dc948e309470f73687685d3a
https://github.com/saifsiddiqui59/RetailGrowthAI/pull/668/files

### docs/DECISIONS.md
~~~~diff
@@ -986,6 +986,13 @@
 ## 2026-10-29 — Private output response requires composed end-to-end denial evidence
 - Keep the current `Feature3PrivateBinaryHTTP` + `Feature3RevocablePNGReader` source adapters separate from an unapproved Azure route but test their actual composed boundary using real image bytes, twice-current tenant membership and independent rights callback, strict response headers and denial-without-bytes on revocation between authenticated Storage read and final response. Synthetic signed tokens and fake reviewer callbacks are tests only, never commercial licence or production release authorization.
 
+## 2026-10-29 — #249 WineShopPOS-style Node HTTP migration only through exact same-origin DEV preview
+- Reuse RetailGrowthAI's own existing Node22 Free-SWA managed HTTP preview as a candidate facade over real Supabase JWT/RLS RPCs and existing Python Queue/FFmpeg workers; do not move render execution into bounded Node HTTP, replace durable outbox/leases or transplant WineShopPOS code/secrets/resources.
+- Browser transport mode is explicitly OFF by default. Node preview JWT must be sent only via existing `x-rgai-supabase-jwt` on an **exact matched** isolated `p0249writes` API+browser origin; no arbitrary Azure Static Web Apps hostname, cross-origin token, browser storage override, hidden client fallback, generic proxy or automatic POST/PATCH replay. Signed session still requires Node JWKS and current shop RLS checks; UI config is not authorization. On Node-preview mode suppress Python's GET 503 direct-RLS fallback so hosted parity tests expose failure. Separate coordinator review, signed full DEV acceptance and rollback before any customer API origin move. Original Python Flex 503 cause needs separate diagnostics.
+
+## 2026-10-29 — #249 offline cross-feature contract fixtures never certify the live Node gateway
+- Verify every existing client campaign/poster/Reel method against the Node dispatcher using only synthetic JWT and stubbed read/write handlers before promoting any UI flag. This 13-route test is a wire-shape check, not model inference, authenticated JWT or private actual media. Real Playwright login cannot be inferred from a DOM-less blocked navigation; do not transmit user credentials to CI, fixtures, test logs or any other project. Use separately authorized ROOT and protected two-shop DEV canary, preserve Python Queue/FFmpeg and default frontend HTTP origin until exact live parity/reliability is proven. Log each external dependency with owner, required output and acceptance in #249 tracker.
+
 ## 2026-10-29 — Generated-history status views never change authorization
 - Client status filtering reuses existing read-only strict shop-scoped metadata, never sends status input as a new private query and never makes a job eligible for paid inference. Filtering a generated job out immediately clears its displayed private Blob and invalidates pending byte acceptance via the existing epoch counter. A SUCCEEDED state is **unreviewed**, not a publication or commercial-rights grant.
 
~~~~

### docs/NEXT_TASK.md
~~~~diff
@@ -1311,6 +1311,14 @@ Detailed handoff: `docs/feature3/PRE_GPU_READINESS_20261028.md`. No WineShopPOS
 ## 2026-10-29 — Feature3 binary HTTP/reader source E2E next gates
 - Review exact-head all four CI jobs for `feat/feature3-private-binary-reader-e2e-20261029`, preserve latest coordinator main, merge only after 4/4 and recheck fresh main. Actual authorized Azure binary route, true server-only current output/source commercial rights, new signed DEV customer and cross-tenant/expiry tests, verified generated PNG/evidence RPC SQL and existing 503 #249 resolution are independent release blockers. No GPU or hosted migrations from source tests.
 
+## 2026-10-29 — Issue #249 Node HTTP gateway migration (12 tracked tasks)
+- See `docs/part1/P0_249_NODE_GATEWAY_CUTOVER_TASKS_20261029.md` for tasks N01–N12, evidence and gates. Source-only initial N04/N05: review exact-host build-time OFF Node frontend transport, current user JWT custom header and same-origin requirement; test all campaign/poster/Reel endpoint paths against actual Node dispatcher, no service key/Authorization leak/unknown retry. Verify 4/4 exact PR-head CI and use coordinator integration with separate main CI.
+- Next release dependencies: actual full retailer SPA isolated deployment to existing Free SWA `p0249writes` host via reviewed coordinator-only workflow, owner-authenticated ROOT 2-shop `node-poster-reel` live acceptance including signed private PNG, 30s H264/AAC, rights, quota, outbox and negative roles/cleanup; 20+ request after-idle Node vs Python reliability evidence. Do not flip current `VITE_CAMPAIGN_API_BASE_URL`, relax JWT/role/CORS, invent signed media or activate paid AlwaysReady. Original Azure ingress cause unresolved; #249 OPEN. No WineShopPOS changes.
+
+## 2026-10-29 — #249 Node adapter independent route matrix and next gates
+- Keep open PR #668 source-only, verify complete 4/4 exact-head CI for new 13-route actual dispatcher mock matrix; coordinate separate #639 ROOT Playwright source PR through shared coordinator, preserve other feature work on rebases. Do not try credentials or ROOT operations through GitHub Actions or source fixtures.
+- Use `docs/part1/P0_249_NODE_GATEWAY_CUTOVER_TASKS_20261029.md` DEP-249-BROWSER-DEV / PREVIEW-SPA / ROOT-APPROVAL / POSTER-REAL / REEL-REAL / SECURITY-E2E / HTTP-TRACE / RELEASE for exact owner, required artifact and acceptance. The local Playwright attempt was network-blocked prior to login; no authenticated session. Continue read-only contract/negative fixtures without waiting for Feature2/3/4/5 outputs, preserve GPU OFF; all live media/tenant and Azure 503 causal gates are still pending.
+
 ## 2026-10-29 — Feature3 generated history filter rollout check
 - Confirm exact branch head four CI jobs for `feat/feature3-generated-history-scoped-filters-20261029`, coordinator merge against latest main and fresh main 4/4. Status filtering is local to already-authorized shop metadata; no actual generated image can be considered reviewed, reusable or published until external rights, real private output evidence and gated signed DEV binary route acceptance. Keep GPU and PROD unchanged.
 
~~~~

### docs/PROJECT_STATE.md
~~~~diff
@@ -1329,6 +1329,15 @@ See docs/NEXT_TASK.md. Live integrations and cloud deployment remain blocked by
 ## 2026-10-29 — Feature3 private PNG HTTP/reader full-source integration QA
 - Added real Pillow PNG/mocked private HTTPS end-to-end source contract testing across the existing `Feature3PrivateBinaryHTTP` and real `Feature3RevocablePNGReader`: exact JWT/RLS user/tenant and twice-current source rights, private SHA-named pixels, zero leaked bytes for revoked membership/licence, foreign job, failed job, changed HTTP size or encoded response. No Azure binary route mounted or true commercial rights authority deployed. See `docs/feature3/PRIVATE_BINARY_SOURCE_COMPOSITION_E2E_20261029.md`; four CI jobs required. No GPU, migrations, PROD, WineShopPOS.
 
+## 2026-10-29 — Issue #249 candidate Node HTTP transport, WineShopPOS-style (OFF)
+- Reviewed WineShopPOS's existing authenticated Node Azure Functions AI client and direct Supabase-first business operations, and read the prior Voice comparison (Voice-agent GitHub only README, live runtime unverified). Reused existing RetailGrowthAI Free SWA Node candidate; preserved original Azure Python Queue/Timer/FFmpeg authority and original customer Python HTTP URL.
+- On isolated `fix/p0249-node-http-transport-candidate-20261029`, implemented **source-only**, exact pinned `p0249writes` same-browser-origin Node mode for the campaign API with an explicit OFF-by-default Vite build flag; sends user JWT in `x-rgai-supabase-jwt` to this verified preview only and never Authorization/cookies or any customer cross-origin Node. Existing Python mode is unchanged. Bounded GET retries remain; Node mode deliberately disables Python 503 direct Supabase read fallback to expose gateway failure; POST/PATCH no replay. Added offline 13-route and actual Node dispatcher mock-composition negative/security tests. Release tracker: `docs/part1/P0_249_NODE_GATEWAY_CUTOVER_TASKS_20261029.md`.
+- No change to `frontend/.env.production`, current deployed frontend/Node host, migration, Azure resource, existing signed customer API, paid capacity, PROD or WineShopPOS. Real signed tenant/ROOT-approved private poster+30s MP4 parity, original Python ~61s 503 trace, full SPA same-origin preview deployment and coordinator release remain unverified. New exact-head 4/4 CI still required.
+
+## 2026-10-29 — #249 Node source continuation, Playwright connectivity and full route dispatch
+- Independently extended open PR #668's candidate Node switch with `tests/frontend/p0249-node-full-route-dispatch.test.mjs`: all 13 existing campaign/poster/Reel browser HTTP methods traverse actual Node secure dispatcher with synthetic JWT and downstream mock; asserts exact verbs/paths/JSON and single-write 401/403/404/409/402/429 denials. These are not authenticated hosted results, actual AI outputs, licensed source media or genuine 30s private MP4. Root #249 503 remains open and Python worker unchanged.
+- Local Playwright (installed headless Chromium) attempted to navigate to existing DEV retailer SPA and was blocked before page load (`net::ERR_BLOCKED_BY_ADMINISTRATOR`); no password sent, account sign-in, ROOT approval, canary, database action or paid deployment occurred. `docs/part1/P0_249_NODE_GATEWAY_CUTOVER_TASKS_20261029.md` now lists exact DEP-249-* owner/output/acceptance gates. DEV Node preview has only a placeholder frontend; no live cutover authorized. CI exact HEAD pending.
+
 ## 2026-10-29 — Feature3 generated private history local status views (GPU OFF)
 - Added accessible read-only local status filters for existing 20-row bounded RLS validated job history: All/Queued/Running/Generated (unreviewed)/Failed. Switching filters invalidates pending private binary fetch and revokes any active preview Blob; only visible current-shop SUCCEEDED output may be shown. Node tests cover foreign/malformed statuses and privacy cleanup. Source-only UI, no hosted images or binary route, GPU, queue, billing, migrations, PROD or WineShopPOS. Details: docs/feature3/GENERATED_HISTORY_SCOPED_FILTERS_20261029.md.
 
~~~~

### docs/WORK_LOG.md
~~~~diff
@@ -746,6 +746,10 @@ Use scripts/checkpoint.sh after completing a task.
 ## 2026-10-29 — Feature3 binary HTTP + private SHA/Pillow reader integration source tests
 - After #669 merged at `e900c5a3ffa5a854a702289dddad0872ffd901c3`, new `feat/feature3-private-binary-reader-e2e-20261029` branch adds a full real-source composition test of JWT-scoped binary handler, current RLS/rights and mocked private HTTPS with original Pillow PNG, changed HTTP length/recode, revocation midstream, wrong shop/job and backend uncertainty. No live signed user, true independent licence, provider, activated route, billing, queue, hosted migrations, PROD or WineShopPOS. PR/exact-head and postmerge main CI pending verification.
 
+- 2026-10-29 — Issue #249 Node gateway candidate start: read mandatory AGENTS/project/architecture/interface/CI docs, WineShopPOS read-only `aiClient.js` + Node Functions + Supabase client, Voice repository (README-only), existing RetailGrowthAI secure Node candidate and historical 9/20 Python vs 0/20 synthetic Node controls. Created separate p0249 Node candidate branch (not PR #639, which still covers ROOT test helper). Implemented opt-in exact same-origin build-gated campaign HTTP client for existing `p0249writes` Free SWA preview, preserving current Python defaults and disabling Node-mode hidden direct RLS GET fallback. Wrote mock full 13-route HTTP test suite including exact custom JWT header, no cross-origin, no credentials, no retries on uncertain writes and composing with actual dispatcher. Added 12-task release gate document. No DEV/PROD runtime, new paid resource, migration, customer traffic or WineShopPOS modification. Exact-head CI to be verified; original issue #249 remains open.
+
+- 2026-10-29 — Extended Issue #249 PR #668 after re-reading all AGENTS-required docs, current main and open #668/#639 and old closed-draft #568. Launched installed Playwright Chromium to the existing DEV RetailGrowthAI SPA; it failed before page load with `ERR_BLOCKED_BY_ADMINISTRATOR`; no credentials submitted, session, Azure or Supabase mutation. Added deterministic 13-method browser→Node dispatcher request-shape test with fake JWT and denied status boundary checks; kept fake data explicitly separate from actual signed tenant/AI/media E2E. Extended tracker with DEP-249-* dependencies (owning feature, required artifact, acceptance) and no cross-feature pause. Source only; original gateway 503 unresolved, no WineShopPOS/PROD/GPU/paid changes. Exact-head full CI to verify.
+
 ## 2026-10-29 — Feature3 generated-history local status filtering
 - Branch `feat/feature3-generated-history-scoped-filters-20261029` from post-#672 source main `afe78543588adcd7c2ac716720d965337f04e240` improves existing generated job history with five local accessibility-labeled status views, no additional fetch/API/GPU calls, and releases private Blob previews on filter changes. Added pure Node metadata/tenant/immutable filter checks and React source lifecycle assertions, handoff + canonical documents. PR exact-head and postmerge main CI still required; no rights/hosted release implied, WineShopPOS untouched.
 
~~~~

### docs/part1/P0_249_NODE_GATEWAY_CUTOVER_TASKS_20261029.md
~~~~diff
@@ -0,0 +1,57 @@
+# Issue #249 — WineShopPOS-style Node HTTP facade migration tasks (2026-10-29)
+
+**Scope:** Reuse the existing RetailGrowthAI `experiments/secure-node-http/` Node 22 Free SWA managed-API *DEV candidate* and the current Supabase user JWT/RLS RPC/outbox, while keeping the original Python Functions Queue/Timer + FFmpeg rendering authoritative. No access to or modification of WineShopPOS or Voice Agent deployments. This is not a Python Flex 503 root-cause fix.
+
+**Observed baseline:** original Python Flex Central India HTTP 9/20 genuine unmarked ~61s 503; same experiment Node synthetic 0/20 expected 401; neither is proof of authenticated production-like parity. See `P0_249_20261028_HTTP_INGRESS_ATTRIBUTION_VERDICT.md`.
+
+| ID | Scope | Acceptance | State |
+|---|---|---|---|
+| N01 | Compare WineShopPOS/Voice HTTP design and existing Node candidate | Read-only current source review, do not assume Voice has a deployed runtime | DONE |
+| N02 | Inventory Node route contract vs original Python | Seven GETs and six POST/PATCH candidate methods at fixed `/api` paths; ensure Python Queue/FFmpeg stays intact | SOURCE CHECKED; full signed parity NOT PROVED |
+| N03 | Verify JWT + Supabase tenant isolation in candidate | Node JWKS ES256/RS256, user JWT/current RLS checks, OWNER/EDITOR/VIEWER/foreign/revoked and media rights negative gates | SOURCE TESTS EXIST; live roles gate PENDING |
+| N04 | Build frontend Node transport adapter | Exact source-reviewed `p0249writes` preview origin, same-origin document, explicit build flag, custom independently verified JWT transport only, default Python unchanged | THIS BRANCH (SOURCE) |
+| N05 | Test browser→Node request shape with mock dispatcher | Exact 13 public v1 methods; no auth cookie/service key; Node request `x-rgai-supabase-jwt` and unchanged JSON; no silent redirect | THIS BRANCH (OFFLINE TESTS) |
+| N06 | Verify contract parity of all real read/write routes | Signed actual campaign create, DRAFT save, poster create/render/select, Reel submit/status and private downloads | EXISTING SOURCE PARTIAL; positive hosted E2E PENDING |
+| N07 | Validate durable jobs, billing and mutation uncertainty | Existing user-RLS RPC quotas, same-transaction outbox, CAS/leases, at most one mutation; no replay after lost 503 | OFFLINE NEGATIVE TESTS; live behavior PENDING |
+| N08 | Protected actual signed-in two-shop DEV canary | Normal ROOT approval within timed window; fresh two shops, real private PNG, 30s H264/AAC FFprobe, foreign/VIEWER deny, cleanup | BLOCKED BY OWNER ROOT INTERACTIVE AUTH + DISPATCH |
+| N09 | Reliability/head-to-head HTTP comparison | 20+ measured first/warm/idle/concurrent routes for current Python and isolated Node; separate application vs gateway 503, p95/p99 | BLOCKED BY AUTHORIZED LIVE TEST + ORIGINAL AZURE DIAGNOSTICS |
+| N10 | Reversible DEV API cutover | Reviewed deployment of full frontend onto same Node preview for same-origin JWT; verified exact deployment SHA, no customer cutover; rollback by deleting preview or restoring Python origin | PENDING COORDINATOR/OWNER APPROVAL |
+| N11 | Coordinator PR merge and postmerge CI | 4/4 exact-head PR jobs, coordinator-owned merge only, independent 4/4 main jobs | PENDING |
+| N12 | Issue #249 closure | Retire original unmarked 503 based on causal Azure evidence or explicitly approved reliable replacement; real tenant/media parity proven, no paid surprise | BLOCKED; issue OPEN |
+
+## First implementation: fail-closed frontend transport
+
+`frontend/src/features/campaigns/campaign-api.mjs` supports `transport:'node-preview'` only when both the configured API origin AND the actual browser document origin exactly match the pinned existing Free SWA `p0249writes` hostname. It sends the current Supabase JWT in `x-rgai-supabase-jwt` solely to that same origin, with no `Authorization`, credentials, cookies, redirects or service-role key. The Node gateway independently checks cryptographic signature and caller RLS; the header is not proof of authorization by itself.
+
+**Ambient cookie isolation fix (2026-11-08):** Browser `fetch` defaults to `credentials: 'same-origin'`, so merely omitting the `Cookie` header from JavaScript does NOT prevent cookies from accompanying a same-origin Node preview request. Explicitly set `credentials: 'omit'` for the Node-preview mode on all 13 v1 methods. Keep the original Python transport's fetch defaults unchanged. The mock transport regression now asserts explicit cookie suppression and unchanged Python defaults. This is source-only risk reduction, not deployed signed-host parity or a fix for Python Flex ingress 503.
+
+`CampaignDashboard.jsx` only selects this mode when `VITE_P0249_NODE_TRANSPORT_ENABLED === 'true'` at **build time**; otherwise it uses the unchanged Python `VITE_CAMPAIGN_API_BASE_URL`. Production .env stays unchanged; no toggle via URL/localStorage/query or redirect; build with a different host fails closed before requesting a token. The current `p0249writes` preview does not contain the full retailer SPA and **must not** be treated as a ready-to-use live website. Coordinator must first build and deploy the reviewed full SPA to that *same exact* isolated named preview before enabling the flag.
+
+Existing safe GET-only bounded retries continue, but the Node preview deliberately disables the Python 503 direct-Supabase-render-read fallback so live gateway comparisons cannot be hidden. POST/PATCH are one-shot only; an uncertain ACK fails and must be reconciled by authenticated read before further action.
+
+## Release / cost / security boundaries
+
+- Do **not** modify `frontend/.env.production`, existing Free SWA production environment, `VITE_CAMPAIGN_API_BASE_URL`, Python HTTP endpoint, SUPABASE schema, Azure queue/worker, billed plans, WineShopPOS or Voice.
+- The current Node DEV preview has synthetic/negative and some genuine signed-in tests, but **not** a complete ROOT-approved private campaign/poster/30s Reel happy path. Do not direct customer traffic or assume Node 0/20 synthetic 503 proves parity.
+- Only the coordinator may alter `.github/workflows/**`, shared interfaces, integrate `main` or approve actual deployment. An owner/operator must explicitly authorize a protected DEV canary and perform real ROOT UI approval; never impersonate ROOT or embed credentials.
+- Keep Issue #249 open and preserve `AZURE_INTERNAL_TRACE_REQUIRED` for original Python Flex ingress→scale→worker causal trace. A working replacement route does not explain the original 503.
+
+
+## 2026-10-29 continued — independent code vs exact external dependency ledger
+
+Source-only evidence: `tests/frontend/p0249-node-full-route-dispatch.test.mjs` drives **all 13** browser campaign/poster/Reel methods through the existing actual Node `createSecureHttpDispatcher` with synthetic JWT and mocked downstream handlers, checks original path/verb/JSON and no header/token cross-origin forwarding; checks 401/403/404/409/402/429 single-write denials. Test fixtures are **not** AI output, approved commercial media, hosted JWT or release acceptance. No need to wait for Features #2/#3/#4/#5 to provide genuine production artifacts to run source tests.
+
+Playwright attempt: launched installed headless Chromium against the existing DEV Static Web App HTTPS login host; navigation failed **before** a page load with `net::ERR_BLOCKED_BY_ADMINISTRATOR`. No credentials submitted, browser login, authenticated session, Azure deployment, ROOT decision or mutation. The isolated Node `p0249writes` preview is still a placeholder and does not itself provide the full retailer login SPA. Protected canary also requires a separate approved owner-dispatched workflow. Do not copy credentials into repo, CI variables, logs or fixtures.
+
+| Dependency ID | Blocked task | Owning workstream | Required artifact / input | Acceptance / unblock proof |
+|---|---|---|---|---|
+| DEP-249-BROWSER-DEV | N08 actual Playwright login | Issue #249 DEV operator/environment | Network-reachable existing approved RetailGrowthAI **DEV** SPA and a real owner-authenticated browser; no reuse of WineShopPOS or PROD | Actual app login page loads, current user JWT verified, role/current shop established; safely record redacted evidence only |
+| DEP-249-PREVIEW-SPA | N08/N10 Node browser flow | Issue #249 + shared coordinator | Reviewed full RetailGrowthAI SPA build mounted at **same** existing `p0249writes` hostname with opt-in transport flag and existing isolated Node handlers; coordinator-only deployment workflow | Signed session works same-origin; exact deployed SHA and rollback source recorded; customer Python origin unchanged |
+| DEP-249-ROOT-APPROVAL | N08 two-shop positive canary | Feature #1 ROOT onboarding + Issue #249 operator | Explicitly approved protected manual DEV canary; two unique disposable retailer accounts; operator applies genuine ROOT approval before window closes | Both exact pending account IDs approved once by authenticated ROOT, actual signed user sessions, private two-shop negatives and finally cleanup PASS; PR #639 remains a separate pending source integration |
+| DEP-249-POSTER-REAL | N06/N08 poster flow | Feature #3 Poster Studio | Existing legitimate test original owned/source-rights asset, applied current DEV poster RPC/migrations and working private PNG output from CPU renderer (no GPU required) | Real tenant upload, original rights and DRAFT lineage verified; 1080x1350 PNG signed private read, banner optimistic CAS and revoked/foreign negatives |
+| DEP-249-REEL-REAL | N06/N07/N08 30-second Reel flow | Feature #4 Video Studio + Part 1 render worker | Existing rights-safe fixture inputs and Python Queue/FFmpeg worker path; authoritative user-token `request_reel_render_job` RPC/outbox/usage state in DEV | Actual atomic one-job+outbox+quota, stable idempotency/lease, 29–31-second portrait H.264/AAC private MP4 and negative cross-tenant signed URL; never label mocked media a real render |
+| DEP-249-SECURITY-E2E | N03/N06/N07 | Issue #249 Node gateway + Supabase/Part 1 backend | Authenticated JWT/JWKS transport and DEV Supabase RLS/RPC rights and billing verification | OWNER/EDITOR positive; VIEWER, revoked, foreign and expired token negative; uncertain POST read-reconciliation and one-charge semantics verified on DEV |
+| DEP-249-HTTP-TRACE | N09/N12 original 503 root cause | Azure Issue #249 DEV infra owner / Azure internal diagnostics | Request-correlated Azure ingress→HTTP-scale-group→host→Python worker trace for true 9/20 unmarked ~61-second 503 samples | Named causal component/condition and approved reversible repair; repeated HTTP warm/idle/concurrency samples plus p95/p99, no speculative AlwaysReady spend |
+| DEP-249-RELEASE | N10/N11/N12 | Shared coordinator | Reviewed PR #668 + existing #639 separate ROOT helper PR, protected workflow/release plan and exact main CI | All four PR jobs success on exact head, coordinator-only merge, independent main 4/4, approved isolated DEV release/rollback and complete E2E before any customer cutover |
+
+**Independent / not blocked:** N01/N02 source comparison, N04/N05 secure frontend adapter and tests, all-route mocked dispatch matrix, source-only negative roles/error/mutation cases, deterministic CI, migration-readiness documentation, and honest input/output trace fixtures. Do not wait on actual Creative Director (#2), Fashion media (#3), video composition (#4) or GPU Motion (#5) to complete these independent tasks; none of their mock fixtures establish hosted media acceptance.
~~~~

### frontend/src/features/campaigns/CampaignDashboard.jsx
~~~~diff
@@ -1,6 +1,6 @@
 import { useEffect, useMemo, useRef, useState } from 'react'
 import { useRetailAuth } from '../../auth/AuthProvider.jsx'
-import { createCampaignApi, validateSignedVideoUrl } from './campaign-api.mjs'
+import { createCampaignApi, validateSignedVideoUrl, P0249_NODE_PREVIEW_ORIGIN } from './campaign-api.mjs'
 import sampleCampaign from './fixtures/sample-campaign.json'
 import {
   buildCampaignRequest, cloneCampaign, formatDayDate, linkedInText,
@@ -392,12 +392,18 @@ function LiveImageUploader({ client, shopId, onUploaded }) {
 
 export default function CampaignDashboard() {
   const { user, client } = useRetailAuth()
+  // OFF unless this frontend build is deliberately deployed into the exact
+  // isolated DEV named-preview origin. The normal customer site stays on Python.
+  const nodePreview = import.meta.env?.VITE_P0249_NODE_TRANSPORT_ENABLED === 'true'
   const api = useMemo(() => createCampaignApi({
-    baseUrl: import.meta.env?.VITE_CAMPAIGN_API_BASE_URL || '',
+    baseUrl: nodePreview ? P0249_NODE_PREVIEW_ORIGIN :
+      (import.meta.env?.VITE_CAMPAIGN_API_BASE_URL || ''),
+    transport: nodePreview ? 'node-preview' : 'python',
+    browserOrigin: typeof window === 'undefined' ? '' : window.location.origin,
     tokenProvider: () => client.getAccessToken(),
     supabaseOrigin: import.meta.env?.VITE_SUPABASE_URL || '',
     supabasePublishableKey: import.meta.env?.VITE_SUPABASE_PUBLISHABLE_KEY || '',
-  }), [client])
+  }), [client, nodePreview])
   const [shops, setShops] = useState([])
   const [shopId, setShopId] = useState('')
   const [assets, setAssets] = useState([])
~~~~

### frontend/src/features/campaigns/campaign-api.mjs
~~~~diff
@@ -1,6 +1,11 @@
 import { createRenderReadFallback } from './reel-rls-fallback.mjs'
 import { collectHttpReceipt } from '../../lib/feature-http-receipt.mjs'
 // Browser-only authenticated API gateway; never sends service keys or synthetic media IDs.
+// The only permitted Node transport today is the isolated, existing Free SWA
+// DEV named-preview. No environment flag may rebind a customer's JWT to an
+// arbitrary API origin, including a different azurestaticapps.net subdomain.
+export const P0249_NODE_PREVIEW_ORIGIN =
+  'https://purple-dune-06b5da200-p0249writes.eastasia.2.azurestaticapps.net'
 const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
 
 function uuid(value) {
@@ -20,16 +25,29 @@ export function validateSignedVideoUrl(url, supabaseOrigin) {
 }
 
 export function createCampaignApi({ baseUrl, tokenProvider, fetchImpl = fetch,
-  supabaseOrigin = '', supabasePublishableKey = '', onResponse = null }) {
+  supabaseOrigin = '', supabasePublishableKey = '', onResponse = null,
+  transport = 'python', browserOrigin = '' }) {
   if (!baseUrl || typeof baseUrl !== 'string') return null
   const parsed = new URL(baseUrl)
   if (parsed.protocol !== 'https:' || parsed.username || parsed.password ||
       parsed.search || parsed.hash || !['', '/'].includes(parsed.pathname)) {
     throw new Error('Campaign API must use an HTTPS origin')
   }
   if (typeof tokenProvider !== 'function') throw new Error('Authenticated token provider required')
+  if (transport !== 'python' && transport !== 'node-preview') {
+    throw new Error('Unsupported campaign API transport')
+  }
   const origin = parsed.origin
-  const statusFallback = createRenderReadFallback({
+  const nodePreview = transport === 'node-preview'
+  // A signed JWT must never be forwarded cross-origin to a preview endpoint.
+  // Build-time opt-in is insufficient: the document itself must be served by
+  // the exact same reviewed and isolated DEV Node SWA preview hostname.
+  if (nodePreview && (origin !== P0249_NODE_PREVIEW_ORIGIN ||
+      browserOrigin !== P0249_NODE_PREVIEW_ORIGIN ||
+      baseUrl !== P0249_NODE_PREVIEW_ORIGIN)) {
+    throw new Error('Node preview transport requires exact same-origin DEV preview')
+  }
+  const statusFallback = nodePreview ? null : createRenderReadFallback({
     supabaseOrigin, publishableKey: supabasePublishableKey,
     tokenProvider, fetchImpl,
   })
@@ -52,7 +70,10 @@ export function createCampaignApi({ baseUrl, tokenProvider, fetchImpl = fetch,
   const READ_ATTEMPTS = 2
   async function request(method, path, body) {
     const token = await tokenProvider()
-    if (typeof token !== 'string' || !token) throw new Error('Please sign in again')
+    if (typeof token !== 'string' || !token || (nodePreview &&
+        (token.length < 10 || token.length > 8192 || /[\s,\u0000-\u001f\u007f,]/.test(token)))) {
+      throw new Error('Please sign in again')
+    }
     // Only pure reads can be re-issued. A lost acknowledgement of POST/PATCH
     // may mean the DB transaction already committed; never blindly replay it.
     const attempts = method === 'GET' ? READ_ATTEMPTS : 1
@@ -64,8 +85,13 @@ export function createCampaignApi({ baseUrl, tokenProvider, fetchImpl = fetch,
       try {
         response = await fetchImpl(origin + '/api' + path, {
           method, redirect: 'error', cache: 'no-store',
+          // A browser's default same-origin mode can send ambient cookies.
+          // The isolated Node preview uses only the explicit user JWT header.
+          ...(nodePreview ? { credentials: 'omit' } : {}),
           headers: {
-            Authorization: 'Bearer ' + token,
+            ...(nodePreview
+              ? { 'x-rgai-supabase-jwt': token }
+              : { Authorization: 'Bearer ' + token }),
             ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
           },
           ...(controller ? { signal: controller.signal } : {}),
~~~~

### tests/frontend/p0249-node-full-route-dispatch.test.mjs
~~~~diff
@@ -0,0 +1,119 @@
+import test from 'node:test'
+import assert from 'node:assert/strict'
+import { createCampaignApi, P0249_NODE_PREVIEW_ORIGIN } from '../../frontend/src/features/campaigns/campaign-api.mjs'
+import { createSecureHttpDispatcher } from '../../experiments/secure-node-http/src/secure-api-dispatch.mjs'
+
+// Pure source-to-source route compatibility, not a signed-in or hosted E2E.
+const ORIGIN = P0249_NODE_PREVIEW_ORIGIN
+const CAMPAIGN = '11111111-1111-4111-8111-111111111111'
+const DAY = '22222222-2222-4222-8222-222222222222'
+const POSTER = '33333333-3333-4333-8333-333333333333'
+const JOB = '44444444-4444-4444-8444-444444444444'
+const TOKEN = 'synthetic.test.token'
+const item = (method, path, kind, invoke, payload = undefined) =>
+  ({ method, path: '/api' + path, kind, invoke, payload })
+const actions = [
+  item('GET', '/campaigns/' + CAMPAIGN, 'read', api => api.getCampaign(CAMPAIGN)),
+  item('GET', '/render-jobs/' + JOB, 'read', api => api.getRenderJob(JOB)),
+  item('GET', '/render-jobs/' + JOB + '/download', 'read', api => api.getDownload(JOB)),
+  item('GET', '/poster-drafts/' + POSTER, 'read', api => api.getPosterDraft(POSTER)),
+  item('GET', '/campaigns/' + CAMPAIGN + '/days/' + DAY + '/posters', 'read',
+    api => api.listPosterDrafts(CAMPAIGN, DAY)),
+  item('GET', '/poster-jobs/' + JOB, 'read', api => api.getPosterJob(JOB)),
+  item('GET', '/poster-jobs/' + JOB + '/download', 'read', api => api.getPosterDownload(JOB)),
+  item('POST', '/campaigns', 'campaign',
+    api => api.createCampaign({ brief: 'synthetic fixture' }), { brief: 'synthetic fixture' }),
+  item('PATCH', '/campaigns/' + CAMPAIGN + '/days/' + DAY, 'campaign',
+    api => api.saveDay(CAMPAIGN, DAY, {topic:'Topic',linkedin:{post_text:'Text'},instagram:{caption:'Caption'}}),
+    {topic:'Topic',linkedin:{post_text:'Text'},instagram:{caption:'Caption'}}),
+  item('POST', '/campaigns/' + CAMPAIGN + '/posters', 'poster',
+    api => api.createPosterDraft(CAMPAIGN, {
+      day_id:DAY,source_asset_id:POSTER,template:'minimal',format:'portrait',
+      business_name:'Fixture',accent_color:'#FFFFFF',background_color:'#000000',
+    }),
+    {day_id:DAY,source_asset_id:POSTER,logo_asset_id:null,template:'minimal',format:'portrait',
+      business_name:'Fixture',accent_color:'#FFFFFF',background_color:'#000000',offer_text:null}),
+  item('POST', '/poster-drafts/' + POSTER + '/renders', 'poster',
+    api => api.createPosterRender(POSTER), {}),
+  item('POST', '/poster-drafts/' + POSTER + '/select', 'poster',
+    api => api.selectPosterBanner(POSTER,{banner_asset_id:null}),
+    {expected_instagram:{banner_asset_id:null}}),
+  item('POST', '/campaigns/' + CAMPAIGN + '/renders', 'reel',
+    api => api.createRender(CAMPAIGN,DAY),{day_id:DAY,preset:'instagram_reel_30s'}),
+]
+
+test('all 13 browser API methods arrive at the existing Node dispatcher with exactly the original paths and JSON',async()=>{
+  let index=0, jwtRequests=0
+  const seen=[]
+  const dispatch=createSecureHttpDispatcher({
+    allowedOrigin:ORIGIN,writesEnabled:true,renderWritesEnabled:true,
+    readGateway:downstream('read'),campaignGateway:downstream('campaign'),
+    posterGateway:downstream('poster'),reelGateway:downstream('reel'),
+  })
+  function downstream(kind) {
+    return async(method,path,bearer,body)=>{
+      seen.push({kind,method,path,bearer,body})
+      return {status:200,jsonBody:{accepted:true},headers:{}}
+    }
+  }
+  const api=createCampaignApi({
+    baseUrl:ORIGIN,browserOrigin:ORIGIN,transport:'node-preview',
+    tokenProvider:async()=>{jwtRequests++;return TOKEN},
+    fetchImpl:async(url,options)=>{
+      const entry=actions[index++]
+      assert.ok(entry,'Unexpected extra request')
+      assert.equal(url,ORIGIN+entry.path)
+      assert.equal(options.method,entry.method)
+      assert.equal(options.credentials,'omit')
+      assert.equal(options.headers.Authorization,undefined)
+      assert.equal(options.headers['x-rgai-supabase-jwt'],TOKEN)
+      assert.equal(options.headers['Content-Type'],entry.method==='GET'?undefined:'application/json')
+      const request={url,method:options.method,
+        headers:new Headers({...options.headers,origin:ORIGIN,'sec-fetch-site':'same-origin'}),
+        text:async()=>options.body||''}
+      const response=await dispatch(request)
+      return {ok:response.status>=200&&response.status<300,status:response.status,
+        json:async()=>response.jsonBody}
+    },
+  })
+  for(const entry of actions) await entry.invoke(api)
+  assert.equal(index,13)
+  assert.equal(jwtRequests,13)
+  assert.equal(seen.length,13)
+  for(let i=0;i<actions.length;i++) {
+    const wanted=actions[i],actual=seen[i]
+    assert.equal(actual.kind,wanted.kind)
+    assert.equal(actual.method,wanted.method)
+    assert.equal(actual.path,wanted.path)
+    assert.equal(actual.bearer,'Bearer '+TOKEN)
+    assert.deepEqual(actual.body,wanted.payload)
+  }
+})
+
+test('a verified transport with denied or missing tenant cannot silently become a successful client operation',async()=>{
+  for(const status of [401,403,404,409,402,429]){
+    let calls=0
+    const api=createCampaignApi({
+      baseUrl:ORIGIN,browserOrigin:ORIGIN,transport:'node-preview',
+      tokenProvider:async()=>TOKEN,
+      fetchImpl:async()=>{calls++;return {status,ok:false,json:async()=>({error:'DENIED'})}},
+    })
+    await assert.rejects(()=>api.createCampaign({brief:'fixture'}),error=>error.status===status)
+    assert.equal(calls,1)
+  }
+})
+
+test('Node mode cannot turn a missing or hostile browser token into a cross-origin fallback request',async()=>{
+  for(const browserOrigin of [
+    'https://purple-dune-06b5da200.2.azurestaticapps.net',
+    'https://evil.example.invalid',ORIGIN+'/', '']){
+    let tokenReads=0,network=0
+    assert.throws(()=>createCampaignApi({
+      baseUrl:ORIGIN,browserOrigin,transport:'node-preview',
+      tokenProvider:async()=>{tokenReads++;return TOKEN},
+      fetchImpl:async()=>{network++;return {status:200,ok:true,json:async()=>({})}},
+    }),/same-origin DEV preview/)
+    assert.equal(tokenReads,0)
+    assert.equal(network,0)
+  }
+})
~~~~

### tests/frontend/p0249-node-transport-candidate.test.mjs
~~~~diff
@@ -0,0 +1,159 @@
+import test from 'node:test'
+import assert from 'node:assert/strict'
+import { readFileSync } from 'node:fs'
+import { createCampaignApi, P0249_NODE_PREVIEW_ORIGIN } from '../../frontend/src/features/campaigns/campaign-api.mjs'
+import { createSecureHttpDispatcher } from '../../experiments/secure-node-http/src/secure-api-dispatch.mjs'
+
+// All tests are offline. No real JWT, DNS, Azure, Supabase or test customer.
+const SHOP = '11111111-1111-4111-8111-111111111111'
+const DAY = '22222222-2222-4222-8222-222222222222'
+const USER_TOKEN = 'example.signed.fixture'
+const base = P0249_NODE_PREVIEW_ORIGIN
+const make = (opts={}) => createCampaignApi({
+  baseUrl: base, browserOrigin: base, transport: 'node-preview',
+  tokenProvider: async () => USER_TOKEN, fetchImpl: async () => ({
+    status: 200, ok: true, json: async () => ({ok: true}),
+  }), ...opts,
+})
+
+test('Node gateway option rejects wrong site, forged preview and unsupported mode before obtaining a JWT', async () => {
+  let tokens = 0, sent = 0
+  const opts = {tokenProvider: async () => { tokens++; return USER_TOKEN },
+    fetchImpl: async () => { sent++; throw Error('should never fetch') }}
+  for (const browserOrigin of ['', 'https://purple-dune-06b5da200.2.azurestaticapps.net',
+    'https://attacker.invalid', base + '/', 'http://'+new URL(base).host]) {
+    assert.throws(() => make({...opts,browserOrigin}), /same-origin DEV preview/)
+  }
+  for (const badOrigin of ['https://some-other.azurestaticapps.net',
+    'https://evil.invalid', base+'/', 'http://'+new URL(base).host]) {
+    assert.throws(() => make({...opts,baseUrl:badOrigin}), /same-origin DEV preview|HTTPS origin/)
+  }
+  assert.throws(() => make({...opts,transport:'node'}), /Unsupported/)
+  assert.equal(tokens,0)
+  assert.equal(sent,0)
+})
+
+test('only this preview can use the custom Supabase header; never Authorization or cookies', async () => {
+  const calls = []
+  const api = make({fetchImpl: async (url, options) => {
+    calls.push({url,options})
+    return {status:200,ok:true,json:async()=>({ok:true})}
+  }})
+  await api.getCampaign(SHOP)
+  await api.createCampaign({brief:'synthetic only'})
+  await api.saveDay(SHOP,DAY,{topic:'t',linkedin:{},instagram:{}})
+  await api.createRender(SHOP,DAY)
+  await api.createPosterDraft(SHOP,{
+    day_id:DAY,source_asset_id:DAY,template:'bold',format:'portrait',
+    business_name:'Test',accent_color:'#FFFFFF',background_color:'#000000',
+  })
+  await api.getPosterDraft(DAY)
+  await api.listPosterDrafts(SHOP,DAY)
+  await api.createPosterRender(DAY)
+  await api.getPosterJob(DAY)
+  await api.getPosterDownload(DAY)
+  await api.selectPosterBanner(DAY,{banner_asset_id:null})
+  await api.getRenderJob(DAY)
+  await api.getDownload(DAY)
+  assert.equal(calls.length,13)
+  for (const {url,options} of calls) {
+    assert.equal(new URL(url).origin,base)
+    assert.equal(options.headers['x-rgai-supabase-jwt'],USER_TOKEN)
+    assert.equal(options.headers.Authorization,undefined)
+    assert.equal(options.credentials,'omit')
+    assert.equal(options.redirect,'error')
+    assert.equal(options.cache,'no-store')
+  }
+  assert.equal(calls.filter(x=>x.options.method==='POST').length,5)
+  assert.equal(calls.filter(x=>x.options.method==='PATCH').length,1)
+})
+
+test('same-origin browser JWT transport composes with actual Node dispatch and preserves original API contract', async () => {
+  const seen=[]
+  const gate=(kind)=>async(method,path,auth,body)=>{
+    seen.push({kind,method,path,auth,body})
+    return {status:200,jsonBody:{kind,status:'DRAFT'},headers:{}}
+  }
+  const dispatch=createSecureHttpDispatcher({
+    readGateway:gate('read'),campaignGateway:gate('campaign'),
+    posterGateway:gate('poster'),reelGateway:gate('reel'),
+    writesEnabled:true,renderWritesEnabled:true,allowedOrigin:base,
+  })
+  const api=make({fetchImpl:async(url,opts)=>{
+    const request={
+      url,method:opts.method,text:async()=>opts.body || '',
+      headers:new Headers({...opts.headers,
+        origin:base,'sec-fetch-site':'same-origin'}),
+    }
+    const reply=await dispatch(request)
+    return {status:reply.status,ok:reply.status>=200&&reply.status<300,
+      json:async()=>reply.jsonBody}
+  }})
+  await api.getCampaign(SHOP)
+  await api.createCampaign({brief:'test'})
+  await api.createPosterRender(DAY)
+  await api.createRender(SHOP,DAY)
+  assert.deepEqual(seen.map(x=>x.kind),['read','campaign','poster','reel'])
+  assert.deepEqual(seen.map(x=>x.auth),Array(4).fill('Bearer '+USER_TOKEN))
+  assert.equal(seen[3].body.preset,'instagram_reel_30s')
+  assert.equal(seen[3].body.day_id,DAY)
+})
+
+test('invalid or absent preview JWT is rejected before any network call', async () => {
+  let calls=0
+  for (const token of ['', 'short', 'spaces are rejected',
+    'a'.repeat(8193),'valid,bad','valid\nother']) {
+    const api=make({tokenProvider:async()=>token,fetchImpl:async()=>{calls++;return null}})
+    await assert.rejects(()=>api.getCampaign(SHOP),/sign in again/)
+  }
+  assert.equal(calls,0)
+})
+
+test('preview 503 read retries remain bounded, never mask error with Python RLS fallback', async () => {
+  let calls=0
+  const api=make({
+    supabaseOrigin:'https://jeearzffnjbvghwjjjrf.supabase.co',
+    supabasePublishableKey:'sb_publishable_safe_public_example',
+    fetchImpl:async()=>{
+      calls++
+      return {status:503,ok:false,json:async()=>({error:'SERVICE_UNAVAILABLE'})}
+    },
+  })
+  await assert.rejects(()=>api.getRenderJob(DAY),e=>e.status===503)
+  assert.equal(calls,2)
+  await assert.rejects(()=>api.getDownload(DAY),e=>e.status===503)
+  assert.equal(calls,4)
+})
+
+test('ambiguous preview POST/PATCH must not replay or fail over to legacy Python', async () => {
+  const requested=[]
+  const api=make({fetchImpl:async(url,opts)=>{
+    requested.push({url,method:opts.method})
+    return {status:503,ok:false,json:async()=>({error:'SERVICE_UNAVAILABLE'})}
+  }})
+  await assert.rejects(()=>api.createCampaign({brief:'test'}),e=>e.status===503)
+  await assert.rejects(()=>api.createRender(SHOP,DAY),e=>e.status===503)
+  await assert.rejects(()=>api.saveDay(SHOP,DAY,{topic:'t',linkedin:{},instagram:{}}),
+    e=>e.status===503)
+  assert.equal(requested.length,3)
+  assert.deepEqual(requested.map(x=>x.method),['POST','POST','PATCH'])
+  assert.ok(requested.every(x=>x.url.startsWith(base+'/api/')))
+})
+
+test('default customer transport is untouched and preview flag is source-only',async()=>{
+  const calls=[]
+  const api=createCampaignApi({baseUrl:'https://rgai-dev-functions-d4e5ddbd.azurewebsites.net',
+    tokenProvider:async()=>USER_TOKEN,fetchImpl:async(url,options)=>{
+      calls.push({url,options})
+      return {ok:true,status:200,json:async()=>({ok:true})}
+    }})
+  await api.getCampaign(SHOP)
+  assert.equal(calls[0].options.headers.Authorization,'Bearer '+USER_TOKEN)
+  assert.equal(calls[0].options.credentials,undefined)
+  assert.equal(calls[0].options.headers['x-rgai-supabase-jwt'],undefined)
+  const ui=readFileSync(new URL('../../frontend/src/features/campaigns/CampaignDashboard.jsx',import.meta.url),'utf8')
+  const env=readFileSync(new URL('../../frontend/.env.production',import.meta.url),'utf8')
+  assert.match(ui,/VITE_P0249_NODE_TRANSPORT_ENABLED === 'true'/)
+  assert.doesNotMatch(env,/VITE_P0249_NODE_TRANSPORT_ENABLED\s*=\s*true/)
+  assert.match(env,/VITE_CAMPAIGN_API_BASE_URL=https:\/\/rgai-dev-functions-d4e5ddbd[.]azurewebsites[.]net/)
+})
~~~~

## PR #676 — HEAD ad112c4ee4d552e5dea374f2f7014d1055ac4458
https://github.com/saifsiddiqui59/RetailGrowthAI/pull/676/files

### docs/DECISIONS.md
~~~~diff
@@ -992,3 +992,6 @@
 ## 2026-10-29 — Shared dependency DAG / dispatcher decision
 - GitHub is authoritative for cross-feature handoff state across chat limits; source-only fixtures, integrated contract and commercial release are separate typed nodes. PR merged state is retrieved from GitHub, and human approvals require explicitly reviewed registry proof. A pending production input must not block unrelated fixture or CPU development.
 - The first implementation limits automation to GitHub dependency evaluation, report output and **up to three ready issues per trusted-main run**, hourly or manual; it does not execute an LLM coding agent, merge feature PRs, make cloud schema changes, deploy, consume queues, spend on GPU or touch WineShopPOS. PR validation is read-only. Owner/coordinator must reconcile actual backlogs and protect cost/security before attaching executor.
+
+## 2026-10-29 — #249 create both disposable Auth users before any ROOT wait
+- Never insert directly into Supabase `auth.users`, pregrant shop memberships/ROOT, log test credentials, or keep permanent test users to work around failed onboarding. The canonical protected DEV GoTrue admin-user canary must append each newly returned user ID to its exact cleanup ledger before requesting a user token. Stage BOTH unique `example.invalid` test Auth identities before entering a single short polled approval window, ensuring an authenticated ROOT operator can review both in the same pending list. Require both independent signed user-JWT `retail_onboarding_status` values `APPROVED`, regardless of approval order, before writing either isolated shop through the real RLS-backed endpoint. Any unexpected status, no approval, partially failed second Auth operation or uncertain state aborts to exact own-fixture cleanup. Synthetic CI tests are never a hosted acceptance.
~~~~

### docs/NEXT_TASK.md
~~~~diff
@@ -1318,3 +1318,7 @@ Detailed handoff: `docs/feature3/PRE_GPU_READINESS_20261028.md`. No WineShopPOS
 1. Review source-only dependency registry, fail-closed DAG validator and GitHub Issues dispatch PR. Require four existing CI jobs plus coordinator offline test; coordinator alone merges to latest main and verifies fresh main CI.
 2. After merge, manually dispatch new coordinator GitHub Actions workflow once to confirm live PR evidence and generated status artifact; ensure the first three ready issues are idempotent on a second run. Do not treat issue creation as autonomous coding.
 3. Map Feature2's **actual** 38 numbered assignments and other verified feature task ledgers into registry incrementally without inventing tasks; connect real PR/acceptance evidence, production approvals and owner handoffs. Attach separately approved coding-agent executor only after budget/security review; keep GPU OFF and PROD untouched.
+
+## 2026-10-29 — #249 two-shop owner acceptance next steps / exact dependencies
+- Verify branch `fix/p0249-parallel-owner-onboarding-20261029` PR 4/4 exact-head CI; coordinator only merges and checks fresh main CI, in dependency order with separate #639 ROOT Playwright operator PR and #668 browser Node transport PR. Stage both signed disposable `rgai-canary-<marker>-[ab]@example.invalid` accounts *concurrently* through protected owner-approved DEV workflow; run exact signed ROOT pending queue approvals, then have user-issued JWTs create and prove two different OWNER shops. Delete only exact canary Auth/shops/objects in `finally`; verify cleanup even on timeout/failure. No service-role key in browser or repo.
+- **DEP-249-TEST-ACCOUNTS** (owner: #249 DEV test operator; output: explicit protected `workflow_dispatch`, working GoTrue admin/secret via environment, two unique temporary Auth sessions and pending rows; acceptance: both signed account UUIDs created once, no test grants/bypass, finally cleanup PASS). **DEP-249-ROOT-APPROVAL** (owner: Feature #1 ROOT operator; output: owner-authenticated approvals for both pending users; acceptance: both exact UUID decisions validated before shops). **DEP-249-BROWSER-EGRESS** (owner: DEV operator/network; output: accessible browser/Playwright to actual DEV app; acceptance: actual signed JWT session; local runner had blocked navigation). Continue offline Node route/tenant/rights tests independent of live Feature3/4 media; never call synthetic samples real model output.
~~~~

### docs/PROJECT_STATE.md
~~~~diff
@@ -1334,3 +1334,7 @@ See docs/NEXT_TASK.md. Live integrations and cloud deployment remain blocked by
 
 ## 2026-10-29 — Shared cross-feature dependency coordinator (integration PR)
 - Coordinator source introduced at `coordination/dependencies.json`, `scripts/coordination/resolve_dependencies.py`, `tests/contracts/test_dependency_coordinator.py` and `.github/workflows/retailgrowthai-dependency-coordinator.yml`. Seed tracks only evidenced F2/F3/F4/F5/F7 handoffs (not all Feature2 38 tasks); fixture/integration/production gates are strictly separate. Hourly trusted-main workflow verifies actual PR merges, emits report and creates at most three ready issues. No coding agent automatically executes them; no GPU/DEV/PROD or WineShopPOS changes. See `docs/DEPENDENCY_COORDINATOR.md`; PR CI and integration to main must be independently verified.
+
+## 2026-10-29 — Issue #249 staged two-owner DEV test harness (source only)
+- Connected read-only to DEV Supabase `jeearzffnjbvghwjjjrf` (ACTIVE_HEALTHY). Exact canary-pattern inventory was 0 temporary `rgai-canary-*` Auth users and 0 named shops before work; no live accounts were created. The GoTrue Auth admin API is available only through the protected owner-dispatched workflow, not through current SQL-only Supabase connector. Refused unsupported direct `auth.users` inserts/ROOT bypass.
+- Existing owner-authorized workflow `.github/workflows/retail-dev-test-accounts-canary-once.yml` already uses fresh random passwords, two nonce-bound disposable email identities, normal ROOT onboarding, scoped cleanup and no WineShopPOS. On Issue #249 branch `fix/p0249-parallel-owner-onboarding-20261029`, fixed its serialized test-account creation: both GoTrue users are staged first, checked with real user-issued password tokens, polled for BOTH genuine ROOT decisions in a *single* bounded window, and only after both approved are isolated OWNER shops created with user-JWT RLS. Exact cleanup ledger includes each user immediately on creation, including partial second Auth token failures. No backend grants, root impersonation, production changes or paid Azure resources. New offline regression tests. Four-job CI pending.
~~~~

### docs/WORK_LOG.md
~~~~diff
@@ -752,3 +752,5 @@ Use scripts/checkpoint.sh after completing a task.
 ## 2026-10-29 — Coordinator dependency registry + workflow implementation
 - Added auditable seed of F2/F3/F4/F5/F7 handoffs with independently verifiable PR merge gates and manual human approvals. Added cycle/unknown ID/unsafe approval validation, readiness resolver, fail-closed GitHub reads, bounded/idempotent ready-issue creation, scheduled/manual GitHub Actions, report artifacts, negative tests and runbook.
 - This is source proposed via coordinator PR, not proof that new Actions is active on main or that coding continues without a configured executor. Exact-head CI/main integration remain required. No paid GPU, cloud deployments, PROD or WineShopPOS modifications.
+
+- 2026-10-29 — Continued open Azure #249 after reading mandatory AGENTS/project docs, current main/PR #639/#668 and existing protected account workflow. Connected RetailGrowthAI DEV Supabase read-only: ACTIVE_HEALTHY, 0 `rgai-canary-*` Auth users/shops, existing secure ROOT onboarding and reel RPCs. Identified the existing canary's sequential A-approval-before-B-creation as an operator timing bottleneck. On separate `fix/p0249-parallel-owner-onboarding-20261029`, staged both short-lived synthetic GoTrue users first, required two real ROOT decisions within one bounded window before any OWNER shop creation and preserved per-user exact cleanup on partial failures. Added offline tests for staging/rollback, reversed real decision order, no shortcuts/denials/timeouts and original early Azure gate preflight. No live test Auth users created, no password leaked, no ROOT mutation, migration, GPU/PROD or WineShopPOS changed. Actual protected owner workflow dispatch and ROOT browser approval remain separately gated; CI to verify.
~~~~

### tests/e2e/retail_dev_canary_once.py
~~~~diff
@@ -405,6 +405,84 @@ def preflight_dev_http_auth_routes(*, transport=None, clock=None, include_prompt
 
 
 
+
+def stage_two_root_gated_accounts(*, marker, admins, pub, accounts, send=None,
+                                  password_factory=None):
+    """Stage BOTH fresh GoTrue users, not shops, before operator ROOT approval.
+
+    The caller's mutable accounts ledger is updated immediately after every
+    successful Auth create so the existing finally block deletes partial
+    fixtures even if password sign-in or the second create fails. This helper
+    grants no shop, role or approval and never prints credentials.
+    """
+    if accounts or not isinstance(marker, str) or len(marker) != 12 or any(
+            ch not in "0123456789abcdef" for ch in marker):
+        raise RuntimeError("Invalid or reused DEV canary account ledger")
+    send = send or call
+    password_factory = password_factory or (lambda: secrets.token_urlsafe(30))
+    first_password = None
+    for label in ("a", "b"):
+        email = "rgai-canary-" + marker + "-" + label + "@example.invalid"
+        password = password_factory()
+        if not isinstance(password, str) or len(password) < 30:
+            raise RuntimeError("DEV canary password generator invalid")
+        _, item = send(SUPABASE + "/auth/v1/admin/users", method="POST",
+                       payload={"email": email, "password": password,
+                                "email_confirm": True},
+                       headers=admins, expect=(200, 201))
+        uid = item["id"]
+        if not isinstance(uid, str) or str(uuid.UUID(uid)) != uid:
+            raise RuntimeError("Invalid temporary Auth identity from GoTrue")
+        accounts.append(uid)  # cleanup ledger BEFORE first user-token request
+        _, auth = send(SUPABASE + "/auth/v1/token?grant_type=password",
+                       method="POST", payload={"email": email, "password": password},
+                       headers={"apikey": pub}, expect=(200,))
+        token = auth["access_token"]
+        if not isinstance(token, str) or not token:
+            raise RuntimeError("Missing verified disposable Auth session")
+        accounts[-1] = (uid, {"apikey": pub, "Authorization": "Bearer " + token})
+        if label == "a":
+            first_password = password
+    print("CANARY_TWO_DISPOSABLE_AUTH_USERS_STAGED=true", flush=True)
+    return first_password
+
+
+def wait_for_both_root_approvals(accounts, *, send=None, sleep=None, attempts=75):
+    """No shop is provisioned until BOTH unique users are ROOT approved.
+
+    Poll within a SINGLE bounded approval window for A and B; the human ROOT
+    operator may approve them in either order. A denied/unknown status fails
+    closed; no direct SQL, fake user JWT or test-only approval shortcut.
+    """
+    if len(accounts) != 2 or any(
+            not isinstance(item, tuple) or len(item) != 2
+            for item in accounts):
+        raise RuntimeError("Exactly two real signed-in test users required")
+    send = send or call
+    sleep = sleep or time.sleep
+    if not isinstance(attempts, int) or attempts < 1 or attempts > 75:
+        raise RuntimeError("Invalid bounded ROOT approval poll")
+    for round_number in range(attempts):
+        statuses = []
+        for _uid, bearer in accounts:
+            _, state = send(SUPABASE + "/rest/v1/rpc/retail_onboarding_status",
+                            method="POST", payload={}, headers=bearer,
+                            expect=(200,))
+            status = state.get("status") if isinstance(state, dict) else None
+            if status not in ("APPROVED", "PENDING"):
+                raise RuntimeError("Temporary retailer onboarding was rejected")
+            statuses.append(status)
+        if statuses == ["APPROVED", "APPROVED"]:
+            print("CANARY_BOTH_OPERATOR_APPROVALS_VERIFIED=true", flush=True)
+            return
+        if round_number == 0:
+            print("CANARY_WAITING_FOR_TWO_EXPLICIT_DEV_OPERATOR_APPROVALS=true",
+                  flush=True)
+        if round_number + 1 < attempts:
+            sleep(4)
+    raise RuntimeError("Both DEV test fixtures were not approved by authorized ROOT")
+
+
 def main():
     if os.getenv("RGAI_DEV_CANARY_APPROVAL")!="AUTHORIZED_RETAILGROWTHAI_DEV_ONLY":
         raise RuntimeError("No explicit RetailGrowthAI DEV authorization")
@@ -433,38 +511,16 @@ def main():
     paths=[]
     status="NOT_STARTED"
     try:
-        account_password_a = None
-        for label in ("a","b"):
-            email="rgai-canary-"+marker+"-"+label+"@example.invalid"
-            password=secrets.token_urlsafe(30)
-            if label == "a":
-                account_password_a = password
-            _,item=call(SUPABASE+"/auth/v1/admin/users",method="POST",
-                payload={"email":email,"password":password,"email_confirm":True},
-                headers=admins,expect=(200,201))
-            uid=item["id"]
-            accounts.append(uid)
-            _,auth=call(SUPABASE+"/auth/v1/token?grant_type=password",
-                method="POST",payload={"email":email,"password":password},
-                headers={"apikey":pub},expect=(200,))
-            bearer={"apikey":pub,"Authorization":"Bearer "+auth["access_token"]}
-            # RetailGrowthAI requires SaaS ROOT approval before a retailer may
-            # create a shop. The connected DEV operator explicitly approves
-            # ONLY the two newly created example.invalid canary requests.
-            # No test-only auth bypass, privileged browser secret or gate flip.
-            for approval_attempt in range(75):
-                _,onboarding=call(SUPABASE+"/rest/v1/rpc/retail_onboarding_status",
-                    method="POST",payload={},headers=bearer,expect=(200,))
-                if onboarding.get("status")=="APPROVED":
-                    print("CANARY_OPERATOR_APPROVAL_VERIFIED=true",flush=True)
-                    break
-                if onboarding.get("status")!="PENDING":
-                    raise RuntimeError("Temporary retailer onboarding was rejected")
-                if approval_attempt==0:
-                    print("CANARY_WAITING_FOR_EXPLICIT_DEV_OPERATOR_APPROVAL=true",flush=True)
-                time.sleep(4)
-            else:
-                raise RuntimeError("DEV test fixture was not approved by authorized operator")
+        # Expose BOTH test-owned pending Auth accounts to the signed ROOT
+        # queue concurrently. Previously B did not exist until A approval,
+        # doubling operator wait and hiding B from one queue refresh.
+        account_password_a = stage_two_root_gated_accounts(
+            marker=marker, admins=admins, pub=pub, accounts=accounts)
+        wait_for_both_root_approvals(accounts)
+        # Only real ROOT approval authorizes each ordinary caller-JWT shop
+        # creation, as in the prior test; never write owner role directly.
+        for index, (uid, bearer) in enumerate(accounts):
+            label = ("a", "b")[index]
             sid=str(uuid.uuid4())
             # Register for cleanup BEFORE attempting an insert: a partial
             # commit/network failure must not leave an untracked test shop.
@@ -478,7 +534,6 @@ def main():
                 headers=bearer,expect=(200,))
             if not isinstance(shoprows,list) or len(shoprows)!=1 or shoprows[0].get("id")!=sid:
                 raise RuntimeError("RLS failed to reveal newly bootstrapped OWNER shop")
-            accounts[-1]=(uid,bearer)
         a=accounts[0][1];b=accounts[1][1]
         if prompt_only:
             from feature2_dev_live_canary import run_live_feature2_prompt
~~~~

### tests/e2e/test_dev_canary_gateway_preflight.py
~~~~diff
@@ -65,6 +65,11 @@ def test_preflight_latency_over_budget_fails_closed():
 def test_real_main_runs_gateway_probe_before_deleting_or_creating_test_users():
     src=SOURCE.read_text()
     main=src.split("\ndef main():\n",1)[1]
+    # Auth admin POST lives in the stage helper; main still performs the
+    # real HTTP preflight BEFORE calling the helper and creating any user.
     assert main.index("preflight_dev_http_auth_routes(include_prompt=prompt_only)") < main.index(
-        '"/auth/v1/admin/users"')
+        "account_password_a = stage_two_root_gated_accounts(")
+    assert '"/auth/v1/admin/users"' in src
+    assert main.index("wait_for_both_root_approvals(accounts)") < main.index(
+        'call(SUPABASE+"/rest/v1/shops",')
     assert "CANARY_DEV_GATEWAY_AUTH_PREFLIGHT_PASSED=true" in src
~~~~

### tests/e2e/test_p0249_parallel_owner_onboarding.py
~~~~diff
@@ -0,0 +1,138 @@
+"""Offline regressions for the ROOT-gated two temporary DEV shop-owner canary.
+
+No live Supabase, Auth, emails, private media, or ROOT decision is executed.
+Fixtures are intentionally distinct from production and real users.
+"""
+import importlib.util
+from pathlib import Path
+
+import pytest
+
+
+SOURCE = Path(__file__).with_name("retail_dev_canary_once.py")
+SPEC = importlib.util.spec_from_file_location("retail_dev_canary_once", SOURCE)
+canary = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(canary)
+MARKER = "012345abcdef"
+UIDS = [
+    "11111111-1111-4111-8111-111111111111",
+    "22222222-2222-4222-8222-222222222222",
+]
+EMAILS = [f"rgai-canary-{MARKER}-{x}@example.invalid" for x in "ab"]
+
+
+def test_both_auth_users_are_staged_with_no_owner_role_or_shop_grant(capsys):
+    operations = []
+    accounts = []
+    def send(url, *, method, payload, headers, expect):
+        assert method == "POST"
+        operations.append((url, payload.copy()))
+        if url.endswith("/auth/v1/admin/users"):
+            assert payload == {"email": EMAILS[len(operations)//2],
+                               "password": "synthetic-fixture-password-is-long-enough",
+                               "email_confirm": True}
+            assert headers == {"test": "service-in-memory"}
+            return 201, {"id": UIDS[len(operations)//2]}
+        assert url.endswith("/auth/v1/token?grant_type=password")
+        assert payload["email"] in EMAILS
+        return 200, {"access_token": "synthetic-local-jwt-fixture"}
+    first = canary.stage_two_root_gated_accounts(
+        marker=MARKER, admins={"test": "service-in-memory"},
+        pub="fake-local-publishable", accounts=accounts, send=send,
+        password_factory=lambda: "synthetic-fixture-password-is-long-enough")
+    assert first == "synthetic-fixture-password-is-long-enough"
+    assert [x[0] for x in accounts] == UIDS
+    assert [x[1]["Authorization"] for x in accounts] == ["Bearer synthetic-local-jwt-fixture"] * 2
+    assert [x[0].split("/")[-1] for x in operations] == ["users", "token?grant_type=password",
+                                                           "users", "token?grant_type=password"]
+    assert all("/shops" not in url and "review_onboarding" not in url
+               for url, _payload in operations)
+    assert "CANARY_TWO_DISPOSABLE_AUTH_USERS_STAGED=true" in capsys.readouterr().out
+    assert not any("service_role" in str(payload) for _,payload in operations)
+
+
+def test_partial_second_auth_failure_keeps_both_ids_for_exact_cleanup():
+    accounts = []
+    created = 0
+    def send(url, *, method, payload, headers, expect):
+        nonlocal created
+        if url.endswith("/admin/users"):
+            created += 1
+            return 201, {"id": UIDS[created - 1]}
+        if payload["email"] == EMAILS[1]:
+            raise RuntimeError("synthetic auth token error, no session")
+        return 200, {"access_token": "fake-access"}
+    with pytest.raises(RuntimeError, match="synthetic auth token error"):
+        canary.stage_two_root_gated_accounts(
+            marker=MARKER, admins={}, pub="fixture", accounts=accounts, send=send,
+            password_factory=lambda: "synthetic-fixture-password-is-long-enough")
+    assert accounts[0][0] == UIDS[0]
+    assert accounts[1] == UIDS[1]  # cleanup still knows user B without a JWT
+
+
+def test_both_pending_are_visible_in_same_round_and_approvable_in_reverse_order(capsys):
+    accounts = [(uid, {"Authorization": "Bearer " + uid}) for uid in UIDS]
+    polls = [[], []]
+    waits = []
+    responses = iter([
+        "PENDING", "PENDING",
+        "PENDING", "APPROVED",  # B approved first
+        "APPROVED", "APPROVED",
+    ])
+    def send(url, *, method, payload, headers, expect):
+        assert url.endswith("/rest/v1/rpc/retail_onboarding_status")
+        assert method == "POST" and payload == {}
+        index = UIDS.index(headers["Authorization"][7:])
+        polls[index].append(headers["Authorization"])
+        return 200, {"status": next(responses)}
+    canary.wait_for_both_root_approvals(accounts, send=send,
+                                        sleep=lambda seconds: waits.append(seconds),
+                                        attempts=3)
+    assert [len(x) for x in polls] == [3, 3]
+    assert waits == [4, 4]
+    log = capsys.readouterr().out
+    assert "CANARY_WAITING_FOR_TWO_EXPLICIT_DEV_OPERATOR_APPROVALS=true" in log
+    assert "CANARY_BOTH_OPERATOR_APPROVALS_VERIFIED=true" in log
+    assert not any("Bearer " in line for line in log.splitlines())
+
+
+@pytest.mark.parametrize("unexpected", ["REJECTED", "UNKNOWN", None, "", True])
+def test_unknown_or_rejected_status_denies_shop_creation(unexpected):
+    accounts = [(uid, {"Authorization": "Bearer synthetic"}) for uid in UIDS]
+    queries = []
+    def send(url, **kwargs):
+        queries.append(url)
+        return 200, {"status": unexpected}
+    with pytest.raises(RuntimeError, match="onboarding was rejected"):
+        canary.wait_for_both_root_approvals(accounts, send=send, sleep=lambda s: None,
+                                             attempts=3)
+    assert len(queries) == 1
+    assert all("/shops" not in url for url in queries)
+
+
+def test_approval_timeout_is_one_bounded_window_not_two_sequential_waits():
+    accounts = [(uid, {"Authorization": "Bearer synthetic"}) for uid in UIDS]
+    count = 0
+    def send(url, **kwargs):
+        nonlocal count
+        count += 1
+        return 200, {"status": "PENDING"}
+    with pytest.raises(RuntimeError, match="Both DEV test fixtures were not approved"):
+        canary.wait_for_both_root_approvals(accounts, send=send,
+                                             sleep=lambda _seconds: None, attempts=4)
+    assert count == 8  # 2 statuses per round; no 2x serialized 5-minute wait
+
+
+def test_main_preserves_gateway_preflight_and_keeps_shops_after_both_root_approvals():
+    source = SOURCE.read_text(encoding="utf-8")
+    main = source.split("\ndef main():\n", 1)[1]
+    preflight = main.index("preflight_dev_http_auth_routes(include_prompt=prompt_only)")
+    staged = main.index("account_password_a = stage_two_root_gated_accounts(")
+    approved = main.index("wait_for_both_root_approvals(accounts)")
+    shop = main.index('call(SUPABASE+"/rest/v1/shops",')
+    assert preflight < staged < approved < shop
+    assert main.index("shops.append(sid)", approved) < shop
+    assert "finally:" in main and '"/auth/v1/admin/users/"+uid' in main
+    assert "CANARY_TWO_DISPOSABLE_AUTH_USERS_STAGED=true" in source
+    assert "CANARY_BOTH_OPERATOR_APPROVALS_VERIFIED=true" in source
+    assert "service_role" not in source.split("\ndef main():\n")[0].lower()
~~~~

### tests/infra/test_p0249_node_full_canary_source.py
~~~~diff
@@ -28,7 +28,11 @@ def test_manual_root_approval_and_exact_node_target(self):
         self.assertNotIn('sb_secret_',src)
         self.assertNotIn('https://wineshop',src.lower())
         # Original canary unchanged and still demands real ROOT approval.
-        self.assertIn('CANARY_WAITING_FOR_EXPLICIT_DEV_OPERATOR_APPROVAL=true',original)
+        self.assertIn('CANARY_WAITING_FOR_TWO_EXPLICIT_DEV_OPERATOR_APPROVALS=true',original)
+        self.assertIn('CANARY_BOTH_OPERATOR_APPROVALS_VERIFIED=true',original)
+        self.assertLess(
+            original.index('wait_for_both_root_approvals(accounts)'),
+            original.index('call(SUPABASE+"/rest/v1/shops",'))
         self.assertIn('preflight_dev_http_auth_routes(',original)
         self.assertIn('CANARY_PRIVATE_30S_H264_AAC_MP4_VERIFIED=true',original)
         self.assertIn('CANARY_POSTER_ONLY_LIVE_ACCEPTANCE=PASSED',original)
~~~~

## PR #679 — HEAD 39b943e28c1f74cdd96b0a0f1c09867b9892319b
https://github.com/saifsiddiqui59/RetailGrowthAI/pull/679/files

### docs/part1/P0_249_NODE_FULL_E2E_RUNBOOK.md
~~~~diff
@@ -22,3 +22,17 @@ Before Auth creation, five anonymous Node routes must return real application 40
 Existing signed-in read #40354972715, applied caller-authorized Reel RPC and actual Free SWA write-route negative #40380525626 do not prove successful positive two-shop work. The separate real-JWT no-shop negative canary must also pass before full E2E. Owner/VIEWER/foreign and stale/revoked JWT denial, uncertainty reconciliation, real storage rights, quota/outbox idempotency, cloud MP4 and after-idle reliability must be evidenced in completed Actions logs.
 
 Until those gates pass, keep issue #249 OPEN, leave production frontend on Python Flex, do not provision paid Free-SWA upgrades, GPU/always-ready, PROD or WineShopPOS resources.
+
+
+## 2026-10-29 — protected Node canary transport hardening (source PR)
+
+For the **manual, owner-approved** Node canary only, the Python bridge now converts exactly one well-shaped original Supabase user Bearer JWT into the secure Node `x-rgai-supabase-jwt` header. It drops `apikey` regardless of casing and **rejects** forged caller-supplied Node JWT, Cookie/Origin/Host/Forwarded or proxy/Functions/principal headers, duplicate Bearer/header identities, control-character injection and missing/invalid Bearer before calling the Node preview. Only Accept, Content-Type and Prefer may otherwise be forwarded. This syntactic check does not validate JWT authenticity: Node JWKS verification, current Supabase RLS, tenant rights and operator ROOT approval remain mandatory. Direct Supabase Auth/admin cleanup calls are not redirected to Node.
+
+Offline test: `tests/infra/test_p0249_node_header_fence.py` extracts the pure helper AST without importing live canary configuration, then exercises valid user header forwarding and negative spoofing/credential-leak paths. Real DEV tests must use genuine disposable approved user JWTs; never put credentials or raw JWTs in source/CI output.
+
+**Unchanged blockers:** PR #639 ROOT UI exact-ACK integration, #668 OFF-by-default same-origin SPA transport, #676 staged two-account ROOT approval, explicit protected workflow dispatch by owner, media/FFmpeg signed E2E and independent Azure #249 original unmarked ~61-second 503 internal cause. Require exact-head 4/4 CI, coordinator merge, independently verified main CI and real signed live acceptance before claiming any #249 resolution. No PROD or WineShopPOS writes, Azure config changes, paid GPU, or user-facing API cutover.
+
+### Additional Node-preview no-redirect fence
+The canary no longer passes preview calls through the parent `urllib.request.urlopen` automatic redirect handler: its isolated Node-only opener returns an HTTP 30x as a fatal `P0249_NODE_REDIRECT_DENIED`, so even a misconfigured/compromised preview cannot redirect the custom user JWT to a foreign host. Read-only GET may retry bounded transient errors; POST/PATCH is single-attempt and an uncertain 502/503/504/timeout is fatal. Supabase Auth/RLS/admin/cleanup requests keep the existing original transport. This is tested with mock HTTP, **not** live signed acceptance or Azure causality.
+
+The same no-redirect opener also applies to **anonymous initial Node health/401 preflight**, not just signed calls. An untrusted 302/307 cannot spoof secure route readiness by redirecting an unauthenticated request to a different host before protected test-user creation. Offline AST/mock preflight tests exercise the exact health and five route checks; genuine hosted verification still requires owner-controlled canary and ROOT approval.
~~~~

### tests/e2e/p0249_dev_node_full_canary_once.py
~~~~diff
@@ -8,7 +8,9 @@
 """
 from __future__ import annotations
 
+import json
 import os
+import re
 import time
 import urllib.error
 import urllib.request
@@ -35,15 +37,15 @@ def check(path, method="GET"):
         )
         started = time.monotonic()
         try:
-            with urllib.request.urlopen(req,timeout=12) as response:
+            with _NODE_OPENER.open(req,timeout=12) as response:
                 code,headers = response.status,response.headers
         except urllib.error.HTTPError as response:
             code,headers = response.code,response.headers
         if (code != 401 or headers.get("X-RGAI-Secure-Adapter") != "candidate-v1"
                 or time.monotonic()-started > 12):
             raise RuntimeError("P0249_NODE_PREVIEW_NOT_AUTHENTICATED_OR_HEALTHY")
     health=urllib.request.Request(NODE_PREVIEW+"/api/p0-secure-health",method="GET")
-    with urllib.request.urlopen(health,timeout=12) as response:
+    with _NODE_OPENER.open(health,timeout=12) as response:
         if (response.status != 200 or response.headers.get("X-P0249-Secure-Preview")
                 != "real-jwks-rls-dev-write-v1"):
             raise RuntimeError("P0249_WRONG_NODE_DEV_PREVIEW")
@@ -58,6 +60,110 @@ def check(path, method="GET"):
     print("P0249_REAL_NODE_WRITE_API_PREFLIGHT_PASSED=true",flush=True)
 
 
+
+def node_preview_headers(headers):
+    """Only a real user JWT may cross into the isolated Node candidate.
+
+    Never forward Supabase apikey, service credentials, cookies, arbitrary
+    caller-supplied Node JWT, proxy identity or browser-origin overrides.
+    The Node dispatcher independently verifies signature, expiry and RLS.
+    """
+    if not isinstance(headers, dict):
+        raise RuntimeError("P0249_INVALID_NODE_HEADER_SET")
+    forwarded = {}
+    token = None
+    for raw_name, value in headers.items():
+        if (not isinstance(raw_name, str) or not isinstance(value, str)
+                or not raw_name or "\r" in raw_name or "\n" in raw_name
+                or "\r" in value or "\n" in value):
+            raise RuntimeError("P0249_INVALID_NODE_HEADER")
+        name = raw_name.lower()
+        if name == "apikey":
+            # Supabase browser publishable key is irrelevant to Node. Never
+            # forward any value, including a mistakenly supplied service key.
+            continue
+        if name == "authorization":
+            if token is not None or not value.startswith("Bearer "):
+                raise RuntimeError("P0249_INVALID_NODE_USER_BEARER")
+            candidate = value[7:]
+            segments = candidate.split(".")
+            if (len(candidate) > 8192 or len(segments) != 3
+                    or not all(re.fullmatch(r"[A-Za-z0-9_-]+", p) for p in segments)):
+                raise RuntimeError("P0249_INVALID_NODE_USER_BEARER")
+            token = candidate
+            continue
+        if name not in {"accept", "content-type", "prefer"}:
+            # Includes a prefilled x-rgai-supabase-jwt, cookies, Origin,
+            # X-Forwarded-*, keys, and any unexpected impersonation header.
+            raise RuntimeError("P0249_UNREVIEWED_NODE_HEADER")
+        if name in forwarded:
+            raise RuntimeError("P0249_DUPLICATE_NODE_HEADER")
+        forwarded[name] = value
+    if token is None:
+        raise RuntimeError("P0249_MISSING_NODE_USER_BEARER")
+    forwarded["x-rgai-supabase-jwt"] = token
+    return forwarded
+
+
+
+class _NodeNeverRedirect(urllib.request.HTTPRedirectHandler):
+    """No custom JWT can follow a 30x away from the pinned preview origin."""
+    def redirect_request(self, req, fp, code, msg, headers, newurl):
+        return None
+
+
+_NODE_OPENER = urllib.request.build_opener(_NodeNeverRedirect())
+
+
+def _call_node_preview(url, *, method, payload, headers, timeout, expect):
+    """Bounded Node-only HTTP transport; no redirect or uncertain write retry.
+
+    The original Supabase client remains untouched. The preview receives
+    only node_preview_headers output; this helper never accepts arbitrary hosts.
+    """
+    if not url.startswith(NODE_PREVIEW + "/api/") or method not in ("GET", "POST", "PATCH"):
+        raise RuntimeError("P0249_INVALID_NODE_REQUEST_TARGET")
+    if payload is not None and isinstance(payload, (bytes, bytearray)):
+        raise RuntimeError("P0249_NODE_BINARY_WRITE_UNSUPPORTED")
+    data = json.dumps(payload).encode("utf-8") if payload is not None else None
+    safe_headers = dict(headers)
+    if data is not None:
+        safe_headers.setdefault("content-type", "application/json")
+    request = urllib.request.Request(url, data=data, method=method, headers=safe_headers)
+    status, body = None, b""
+    for attempt in range(3 if method == "GET" else 1):
+        try:
+            with _NODE_OPENER.open(request, timeout=(65 if method == "GET" else timeout)) as response:
+                status, body = response.status, response.read(1_000_001)
+            if len(body) > 1_000_000:
+                raise RuntimeError("P0249_NODE_RESPONSE_TOO_LARGE")
+            break
+        except urllib.error.HTTPError as response:
+            status, body = response.code, response.read(4097)
+            if 300 <= status <= 399:
+                raise RuntimeError("P0249_NODE_REDIRECT_DENIED") from None
+            if method == "GET" and status in (502, 503, 504) and attempt < 2:
+                time.sleep(4 * (attempt + 1))
+                continue
+            break
+        except (TimeoutError, ConnectionResetError, OSError):
+            if method == "GET" and attempt < 2:
+                time.sleep(4 * (attempt + 1))
+                continue
+            raise RuntimeError("P0249_REAL_NODE_HTTP_TRANSACTION_UNCONFIRMED") from None
+    if status not in expect:
+        if status in (502, 503, 504):
+            raise RuntimeError("P0249_REAL_NODE_HTTP_TRANSACTION_UNCONFIRMED")
+        # Never surface error bodies, signed IDs, private URL or request JWTs.
+        raise RuntimeError("P0249_NODE_UNEXPECTED_HTTP_STATUS_" + str(status))
+    if not body:
+        return status, None
+    try:
+        return status, json.loads(body)
+    except (ValueError, UnicodeDecodeError):
+        return status, body
+
+
 def main():
     if os.environ.get("RGAI_DEV_CANARY_APPROVAL") != "AUTHORIZED_RETAILGROWTHAI_DEV_ONLY":
         raise RuntimeError("ROOT_APPROVAL_PRECONDITION_MISSING")
@@ -71,26 +177,17 @@ def main():
 
     def node_routed_call(url,method="GET",payload=None,headers=None,timeout=30,
                          expect=(200,201,202,204)):
-        original=dict(headers or {})
         is_node=url.startswith(NODE_PREVIEW+"/api/")
         if is_node:
-            # Only the original access JWT minted by Supabase Auth is forwarded
-            # via the custom SWA header; SWA Authorization/principal is ignored.
-            bearer=original.pop("Authorization",original.pop("authorization",None))
-            original.pop("apikey",None)
-            if bearer is not None:
-                if not isinstance(bearer,str) or not bearer.startswith("Bearer "):
-                    raise RuntimeError("UNTRUSTED_SUPABASE_JWT_TRANSPORT")
-                original["x-rgai-supabase-jwt"]=bearer[7:]
-        try:
-            return previous_call(url,method=method,payload=payload,
-                                 headers=original,timeout=timeout,expect=expect)
-        except (canary.TransientGateway,TimeoutError,ConnectionResetError) as e:
-            if is_node:
-                # NO fallback to direct SQL or blind replay: the assertion is
-                # that the real Node HTTP write, not a backup route, works.
-                raise RuntimeError("P0249_REAL_NODE_HTTP_TRANSACTION_UNCONFIRMED") from None
-            raise
+            # One customer JWT only; reject forged inbound Node identity.
+            original=node_preview_headers(headers or {})
+        else:
+            original=dict(headers or {})
+        if is_node:
+            return _call_node_preview(url, method=method, payload=payload,
+                                      headers=original, timeout=timeout, expect=expect)
+        return previous_call(url,method=method,payload=payload,
+                             headers=original,timeout=timeout,expect=expect)
 
     canary.call=node_routed_call
     canary.preflight_dev_http_auth_routes=node_preflight
~~~~

### tests/infra/test_p0249_node_full_canary_source.py
~~~~diff
@@ -79,12 +79,16 @@ def urlopen(req, *, timeout):
                 request=types.SimpleNamespace(Request=request, urlopen=urlopen),
                 error=types.SimpleNamespace(HTTPError=urllib.error.HTTPError)),
             "NODE_PREVIEW": origin,
+            "_NODE_OPENER": types.SimpleNamespace(open=urlopen),
             "time": time,
         }
         exec(compile(ast.Module(body=[preflight], type_ignores=[]),
                      str(E2E), "exec"), scope)
         scope["node_preflight"](include_prompt=False)
         self.assertEqual(len(calls), 6)  # health + five protected routes
+        self.assertIn("_NODE_OPENER.open", source)
+        self.assertNotIn("urllib.request.urlopen(", source)
+
         with self.assertRaisesRegex(RuntimeError, "PROMPT_MODE_NOT_SUPPORTED"):
             scope["node_preflight"](include_prompt=True)
         # Unsupported mode is rejected BEFORE any network request.
~~~~

### tests/infra/test_p0249_node_header_fence.py
~~~~diff
@@ -0,0 +1,273 @@
+"""Issue #249: untrusted Node canary headers never carry browser/service identity.
+
+Only extract the pure helper AST. Never import the live DEV canary or access
+GitHub Secrets, Supabase, an Azure endpoint, or an operator ROOT session.
+"""
+import ast
+import io
+import json
+import re
+import time
+import urllib.error
+import urllib.request
+import unittest
+from pathlib import Path
+
+TARGET = Path(__file__).resolve().parents[2] / "tests/e2e/p0249_dev_node_full_canary_once.py"
+
+
+def _headers():
+    tree = ast.parse(TARGET.read_text())
+    helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
+                  and n.name == "node_preview_headers")
+    namespace = {"re": re}
+    exec(compile(ast.Module(body=[helper], type_ignores=[]), str(TARGET), "exec"),
+         namespace)
+    return namespace["node_preview_headers"]
+
+
+class NodePreviewHeaderFence(unittest.TestCase):
+    def test_only_one_signed_user_token_forwards_with_safe_headers(self):
+        headers = _headers()({
+            "Authorization": "Bearer eyJhbGciOi.test_-part.signature_123",
+            "apikey": "sb_publishable_example_never_forward",
+            "Accept": "application/json",
+            "Content-Type": "application/json",
+            "Prefer": "return=representation",
+        })
+        self.assertEqual(headers, {
+            "accept": "application/json",
+            "content-type": "application/json",
+            "prefer": "return=representation",
+            "x-rgai-supabase-jwt": "eyJhbGciOi.test_-part.signature_123",
+        })
+        self.assertNotIn("authorization", headers)
+        self.assertNotIn("apikey", headers)
+
+    def test_disallow_all_conflicting_node_or_browser_identity_headers(self):
+        cases = (
+            {"x-rgai-supabase-jwt": "attacker.value.here"},
+            {"X-RGAI-SUPABASE-JWT": "attacker.value.here"},
+            {"Cookie": "session=stolen"},
+            {"Proxy-Authorization": "Bearer proxy"},
+            {"x-functions-key": "internal"},
+            {"X-MS-CLIENT-PRINCIPAL": "fake"},
+            {"Origin": "https://attacker.example"},
+            {"Referer": "https://attacker.example"},
+            {"Host": "attacker.example"},
+            {"X-Forwarded-Host": "attacker.example"},
+            {"Set-Cookie": "a=b"},
+        )
+        for bad in cases:
+            with self.subTest(bad=tuple(bad)):
+                with self.assertRaisesRegex(RuntimeError, "UNREVIEWED_NODE_HEADER"):
+                    _headers()({"Authorization": "Bearer a.b.c", **bad})
+
+    def test_require_one_actual_jwt_shaped_user_bearer(self):
+        cases = (
+            {}, {"Authorization": ""}, {"Authorization": "Basic a.b.c"},
+            {"Authorization": "Bearer "}, {"Authorization": "Bearer sb_secret_example"},
+            {"Authorization": "Bearer a..c"},
+            {"Authorization": "Bearer a.b.c."},
+            {"Authorization": "Bearer a.b.c$"},
+            {"Authorization": "Bearer " + "a" * 8193 + ".b.c"},
+            {"Authorization": "Bearer a.b.c", "authorization": "Bearer d.e.f"},
+        )
+        for bad in cases:
+            with self.subTest(bad_keys=tuple(bad)):
+                with self.assertRaises(RuntimeError):
+                    _headers()(bad)
+
+    def test_header_smuggling_and_case_collisions_fail_closed(self):
+        cases = (
+            {"Authorization": "Bearer a.b.c\r\nCookie: forged"},
+            {"Authorization": "Bearer a.b.c", "Accept": "text/plain\nUnsafe"},
+            {"Authorization": "Bearer a.b.c", "Accept": "application/json",
+             "accept": "text/plain"},
+            {"Authorization": "Bearer a.b.c", "a\r\nb": "x"},
+            {"Authorization": "Bearer a.b.c", "apikey": None},
+            {"Authorization": "Bearer a.b.c", "x-request-id": "unsafe-caller"},
+        )
+        for bad in cases:
+            with self.subTest(bad_keys=tuple(bad)):
+                with self.assertRaises(RuntimeError):
+                    _headers()(bad)
+
+
+    def test_standard_library_redirect_handler_denies_all_redirects(self):
+        source = ast.parse(TARGET.read_text())
+        cls = next(n for n in source.body if isinstance(n, ast.ClassDef)
+                   and n.name == "_NodeNeverRedirect")
+        namespace = {"urllib": urllib}
+        exec(compile(ast.Module(body=[cls], type_ignores=[]), str(TARGET), "exec"),
+             namespace)
+        handler = namespace["_NodeNeverRedirect"]()
+        self.assertIsNone(handler.redirect_request(
+            None, None, 302, "Found",
+            {"Location": "https://attacker.example"}, "https://attacker.example"))
+        self.assertIsNone(handler.redirect_request(
+            None, None, 307, "Temporary Redirect",
+            {"Location": "https://attacker.example"}, "https://attacker.example"))
+
+    def test_node_transport_never_replays_mutations_or_follows_redirect(self):
+        source = ast.parse(TARGET.read_text())
+        fn = next(n for n in source.body if isinstance(n, ast.FunctionDef)
+                  and n.name == "_call_node_preview")
+        url = ("https://purple-dune-06b5da200-p0249writes."
+               "eastasia.2.azurestaticapps.net/api/campaigns")
+        header = {"x-rgai-supabase-jwt": "a.b.c"}
+        actions = []
+
+        class FakeResponse:
+            status = 202
+            def __init__(self, payload=b'{"status":"PLANNING"}'):
+                self.payload = payload
+            def read(self, count):
+                return self.payload[:count]
+            def __enter__(self):
+                return self
+            def __exit__(self, *args):
+                return False
+
+        class Opener:
+            def __init__(self, results):
+                self.results = iter(results)
+            def open(self, req, timeout):
+                actions.append((req.full_url, req.get_method(),
+                                req.headers.get("X-rgai-supabase-jwt")))
+                item = next(self.results)
+                if isinstance(item, BaseException):
+                    raise item
+                return item
+
+        def invoke(items, method="POST", expected=(202,)):
+            namespace = {
+                "json": json, "urllib": urllib, "time": time,
+                "NODE_PREVIEW": url[:-len("/api/campaigns")],
+                "_NODE_OPENER": Opener(items),
+            }
+            exec(compile(ast.Module(body=[fn], type_ignores=[]),
+                         str(TARGET), "exec"), namespace)
+            return namespace["_call_node_preview"](
+                url, method=method, payload={} if method=="POST" else None,
+                headers=header, timeout=30, expect=expected)
+
+        self.assertEqual(invoke([FakeResponse()]),
+                         (202, {"status": "PLANNING"}))
+        self.assertEqual(len(actions), 1)
+        self.assertEqual(actions[0][2], "a.b.c")
+        actions.clear()
+        redirect = urllib.error.HTTPError(
+            url, 307, "Temporary Redirect",
+            {"Location": "https://attacker.example"}, io.BytesIO(b""))
+        with self.assertRaisesRegex(RuntimeError, "REDIRECT_DENIED"):
+            invoke([redirect])
+        self.assertEqual(len(actions), 1)
+        actions.clear()
+        transient = urllib.error.HTTPError(
+            url, 503, "Unavailable", {}, io.BytesIO(b""))
+        with self.assertRaisesRegex(RuntimeError, "TRANSACTION_UNCONFIRMED"):
+            invoke([transient])
+        self.assertEqual(len(actions), 1)
+        actions.clear()
+        with self.assertRaisesRegex(RuntimeError, "TRANSACTION_UNCONFIRMED"):
+            invoke([TimeoutError("failed")])
+        self.assertEqual(len(actions), 1)
+
+    def test_get_transient_retry_is_bounded_and_never_changes_target(self):
+        """An idempotent GET may retry; a mutating POST/PATCH never may."""
+        source = ast.parse(TARGET.read_text())
+        fn = next(n for n in source.body
+                  if isinstance(n, ast.FunctionDef) and n.name == "_call_node_preview")
+        origin = ("https://purple-dune-06b5da200-p0249writes."
+                  "eastasia.2.azurestaticapps.net")
+        url = origin + "/api/campaigns/11111111-1111-4111-8111-111111111111"
+        headers = {"x-rgai-supabase-jwt": "a.b.c"}
+        seen = []
+        slept = []
+
+        class Response:
+            status = 200
+            def __enter__(self): return self
+            def __exit__(self, *_): return False
+            def read(self, length):
+                return b'{"status":"DRAFT"}'
+
+        class Opener:
+            def __init__(self, items):
+                self.items = iter(items)
+            def open(self, request, timeout):
+                seen.append((request.full_url, request.get_method(),
+                             request.headers.get("X-rgai-supabase-jwt")))
+                item = next(self.items)
+                if isinstance(item, BaseException):
+                    raise item
+                return item
+
+        def run(items, *, method="GET", payload=None):
+            space = {
+                "json": json, "urllib": urllib,
+                "time": type("FakeTime", (), {"sleep": lambda _, delay: slept.append(delay)})(),
+                "NODE_PREVIEW": origin, "_NODE_OPENER": Opener(items)
+            }
+            exec(compile(ast.Module(body=[fn], type_ignores=[]),
+                         str(TARGET), "exec"), space)
+            return space["_call_node_preview"](
+                url, method=method, payload=payload, headers=headers,
+                timeout=6, expect=(200,))
+
+        err = urllib.error.HTTPError(url, 503, "Unavailable", {},
+                                     io.BytesIO(b"server error"))
+        self.assertEqual(run([err, Response()]), (200, {"status": "DRAFT"}))
+        self.assertEqual(len(seen), 2)
+        self.assertEqual(slept, [4])
+        self.assertTrue(all(item == (url, "GET", "a.b.c") for item in seen))
+
+        seen.clear()
+        slept.clear()
+        with self.assertRaisesRegex(RuntimeError, "TRANSACTION_UNCONFIRMED"):
+            run([TimeoutError("timeout"), TimeoutError("timeout"),
+                 TimeoutError("timeout")])
+        self.assertEqual(len(seen), 3)
+        self.assertEqual(slept, [4, 8])
+
+        for method in ("POST", "PATCH"):
+            seen.clear()
+            slept.clear()
+            with self.subTest(method=method):
+                with self.assertRaisesRegex(RuntimeError, "TRANSACTION_UNCONFIRMED"):
+                    run([err], method=method, payload={})
+                self.assertEqual(len(seen), 1)
+                self.assertEqual(slept, [])
+
+        # Reject same-path redirection (as well as cross-host redirect) and
+        # do not convert it into an opaque success/readback.
+        seen.clear()
+        redirect = urllib.error.HTTPError(
+            url, 302, "Redirect", {"Location": url}, io.BytesIO(b""))
+        with self.assertRaisesRegex(RuntimeError, "REDIRECT_DENIED"):
+            run([redirect])
+        self.assertEqual(len(seen), 1)
+
+        seen.clear()
+        forbidden = urllib.error.HTTPError(url, 403, "Forbidden", {},
+                                           io.BytesIO(b'{"message":"private"}'))
+        with self.assertRaisesRegex(RuntimeError, "UNEXPECTED_HTTP_STATUS_403"):
+            run([forbidden])
+        self.assertEqual(len(seen), 1)
+
+    def test_pure_source_integration_keeps_dev_and_mutation_safety(self):
+        source = TARGET.read_text()
+        self.assertIn("_NODE_OPENER.open(req,timeout=12)", source)
+        self.assertIn("_NODE_OPENER.open(health,timeout=12)", source)
+        self.assertNotIn("urllib.request.urlopen(", source)
+        self.assertIn("original=node_preview_headers(headers or {})", source)
+        self.assertIn("is_node=url.startswith(NODE_PREVIEW+\"/api/\")", source)
+        self.assertIn("P0249_REAL_NODE_HTTP_TRANSACTION_UNCONFIRMED", source)
+        self.assertIn("RGAI_DEV_CANARY_APPROVAL", source)
+        self.assertNotIn("sb_secret_", source)
+        self.assertNotIn("WineShopPOS", source.split("def node_preview_headers", 1)[1])
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

## PR #955 — HEAD 6fedbba1befa1deb11eb928ad420e035133c47bd
https://github.com/saifsiddiqui59/RetailGrowthAI/pull/955/files

### docs/DECISIONS.md
~~~~diff
@@ -1125,3 +1125,68 @@ Owner direction to reuse original VoiceStudio code implemented with unchanged pi
 - Accept **source-only** recovery of old #767 private trace generation/scope fence into #960; no backend authorization implied. Accept compatible #796 Unicode/bidi control checks into newest main under #962, retaining valid Devanagari virama conjunct behavior and mock-only provider tests, **not** old signed CAS/editor approval. Separate reviewer/security approval remains needed for hosted tenant/JWT/RLS/VoiceStudio/F4/F7 changes, original F2-03/F2-12/F2-17 task status not automatically DONE.
 - Archive-only source preservation and source-level mock CI never grant rights for real media, commercial voice inference, paid provider, GPU, PROD or WineShopPOS.
 
+## 2026-11-15 — #249 isolated Y1 shadow activation must be manually dispatched
+- **Decision:** Never tie DEV Azure appsetting writes to a `push`, squash-merge title or commit-message string. Protected trial PR #939 requires `workflow_dispatch`, explicit YES, main, tagged exact Y1-only guard, rollback marker, EXIT cleanup and separate independent restore. This is source security-hardening with [CI #43707648803](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43707648803) 4/4; independent security/ops review remains required and no Azure activation occurred.
+- **Source integrated (#954, main `9289fd79`, exact PR CI 4/4; postmerge main CI pending):** Reuse only the original one-entry origin-bound, 300-second JWKS-set verifier in Y1 signed GET warm path; do not reuse JWT claims, authorization, TenantStore, membership or request-scope data. Treat code/offline CI as distinct from hosted positive Auth and original Flex gateway remediation.
+- Follow-up: #939 branch source was merged forward onto main without dropping its six original changed Git blobs (merge commit `e8f5e16d3e4344eb1d4d997232e7598bf78ef8f9`), but remains **OPEN/unreviewed**; no workflow dispatch, appsetting activation, real JWT test or cutover occurred.
+
+## 2026-11-15 — #249 Auth-only fixture first; avoid live campaign INSERT side effects
+- Use modern opaque `sb_secret_` as `apikey` only in protected disposable Auth test runner; legacy JWT service-role keys may be sent as Bearer. Original Y1 receives public publishable key only; temporary shadow requires manual dispatch, independent review and verified cleanup.
+- Read-only DEV catalog confirmed `campaign_job_outbox` AFTER INSERT and subscription reserve BEFORE INSERT triggers on `public.campaigns`. **Do not seed live signed two-shop campaign rows** without a separately reviewed no-worker/usage and exact cleanup strategy. Source-only Auth identities do not demonstrate own-shop GET200 or full RLS parity; do not claim #249 closure.
+
+## 2026-11-15 — #249 bounded verifier consistency across Flex API and Feature2
+- When sharing `cached_supabase_verifier(origin)` in the Azure Functions root module, both ordinary `build_api` and optional `build_feature2_api` must call that imported name, not an undefined `SupabaseJWTVerifier` symbol. Cache only bounded project JWKS verifier, never caller JWT, permissions, current membership or tenant store. Keep Feature2 off-by-default and retain current per-request tenant/RLS checks; source regression in [PR #965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965), independent root/Feature2 security review still required. No pre-handler 503 repair claimed.
+
+## 2026-11-17 — #249 admin cleanup must verify UUID plus exact synthetic identity before delete
+- The bounded DEV-only protected Auth trial is allowed to delete only a marker `rgai-p0249-jwt-` plus exactly 16 lowercase hex characters ending with `@example.invalid`. Even a known created-user UUID is **insufficient** authority: always independently GET its actual Admin user object first and require exact canonical UUID/email. Abort on a mismatched, malformed, missing or ambiguous account; never issue DELETE merely because an unexpected admin response contained an ID. Check the create-result email before attempting sign-in. Preserve limited exact pagination for uncertain-create ACKs and independent Azure setting rollback.
+- Account deletion does not revoke previously signed JWT access tokens. Synthetic Auth-only users gain no shop memberships, and no customer, campaign, worker or subscription data are changed by this trial. Protected workflow cannot activate from a push and still requires independent security/ops review; no real hosted acceptance from offline tests.
+
+## 2026-11-17 — #249 DEV signed canary HTTP redirects must fail closed
+- All credential-bearing DEV #249 Auth Admin/public-key and signed-bearer Y1 canary HTTP clients must **not follow 301/302/303/307/308** responses: a pre-validated URL is insufficient if the HTTP library automatically follows a subsequent Location. Record a 3xx as failed trial evidence, never carry tokens or keys to a redirected host. Synthetic tests prove the attempted request count remains one at the pinned origin. This is source safety hardening on open protected #939, not a hosted Azure gateway fix, no independent workflow approval and no permission to deploy.
+
+## 2026-11-17 — The original user-token PostgREST transport must reject redirects
+- A trusted initial Supabase HTTPS URL does **not** constrain `urllib.request.urlopen`'s default redirect target. The original `TenantStore` sends both the requesting user's Supabase JWT and the project publishable key on PostgREST GET; use a no-redirect `HTTPRedirectHandler` default opener so 301/302/303/307/308 cannot silently forward these credentials. Treat such responses as unavailable, never a success. Preserve injection of mock network transport for isolated tenant/RLS negative fixtures. Security review and exact-head CI are required; this source measure is not proof or remediation of the Azure Flex gateway's pre-handler 503.
+
+## 2026-11-17 — #249 JWT transport trust must include both the first hop and redirected POSTs
+- No-redirect alone does not validate a misconfigured *initial* Supabase URL: validate canonical HTTPS origin with no userinfo/path/query/fragment/invalid port/control or backslash before even constructing JWT-bearing PostgREST calls. Retain valid origin + optional trailing slash and explicit test-only injected transports. Treat redirect responses as terminal storage failures for **both GET and POST**, preventing credential forwarding **and** redirect-induced mutation replay (including 302/307/308). Keep this source-only shared-code change review-gated; it does not prove ingress gateway 503 repaired.
+
+## 2026-11-17 — #249 rejected PostgREST HTTP responses own a socket: always close
+- A denied 30x, 401/403 or quota/error `urllib.error.HTTPError` carries the underlying response object. Preserve safe sanitized HTTPAPI errors while deterministically closing `HTTPError` via a `finally` clause on the original JWT-backed `TenantStore._request` handler. Test with held synthetic 301/302/303/307/308 response objects and both GET/POST, not just eventual garbage collection; do not follow or retry redirects. Source-only; original gateway ingress diagnosis and independent security review remain separate.
+
+## 2026-11-17 — Extend original #249 fail-closed HTTP trust boundary to elevated workers
+- The original `AdminStore` performs backend-only PostgREST GET and privileged mutating RPCs with `sb_secret_` keys or legacy JWT service-role credentials. The initial `https://` prefix check and normal `urllib.request.urlopen` are insufficient: HTTP 30x can forward keys or redirect a POST. Require full canonical HTTPS project origin, a no-redirect default opener preserving test transport injection, and deterministic `HTTPError` close. Treat redirects as sanitized storage errors with **no automatic mutation replay**. Shared security review/actual safe release remain required; this does not cure Azure pre-handler 503.
+
+## 2026-11-17 — #249 invalid user token vs unavailable JWKS are distinct states
+- Original `SupabaseJWTVerifier` must fail closed on both bad signatures and unavailable project signing keys, **but HTTP status must distinguish them**: PyJWT connection-layer `PyJWKClientConnectionError` -> noncredential `SigningKeysUnavailable` -> sanitized `HTTPAPI` 503, whereas invalid signature/key-id/claims remain 401. This neither retries a write nor logs tokens/JWKS exception details. It is a **handler-marked dependency 503**, not evidence for the historic **unmarked pre-handler Azure ingress 503**. Source-only shared auth needs independent security review before main integration or hosted activation.
+
+### 2026-11-17 — #249 distinguish marked handler dependency 503 from unmarked gateway 503
+- The original Y1 shadow `campaign_read.main` preserves safe `X-Request-ID` for a true JWKS connection outage classified by the original verifier+HTTPAPI as dependency 503. Add actual handler-level synthetic fixture, asserting no tenant reads and no secret leakage. This is an offline observability distinction, **not** the historical original Flex Azure ingress outage resolution or permission to enable Y1.
+
+## 2026-11-17 — #249 recheck real hosting contrast without enabling signed shadow
+- Previously merged protected **read-only** diagnostic jobs are allowed to measure current Y1 and original Flex anonymous/synthetic GET status, latency and handler marker without Azure writes. A successful Actions job merely proves observation completed, not reliable HTTP acceptance. Pin exact rerun attempt in evidence; distinguish old historical passed windows from fresh data.
+- Protected #939 genuine disposable JWT trial acceptance must include **two independently signed Auth-only JWTs after 240 seconds idle** and reject already-near-expiry JWT before the idle; no final signed success receipt until both exact GoTrue cleanup operations complete. Still requires independent protected workflow security/ops review; do not enable public Y1 settings from CI or PR push. Auth-only signed 404s do not prove positive retailer tenant parity.
+
+## 2026-11-17 — #249 favor isolated Y1 HTTP path only after signed parity, preserve original workers
+- New real protected read-only Flex vs Y1 comparison: original Flex route matrix 6/9 anomalous, including unknown route timeouts absent app marker, while independent existing isolated Y1 returned 40/40 synthetic HTTP GET statuses and 12/12 expected missing-JWT denials across immediate and 240s-idle windows. This supports continuing Y1 **as a candidate**; not a proof of original Azure gateway RCA, production readiness, two-shop signed RLS or mutation endpoints.
+- Keep original worker/timer triggers on the original Flex until reviewed migration; never blindly deploy full root API to Y1 and duplicate queue/timer ownership. Privileged signed two-user trial #939 remains manually dispatched only after independent protected security/ops review, exact-head four green jobs and verified temporary settings rollback.
+
+### 2026-11-17 — #249 shared JWT dependency outage error contract includes Feature2
+- Returning 503 only for a connection-layer signing-key fetch failure is not enough when Feature2 has three independent `TrendFeatureAdapter` handler families. Convert `SigningKeysUnavailable` in all three to existing stable sanitized storage/dependency **503** contracts, never generic 500 or invalid-JWT 401. No retries of POST, membership bypass, debug tokens or paid model activation; source requires independent shared auth/Feature2 review.
+
+## 2026-11-17 — #249 make disposable Auth cleanup recoverable across jobs
+- A protected Auth-only canary that owns two short-lived synthetic users must have recovery outside the test runner: derive strictly the two run-bound labels from the GitHub run ID + attempt + slot using SHA-256 (16 hex characters) and authorize deletion **only after fresh exact UUID/email verification**. A second protected job reconciles both even if the first cannot finish normally; failure/ambiguity must mark the run red. Neither marker nor JWT is a secret by itself, but Admin credentials stay runner-only.
+- `if: always()` is best-effort and cannot guarantee a recovery job on full workflow cancellation/control-plane outage. Keep explicit manual run-ID-scoped recovery documented, independent security approval mandatory, and no authenticated trial/runtime change merely from source tests.
+
+## 2026-11-17 — #249 positive two-shop fixture must avoid job outbox and preserve billing semantics
+- Actual current DEV trigger definition enqueues campaign jobs only on `status='PLANNING'`; `DRAFT` can avoid outbox, **not** `reserve_subscription_unit` (BEFORE INSERT applies regardless of status and reserves one unit in synthetic shop trial). A separate reviewed positive RLS fixture may use disposable trial shops and schema-valid DRAFT campaign days, with asserted zero outbox events, exact usage reservation count and verified cleanup. Do not claim zero side effects or bypass triggers with `session_replication_role`.
+- Delete shops (and cascading child reservations/subscriptions/campaigns) **before** Auth owners because `shops.owner_user_id` FK is not ON DELETE CASCADE; fail closed on any unknown identity/child/tenant scope. This does not authorize live mutations under #939 Auth-only workflow.
+
+## 2026-11-17 — #249 TLS-complete no-first-byte evidence prioritizes hosting isolate
+- Fresh original Flex GET-only curl phase trace found 6/8 no-first-byte timeouts at 20s despite DNS/TCP/TLS already finished (~0.65s); paired 6/9 anonymous route matrix confirms both valid auth-gated routes and unknown route can fail. Function worker-start telemetry is aggregated and not correlated at invocation level, so no definitive platform RCA. Avoid claiming a JWT verifier, FFmpeg worker or simple model import adjustment alone repairs this pre-handler ingress symptom. Validate isolated Y1 signed retailer auth, tenant/RLS, and the entire API contract before safe staged cutover.
+
+## 2026-11-17 — #249 stage only GET-status parity source before any Y1 ZIP or settings
+- The original Flex 503/timeout issue is not fixed by JWT cache or a single route; current live matrix reproduces 6/9 anomalies (notably poster draft/job and render job GET 18s no-first-byte), while different-host Y1 passes two anonymous/no-JWT windows with 240s idle. Prioritize a protected, source-first separate-hosting path rather than rewriting auth or moving queue/timer triggers.
+- [#968](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/968) stages exactly GET-only Python v1 wrappers for `render-jobs/{id}`, `poster-jobs/{id}`, `poster-drafts/{id}`, delegated to original `HTTPAPI`, `RenderAPI.get`, `PosterRenderAPI.get`, `PosterDraftAPI.get` and per-request caller-JWT RLS. Require a **second explicit OFF-by-default Y1 flag** `RGAI_P0249_EXTRA_GET_SHADOW` in addition to original shadow/public-key checks. No service-role, renderer, queue, timer, GPU, paid provider or arbitrary method/route allowed. Do not deploy from source PR or piggyback on #939's three-setting rollback; any five-route ZIP/deploy/setting rollback needs separate independent review. Positive signed two-shop and no-billing-leak fixture proof required before cutover.
+
+### 2026-11-17 — #249 require original cryptographic JWT and current member tests even for safe Y1 read status
+- Source-only Y1 status GET adapters must execute the actual signed RS256 verifier and original tenant/membership code, not only mocks of a returned `user_id`; test both synthetic shops, forged foreign records, membership revocation, bad issuer/signature, role and expiry against an offline no-write PostgREST transport. This is a **minimum source gate**, not authority to deploy. Production/customer JWT, private media and paid services stay entirely absent from tests; independent review and protected hosted E2E remain mandatory.
~~~~

### docs/NEXT_TASK.md
~~~~diff
@@ -1502,3 +1502,84 @@ Feature3 NEXT: verify main CI #41820799158, integrate reviewed 24-component sour
 4. For each missing old feature patch, inspect archived diff and latest same-module code, port only missing behavior into **reviewable current-main feature-owned changes**, keep existing newer sources, run exact-head four jobs and fresh main four jobs. Shared JWT/RLS/storage/F4/F7/Functions routes require independent affected-lead review. Do not turn disabled Kokoro/Azure-only voice drafts into active model calls: favor approved VoiceStudio CPU-only. Azure #249 and #650 remain OPEN.
 5. Continue other independent non-GPU Feature2 source jobs while private hosted test identities/licenses/editor rights are unavailable. No paid provider, Azure SQL/PROD, new GPU or WineShopPOS mutation.
 
+## 2026-11-15 — #249 next code/host milestones after manual-only source guard
+1. PR #954 source-only JWKS change merged after final [4/4 CI #43708057346](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43708057346). Verify fresh exact merge-SHA [main CI #43708417378](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43708417378) **4/4** before marking integrated source DONE; do not infer hosted performance from cache code alone.
+2. Obtain independent review for protected workflow PR #939 (source head `1f2ead12713e8d08fcb2eea5a5c1fef0cdd968f1`, CI 4/4); manually dispatch only after protected approval/rollback monitoring. Explicit `workflow_dispatch` YES required, never autoactivate from main merge. Reconfirm three public-only Y1 appsettings absent after cleanup.
+3. If signed Auth-only hosted acceptance succeeds, create/clean authorized disposable **two-shop** signed test identities and campaigns, confirm original API own-shop 200, foreign 404/403, revoked membership denial and current RLS. Do not use or overwrite existing RetailGrowthAI owners, user data or service-role credentials in Y1.
+4. Evaluate/qualify full API-only HTTP ingress migration separately while retaining original Flex and preventing duplicate queue/timer/render workers; only close #249 on actual poster select/download and 503 latency/availability acceptance, not synthetic Y1 GET alone.
+- Follow-up: #939 branch source was merged forward onto main without dropping its six original changed Git blobs (merge commit `e8f5e16d3e4344eb1d4d997232e7598bf78ef8f9`), but remains **OPEN/unreviewed**; no workflow dispatch, appsetting activation, real JWT test or cutover occurred.
+
+## 2026-11-15 — #249 secure real-user test follow-up
+1. Verify current [#939](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/939) final exact-head 4/4 CI after modern secret-key header correction and bounded exact-user cleanup. **Do not self-approve** shared protected workflow; obtain independent security review before any manual DEV dispatch.
+2. Only run genuine signed two-user **Auth-only** Y1 trial with exact three-setting rollback, human monitoring and clear evidence of final settings absence. Current real DEV campaign INSERT automatically enqueues outbox and reserves subscription usage, so the later two-shop positive GET200/foreign-404 fixture needs separate no-worker seeding and cleanup review; do not create ordinary campaigns as a shortcut.
+3. Preserve original Flex, no duplicate worker/queue/timer triggers, no cutover until genuine poster select/download reliability and tenant denial tests pass. #249 remains OPEN.
+
+## 2026-11-15 — #249 Feature2 verifier code regression checkpoint
+1. Verify [#965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) final exact-head 4/4 CI, confirm its one-line root Functions fix and synthetic enabled Feature2 builder tests, obtain required affected Feature2/security review, reconcile newest main before any merge and then verify fresh main 4/4. It fixes a **handler NameError**, not the pre-handler Azure 503 or full hosted acceptance.
+2. #939 remains open until independent protected workflow review; no automatic/manual Y1 cloud mutation from mere source CI. Two-shop signed positive RLS still requires approved clean fixtures with no queue/billing side effects. Do not close #249 prematurely.
+
+## 2026-11-17 — Issue #249 next reviewed acceptance step
+1. Review exact current head of [protected Y1 trial #939](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/939); after final exact-head 4/4 and independent affected security/ops review, an authorized operator may deliberately merge and invoke **manual-only** protected DEV trial. Verify three temporary public settings absent at end, two actual signed synthetic users valid 404 and forged-token 401 in Y1, no original Flex changes. Deleting synthetic GoTrue identities does not itself revoke JWT; no shop/campaign identities or live data may be seeded here.
+2. Independently review and safely integrate [root Functions + Feature2 fix #965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) after final CI, then verify fresh postmerge main 4/4. This corrects handler-level NameError/500 risk, not earlier pre-handler 503.
+3. Plan isolated **positive two-shop** fixture separately: current DEV campaign INSERT triggers outbox queue and subscription reservation, so do not blindly seed campaign rows. Original gateway #249 remains OPEN pending hosted JWT/RLS, measured post-idle HTTP, poster read/select/download parity, safe no-worker routing transition. No GPU, PROD or WineShopPOS.
+
+## 2026-11-17 — #249 next verified actions after safe-redirect patch
+1. Check final **exact-head four-job** result for [#939 at 58d27135](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/939); Python redirect-denial tests passed but other jobs were not yet complete at this checkpoint. Inspect newer source heads and recheck CI if another worker pushes.
+2. Obtain actual independent security/ops review of the **manual-only** protected Azure workflow and temporary Y1 public configuration; no source-only reviewer impersonation, auto-merge or dispatch. Review synthetic Auth cleanup, independent rollback, no-redirect HTTP clients and zero campaign seeding before authorizing a bounded DEV trial.
+3. After approved protected dispatch, separately verify all three Y1 settings ABSENT and retain original Flex unchanged. Signed Auth-only 404 validates original JWT processing, **not** own-shop GET200/foreign-shop RLS, poster select/download, worker parity or closure of #249.
+
+## 2026-11-17 — #249 next integration after original PostgREST redirect repair
+1. Verify final exact-head four-job [CI #44000033699](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44000033699) at `0a6828249a16110f19059899d14b79917a5b7668` for [source #965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965). Security reviewer must inspect the default no-redirect PostgREST reader, updated two-shop transport fixture, Feature2 verifier constructor and current-main compatibility before any shared/root merge. Recheck newer heads before acting.
+2. Complete independent review of manual-only protected [Y1 trial #939](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/939), preserving synthetic cleanup and independent rollback; no workflow dispatch or Azure activation from source CI. Then deliberately run a separately authorized bounded signed Auth-only trial and prove all three public Y1 settings are removed.
+3. The original Flex pre-handler HTTP timeouts and poster select/download latency/hosted cross-tenant acceptance remain unsolved. Do not mark #249 done or migrate worker triggers without genuine evidence. No GPU, PROD or WineShopPOS.
+
+## 2026-11-17 — #249 exact-head gate for HTTPS-origin and POST redirect regressions
+1. Verify [Part 1 CI #44007592073](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44007592073) all four jobs at source [#965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) head `4b75a0b2eb8cc8d77d5a4e710e22f6a8fda93d60`; do not reuse green evidence from prior head. Confirm exact changed paths and no newer main integration drift; require independent shared JWT/RLS security review before merge, plus postmerge main CI.
+2. After separate independent ops review of [#939](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/939), only deliberate bounded DEV Y1 public-only signed Auth test with verified restoration may establish hosted auth handling; live two-shop 200/foreign-row 404, original Flex pre-handler 503 diagnosis and poster parity remain open. Never claim issue resolved from local regressions.
+
+## 2026-11-17 — #249 final source gate for denied-response cleanup
+- At [PR #965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) head `5790d4fcd787800455707d58dafd82a953281fe4`, inspect exact four-job [CI #44008226907](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44008226907), including `test_p0249_tenant_store_redirects.py` response-closure cases. Reconfirm latest main before merge. Independent JWT/RLS/Functions reviewer still required; no DEV activation or claims from offline green tests. Continue separately gated [#939](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/939) Y1 trial, original 503 and true signed positive two-shop acceptance.
+
+## 2026-11-17 — #249 privileged worker redirect gate
+1. Verify final source [PR #965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) head `69758c5ccc3298f65c4dd59727d2d27f91adac08` [CI #44029160113](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44029160113), including original AdminStore legacy-service/opaque-key redirected POST/GET tests and existing user-JWT two-shop parity. Reinspect the latest main and obtain **independent affected Functions/auth/security review** before shared original backend merge. Never substitute older green CI from pre-admin head.
+2. Preserve unmerged manual-only Y1 [PR #939](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/939) and exact temporary rollback; independent ops review remains necessary before any protected DEV test. Original Flex pre-handler 503, real hosted positive two-shop JWT/RLS, poster select/download and safe app cutover remain NOT DONE.
+
+## 2026-11-17 — #249 next gate after JWKS dependency outage classification
+1. Verify [PR #965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) source head `8a713825ce1aa6dde602d76e00f878ebb04dcbad` [CI #44087947443](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44087947443) four jobs (including `test_p0249_jwks_outage_classification.py`). Independently review shared verifier/HTTPAPI/worker code before any main merge. Recompare against latest main and require fresh main 4/4 after accepted integration.
+2. Separately review manual-only protected [Y1 trial #939](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/939), then deliberately test signed DEV Auth GET with exact 3-appsetting rollback, no worker role or production path. Original **pre-handler** Flex ingress 503 and positive two-shop/shop-member acceptance remain open independent validation, not solved by classifying JWKS 503.
+
+### 2026-11-17 — #249 Y1 handler outage-classification exact-head gate
+- Verify source [#965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) `681ec17dee7a5a64a50f31c5b486c2f4cc8deedc` [CI #44088585523](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44088585523) all four jobs, including actual offline `campaign_read.main` JWKS transient 503 + request marker test. Require independent JWT/RLS shared Functions review, preserve protected Y1 [#939](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/939) manual-only activation/rollback gates. No hosted proof or original 503 root-cause yet.
+
+## 2026-11-17 — #249 verify active read-only comparison and signed idle trial
+1. Inspect latest rerun attempts of read-only [Y1 #42964811296](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42964811296) and [original Flex #40100546239](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40100546239). Classify real statuses/marker and timeout without conflating observation success with HTTP acceptance. Neither existing workflow changes appsettings or deploys.
+2. Finish latest [PR #939](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/939) exact-head CI and independent protected workflow review; **do not dispatch before review**. Its signed positive Auth-only test now validates two user JWT 404s after 240-second idle with exp margin and exact deletion; original positive two-shop GET200/foreign 404 cannot be inferred from no-shop identities.
+3. Continue safe no-worker positive two-shop fixture plan, poster GET/select/download routing parity, and original Flex HTTP P0. Keep Azure/GPU/PROD/WineShopPOS unchanged until independently approved.
+
+## 2026-11-17 — #249 measured hosting comparison directs next activation
+1. Actual same-day read-only evidence: Flex [#40100546239 rerun](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40100546239) had **6/9 anomalies**, while Y1 [#42964811296 rerun](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42964811296) passed **40/40 plus 12/12** after a 240s idle. Keep original Flex unchanged and issue OPEN.
+2. Independent security/ops review, merge and deliberately approved protected manual dispatch are required for #939 genuine signed two-user after-idle JWT trial (exact-head [CI #44088736861](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44088736861) 4/4 PASS); confirm rollback of exactly three public Y1 settings. Do not turn on via push or PR merge.
+3. After signed no-shop evidence, build safe positive own-shop GET200 and foreign-shop 404 against isolated, no-outbox, no-subscription-charge test data; verify poster GET/select/download and HTTP route parity before routing or shutdown. No duplicated worker/queue/timer and no PROD/WineShopPOS/GPU changes.
+
+### 2026-11-17 — #249 Feature2 JWT outage correct failure status gate
+- Verify exact-head [CI #44089856853](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44089856853) for shared [#965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) source `63f5cbe4bbc3840b3ced6aeb60938976137782bc`: true verifier network-failure classification must yield safe 503 in original campaign/Y1 and Feature2 trends/prompt/draft paths; invalid JWT remains 401, no tenant reads. Require independent security/Feature2 review before merging; verify latest main. Protected manual Y1 trial [#939](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/939) and original Flex unmarked 503 remain separate.
+
+## 2026-11-17 — #249 verify independent Auth cleanup and protected approval
+1. Latest #939 also includes deterministic original-run/attempt-specific two Auth-only user markers plus protected `independent-restore` `cleanup-only` step. Inspect final exact-head CI (all four) and independent review before even manually activating. Verify temporary public Y1 settings and both disposable Auth identities absent after completion; on a cancelled entire workflow, explicitly reconcile the original run ID/attempt manually in protected environment—an `always()` job is not guaranteed on cancellation.
+2. Signed post-idle real Auth-only 404, genuine positive two-shop RLS, poster API parity and original ingress 503 remain unresolved independently; no quick pass from merely compiling a workflow.
+
+## 2026-11-17 — #249 no-worker two-shop fixture design, source first
+1. For a separately reviewed protected signed two-shop positive test, source current live `enqueue_new_job`: only PLANNING campaigns enqueue. A fixture using DRAFT avoids outbox but **still reserves one trial campaign unit**; use separate disposable shops with explicit bounded quota accounting and exact cleanup. Never use READY with missing days as a bogus successful API fixture. Verify real `validate_campaign` DRAFT contract before implementing test rows.
+2. Verify shop/campaign/children/usage/subscription cleanup is exact; **delete disposable shops before Auth users**, as `shops.owner_user_id` has non-cascade user FK. Keep two-shop setup distinct from current #939 Auth-only trial and independently review every hosted DEV data change. Existing original Flex #249 remains OPEN.
+
+## 2026-11-17 — #249 next Azure escalation evidence
+1. Pair the reviewed read-only original Flex [#40100546239 rerun](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40100546239) **6/9 HTTP anomalies** with [transport-phase #40176054781 rerun](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40176054781) **6/8 no-first-byte after completed TLS** and Y1 [#42964811296 rerun](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42964811296) **40/40 and 12/12 after idle**. These are a concrete DEV-only Microsoft.Web hosting escalation dossier, not proof of root cause; request Azure diagnostics/support only where no unexpected fee/privilege.
+2. Retain original Flex and active queue/timer workers until protected Y1 signed Auth-only trial, positive same/foreign shop read, poster route parity, rollback and safe transition are independently accepted.
+
+## 2026-11-17 — #249 verified route matrix => staged Y1 three status GET source
+1. Compare exact [original Flex attempt 3 #40100546239](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40100546239) **6/9** anomalies against [Y1 attempt 3 #42964811296](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42964811296) **40/40+12/12** across 240s. Preserve red/green interpretation: successful observation job is not original Flex acceptance, and no Y1 signed or two-shop RLS proof exists.
+2. Finish [new source-only PR #968](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/968) exact-head four CI checks and affected JWT/RLS, render and poster reviewer approval. Only once verified, prepare a **separately reviewed, manual-only DEV** 5-GET Y1 bundle/deploy with exact current Y1 two-route preflight, no queue/timer/paid service, rollback and both off-by-default public flags. Never rerun obsolete one-route-create workflow.
+3. Protected [#939](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/939) Auth-only two-user 240s signed trial still needs independent security/ops review, genuine hosted success and cleanup before extra GET activation. Positive owned/foreign-shop job/poster RLS fixture plus revocation needs isolated consented DEV fixture; DRAFT campaigns avoid outbox but still reserve subscription quota. Original #249 and original Flex 503 remain open; no frontend cutover or WineShopPOS modifications.
+
+### 2026-11-17 — #249 verify Y1 extra three-route signed source fixture and protected packaging
+- Verify [#968](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/968) final exact-head 4/4 after genuine local RSA-signed two-shop tests (own 200/foreign 404/current membership revocation across render status/poster job/poster draft) and independent affected security/feature review. **Do not treat offline signatures/RLS fake as hosted Auth/tenant proof**. The required second Y1 extra-GET flag remains OFF and is not part of #939's protected three-setting rollback. A separate reviewed manual 5-route ZIP/activation/rollback plan is still required; original #249 remains OPEN.
~~~~

### docs/PROJECT_STATE.md
~~~~diff
@@ -1493,3 +1493,70 @@ Feature3 verified source-integration checkpoint:
 - New [#962](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/962) surgically ports original #796 invisible/bidi Unicode prompt-safety restrictions onto **current-main** `prompt_improver.py`, with new tests; legitimate Hindi virama conjuncts preserved, mock LLM only. Exact-head [CI #43713860334](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43713860334) **4/4 PASS**, merged `e9610ffd32e27b9c9dc02aac5770c0dec45fe080`; fresh main [CI #43714482943](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43714482943) **COMPLETED SUCCESS 4/4**. Original reviewed prompt CAS and stored script review are **NOT** integrated or accepted.
 - No Azure or Supabase deployment/migration, paid AI inference, model weights, GPU, PROD or WineShopPOS mutation. Feature2 38 original IDs remain unchanged.
 
+## 2026-11-15 — Issue #249 DEV Y1 source hardening (no hosted activation)
+- Privileged trial PR [#939](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/939) removed an unsafe matching-`push` autoactivation condition: temporary public-only Y1 settings now require explicit manual `workflow_dispatch` + protected DEV environment + exact YES confirmation. Regression prohibits implicit push activation. Final head `1f2ead12713e8d08fcb2eea5a5c1fef0cdd968f1`, [PR CI #43707648803](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43707648803) **4/4 PASS**, still OPEN without independent security review and WITHOUT cloud config changes.
+- Source-only [PR #954](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/954) uses existing bounded one-entry `security.cached_supabase_verifier` on the Y1 GET-only shadow while constructing a fresh original TenantStore per request; offline same-origin/cross-origin/JWT-store checks added. An outdated source-shape test was repaired; final exact-head [PR CI #43708057346](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43708057346) **4/4 PASS**, safely source-only squash-merged to main `9289fd792641a637c3cc23a93c88889016863ed8`; fresh [main CI #43708417378](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43708417378) passed **4/4** in [main CI #43708417378](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43708417378). No hosted signed test or Azure deployment.
+- Original Flex #249 unresolved (historical 503 and pre-handler timeouts); Y1's previously verified 40/40 after-idle synthetic GET + 12/12 missing-Bearer 401 do not prove positive signed two-shop RLS or authorize frontend cutover. No Azure/SQL deployment, tenant mutation, GPU, paid provider, PROD or WineShopPOS change this continuation.
+- Follow-up: #939 branch source was merged forward onto main without dropping its six original changed Git blobs (merge commit `e8f5e16d3e4344eb1d4d997232e7598bf78ef8f9`), but remains **OPEN/unreviewed**; no workflow dispatch, appsetting activation, real JWT test or cutover occurred.
+
+## 2026-11-15 — #249 Y1 signed-Auth safety hardening checkpoint
+- Rebased original open [PR #939](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/939) onto exact main without losing source; manual-only protected Azure workflow remains unmerged and not activated. Current source adds Supabase modern opaque `sb_secret_` **apikey-only** Admin handling instead of invalid Bearer headers, plus fail-closed bounded 10-page exact synthetic-user cleanup on uncertain Auth-create acknowledgement; tests check both key types, page-two cleanup and unsafe pagination. These are source only, not hosted Auth success.
+- Read-only PostgreSQL catalog inspection of original DEV `public.campaigns` confirms an AFTER INSERT outbox enqueue trigger and BEFORE INSERT subscription reservation trigger; blindly seeding two campaigns could schedule real work and spend subscription quota. The #939 trial remains Auth-only: no shop/campaign seed, Azure settings, frontend cutover, GPU or WineShopPOS changes. Full positive two-shop signed JWT/RLS still open.
+
+## 2026-11-15 — #249 Flex shared Feature2 JWT verifier follow-up (source-only)
+- Opened [PR #965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965): current `function_app.py` imports `cached_supabase_verifier` after #946, but enabled `build_feature2_api` still called the removed `SupabaseJWTVerifier` name. That is an observable **runtime NameError / handler HTTP500 risk** on Feature2-enabled requests, not the original pre-handler gateway 503 diagnosis. Replaced the stale constructor call with the existing bounded verifier; added synthetic execution regression for enabled/disabled builder and shared security import. First CI exposed an unrelated stale source-text assertion in the existing media lazy-import suite; repaired it to validate actual security AST import. Exact-head CI and affected Feature2/security review required before merge. No Azure deploy, Auth/user/shop SQL, paid models, GPU, PROD or WineShopPOS changes.
+
+## 2026-11-17 — Issue #249 protected Y1 signed-test deletion safety, source-only
+- In existing protected [#939](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/939), fixed the disposable Supabase Auth cleanup boundary: require exactly a 16-lowercase-hex synthetic marker; re-read user by UUID via privileged Admin GET and compare exact UUID **and synthetic email** before any delete, including uncertain-create-ACK recovery; validate email on initial Admin-create response. Regression tests cover matching/swap/missing identity, malformed marker, and paginated recovery. This is source-only, **NOT a real signed hosted test**; the workflow still requires independent security/ops review and a deliberately monitored, protected manual dispatch. The current PR branch head is checked by its own CI, separate from prior passed heads.
+- Supabase Auth deletion alone does not immediately invalidate an already issued signed access JWT; isolated Auth-only users receive no shop membership. #249 original Flex ingress 503 is still OPEN; isolated Y1 previous 40/40 GET and 12/12 unsigned denials are unchanged, and live signed own-/foreign-shop read and new hosting parity remain unverified. Source [#965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) handler-level Feature2 undefined-verifier fix passed exact-head CI 4/4 but awaits independent root/router review and main integration. No Azure/SQL/Auth writes in this development pass; GPU, PROD, WineShopPOS untouched.
+
+## 2026-11-17 — Issue #249 signed DEV Y1 canary redirect guard (source review candidate)
+- Existing protected [PR #939](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/939) at source head `58d27135e29bc997cf3204ff814c8691e1cc5230` now rejects HTTP 3xx redirects in the original signed Auth helper, Y1 bearer campaign GET and Y1 negative-health probe. This prevents the default Python HTTP redirect handler from forwarding credential-bearing requests outside their pinned host. Added synthetic redirect negative tests for each path; initial exact-head [CI #43997434346](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43997434346) Python and FFmpeg jobs passed at documentation checkpoint, Supabase and frontend still running. Do not claim 4/4 until verified.
+- Source-only, **UNMERGED** and protected workflow still **unreviewed**. No actual signed hosted two-user test, Y1 appsetting activation, original Flex 503 remediation, API migration, tenant/SQL/media writes, GPU, PROD or WineShopPOS change. Original #249 remains OPEN.
+
+## 2026-11-17 — #249 original signed PostgREST redirect fix in review (not deployed)
+- [PR #965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) now changes the **original** `TenantStore` default PostgREST reader, not just DEV signed-test clients: Python's standard `urlopen` can follow HTTP 30x responses while carrying a verified user's Bearer token and project API key. The secure default transport rejects redirects; explicitly injected offline test transports remain supported. Updated real original signed two-shop mock fixture and added offline 301/302/303/307/308 regression tests verifying exactly one request to the pinned origin. Source head `0a6828249a16110f19059899d14b79917a5b7668`, [Part 1 CI #44000033699](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44000033699); final four-job status must be rechecked before any integration claim.
+- The existing Feature2 undefined-verifier repair on #965 is preserved. No real Azure deploy/config, original Flex pre-handler 503 repair, hosted signed two-shop RLS proof, queue/media action, GPU/paid inference, PROD or WineShopPOS change. Shared security review is still required; keep #249 OPEN.
+
+## 2026-11-17 — Additional #249 source-only HTTPS origin and POST-replay fence
+- Original `TenantStore` in shared-review [#965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) now also validates an exact HTTPS **origin** (no URL userinfo, unsafe port, path, query, fragment, control characters or backslash) before building any JWT-backed request. Offline regression denies invalid initial origins, allows valid project origins and proves 302/307/308 cannot follow/replay an original JWT-bearing **POST** to another host. Source head `4b75a0b2eb8cc8d77d5a4e710e22f6a8fda93d60`; [CI #44007592073](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44007592073) pending verification at this source checkpoint. Previously verified 4/4 run #44000033699 covers the prior redirect-only commit, NOT this new head. No hosted/cloud acceptance or original 503 fix.
+
+## 2026-11-17 — #249 fail-closed response/socket cleanup under source review
+- Final additional source on [#965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) closes the original PostgREST `HTTPError` response on **every** failure path (401/403 auth, 402/409/429 quota, 30x redirect, 5xx) via `finally: exc.close()`. Prior exact-head Python CI surfaced synthetic redirect response `ResourceWarning` from an unclosed `HTTPError`; new offline assertions retain redirect response objects and require they be closed after GET and POST denial. Source head `5790d4fcd787800455707d58dafd82a953281fe4`; exact-head [CI #44008226907](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44008226907) pending final jobs at documentation authoring. Still no cloud changes or original Flex gateway 503 resolution.
+
+## 2026-11-17 — #249 original privileged worker PostgREST redirect security, source only
+- [#965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) now also guards original `AdminStore` service-only PostgREST requests. Before this fix, the worker adapter used `urllib.request.urlopen`, which follows HTTP redirects and could forward elevated `sb_secret_` API keys or legacy service-role Bearer tokens to another origin, or redirect a financial/queue claim POST. The original injected `urlopen` test seam remains; production default now uses no-redirect HTTPS opener, checks the exact initial project origin, and closes all `HTTPError` response handles. New synthetic tests exercise five 30x responses for GET and POST with both credential classes, strict origin and 401/403/quota cleanup. Source head `69758c5ccc3298f65c4dd59727d2d27f91adac08`; [exact-head CI #44029160113](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44029160113) requires final all-four verification. No original Flex 503 diagnosis or hosted Y1 acceptance claimed.
+
+## 2026-11-17 — #249 transient signing-key fetch must not masquerade as invalid retailer JWT
+- On shared original Functions [#965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965), an upstream `PyJWKClientConnectionError` for Supabase asymmetric JWKS could previously be swallowed by the broad `jwt.PyJWTError` -> `AuthenticationError` conversion, yielding false 401. Source-only now raises safe `SigningKeysUnavailable` and original `HTTPAPI` converts it to sanitized handler-level **503 SERVICE_UNAVAILABLE**, without accepting unverified JWTs or making tenant reads. Invalid signature/kid stays **401**. New offline original API/verifier tests exercise both classes. Source head `8a713825ce1aa6dde602d76e00f878ebb04dcbad`; [CI #44087947443](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44087947443) requires final all-four verification. This does **not** fix original unmarked Azure ingress 503 or prove hosted JWT/RLS.
+
+### 2026-11-17 — #249 actual shadow endpoint JWKS outage marker regression
+- Added a synthetic **actual** `campaign_read.main` Y1 path test to `tests/infra/test_p0249_y1_signed_two_shop_transport.py` on source [#965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965), head `681ec17dee7a5a64a50f31c5b486c2f4cc8deedc`. Offline injected public JWKS network failure must yield **handler-marked 503**, sanitized `SERVICE_UNAVAILABLE`, no JWT/secret data and **zero** tenant queries. Prior direct verifier/HTTPAPI regression also remains. [Exact-head CI #44088585523](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44088585523) pending verification. Historical Azure Flex *pre-handler unmarked* 503 remains unresolved.
+
+## 2026-11-17 — #249 two real read-only DEV host comparisons and signed idle acceptance source
+- Re-ran existing protected **read-only** Azure checks, without any deployment or setting mutation: isolated Y1 two-route/240-second-idle workflow [#42964811296](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42964811296), and original Flex HTTP route-matrix [#40100546239](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40100546239). These are current re-run attempts of previously merged workflows; record the resulting attempt logs before claiming a current reliability result. Previous Y1 historical 40/40 and 12/12 was not signed JWT/2-shop evidence.
+- Extended existing protected [PR #939](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/939) source-only two-user test: original Y1 signed GET success immediately and again after exactly **240 seconds of no probe traffic** for both disposable Auth identities, forged signature 401, and explicit JWT validity margin (exp at least 360 seconds ahead). A final PASS receipt only occurs after both exact GoTrue user cleanup operations verify. Offline tests cover successful after-idle reads and post-idle failure cleanup. **No protected trial was dispatched**, so these are acceptance requirements, not observed signed host success. Independent workflow security/ops review remains outstanding and original #249 OPEN.
+
+## 2026-11-17 — #249 fresh Y1 versus original Flex host results (actual Azure, read-only)
+- Latest re-run attempt of original Flex [protected #40100546239](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40100546239) completed diagnostic job SUCCESS but measured **6/9 anomalies**: three poster/render GETs, poster-select POST and nonexistent-route GET each timed out at 18.0s with no handler marker; a final campaign GET returned 401 only after **26.081s**. Identity/indexing verified, synthetic no-JWT requests; original 503/timeout issue still OPEN. Do not mislabel successful diagnostic as healthy API.
+- In contrast, exact original Flex and Y1 resource identity checks passed in fresh previously-reviewed Y1 [protected re-run #42964811296](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42964811296). Existing isolated Y1 indexed exactly two GET functions and passed **40/40 health/unknown HTTP statuses** and **12/12 handler-marked no-JWT campaign 401s**, across immediate and 240-second after-idle windows. This is real hosted **unauthenticated** evidence only; does not prove genuine signed positive two-shop RLS, POST/select/download parity or safe cutover.
+- Existing #939 source head `a6ba6bb9f2ae47f1d63cd686aa23ec67eab56813` [exact PR CI #44088736861](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44088736861) **4/4 PASS**; new two genuine signed test users after-idle acceptance is source-tested only, unmerged and unexecuted pending independent security/ops review. No Azure appsetting, test Auth identity, shop/campaign, queue, GPU, PROD or WineShopPOS mutation from this source work.
+
+### 2026-11-17 — #249 Feature2 original JWT routes preserve signing-key outage 503 (source-only)
+- The same original signing-key transport failure in `SupabaseJWTVerifier` also affects separately registered Feature2 Trends, prompt-preview and draft-list handlers. In [#965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) `TrendFeatureAdapter` now maps `SigningKeysUnavailable` to each route's existing sanitized **503** error, rather than letting it become a generic **500** in `dispatch_feature2`. Explicit bad JWT/key IDs remain **401**; zero tenant reads when JWKS unavailable. Offline regression covers all three feature routes; source head `63f5cbe4bbc3840b3ced6aeb60938976137782bc`; [CI #44089856853](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44089856853) awaiting final 4/4. This is not remediation of the Azure unmarked 503 or live hosted RLS acceptance.
+
+## 2026-11-17 — #249 interrupted-trial Auth cleanup resilience (source only)
+- Existing #939 manual-only protected Y1 JWT trial now derives two **recoverable deterministic disposable Auth markers** from GitHub run ID+attempt+slot, so a separate protected `independent-restore` job can reconcile both via exact GoTrue UUID/email verification even after the temporary test step is interrupted. The restore job uses its own runner-only Admin key and cannot send this key to Y1. Offline tests cover run separation, malformed slot, cleanup both slots even if one fails, and no unsafe deletion. Exact-head CI pending at note time. A cancelled whole workflow cannot guarantee execution of an `always()` job: manual operator recovery of the precise run ID+attempt may still be required. No hosted Auth account or Azure settings touched; independent reviewer still required before merge/dispatch.
+
+## 2026-11-17 — #249 source-only safe positive two-shop fixture constraints from actual DEV catalog
+- Read-only `pg_get_functiondef` verification: `retail_private.enqueue_new_job` inserts `job_outbox` **only for campaign status PLANNING** (and render status QUEUED). A synthetic `DRAFT` campaign **would not enqueue** under that current trigger, but the separate BEFORE INSERT `reserve_subscription_unit` trigger **still charges one quota reservation**, even for DRAFT; avoid implying cost-free fixtures. New synthetic `shops` bootstrap an OWNER membership, business profile and a seven-day trial; `shop_usage_reservations`, subscriptions, campaigns and days cascade on shop deletion. Critically `shops.owner_user_id` references Auth users **without cascade**, so owned shops must be deleted **before** deleting Auth identities. These are candidate reviewed cleanup boundaries, not approval for hosted data writes or evidence of full two-shop GET200/404. No DEV data modified in this catalog read.
+
+## 2026-11-17 — #249 HTTP pre-handler timing corroboration
+- Independently re-ran the protected existing **GET-only** original Flex transport-phase correlation [#40176054781](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40176054781): diagnostic job SUCCESS; **6/8** synthetic routes anomalous. Six samples completed DNS/TCP/TLS in approximately **0.64–0.65s**, then received **no HTTP first byte or handler marker within 20s** (curl exit 28). Other samples succeeded 401/marked 5.302s and unknown GET 404/1.219s. Aggregated host telemetry shows worker-start buckets, but no causal worker-to-request mapping; do not assert root cause or fix. Paired fresh original Flex route matrix 6/9 anomalous versus isolated Y1 40/40 + 12/12 after 240s idle. Original #249 OPEN.
+
+## 2026-11-17 — #249 live original-Flex vs isolated-Y1 ingress comparison and next GET parity source
+- Fresh protected read-only original Flex [#40100546239 **attempt 3**](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40100546239) showed **6/9 HTTP anomalies**: three signed-in-relevant read-status GET routes (render job, poster job, poster draft) and one poster-select POST plus unknown GET timed out at 18s without HTTP response or app marker; final campaign GET returned marked 401 only after **26.081s**. Success of diagnostic Actions run is not HTTP acceptance. In the different-hosting isolated Y1, [#42964811296 **attempt 3**](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42964811296) verified exact Y1/unchanged original FC1 and passed **40/40** health/unknown GET and **12/12** handler-marked missing-JWT GET401 across 240-second idle. No signed JWT or positive tenant API parity yet; #249 remains OPEN.
+- Opened source-only [PR #968](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/968) for exactly three previously failing read-only endpoint candidates under `ops/p0249-y1-readonly-extra-get`: render-job status, poster-job status, poster-draft status, each using original `HTTPAPI`, bounded per-origin JWT verifier, request-local caller-JWT `TenantStore`, original read adapters, and literal GET-only Python v1 manifests. A **separate second enable flag OFF by default** prevents activation from existing #939 trial settings. No deployment workflow/ZIP/frontend routing change, Azure/SQL/Auth mutation, PROD, GPU or WineShopPOS. Source exact-head CI and independent affected leads review required; staged source is not hosted capability.
+
+### 2026-11-17 — #249 staged Y1 read-status three-GET original signed two-shop offline tests
+- Source-only [PR #968](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/968) also adds `test_p0249_y1_extra_get_signed_two_shop.py`, exercising actual original RS256 JWT signature/issuer/audience/expiry and original `HTTPAPI`→`TenantStore`→three original read adapters with a synthetic two-shop PostgREST fake. Own-shop returns 200; intentionally leaked foreign upstream row must still become 404; revoking membership denies next GET; forged/expired/wrong-role token fails before database; all calls GET only and double flag defaults off. The latest PR Python/uv job passed with the fixture. This is **local cryptographic source integration**, not hosted Supabase signed/RLS proof, genuine data, or Y1 deployment; independent affected JWT/RLS/poster/render review and full final-head CI still required.
~~~~

### docs/WORK_LOG.md
~~~~diff
@@ -910,3 +910,68 @@ Work completed: #859 merged & postmerge 4/4, #866 merged (postmerge running), #8
 - [#962](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/962): surgical current-main port of #796 Unicode/invisible/bidi prompt control checks plus new negative tests and Hindi conjunct positive fixture, no model execution. Exact PR [#43713860334](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43713860334) **4/4 PASS**; merged `e9610ffd32e27b9c9dc02aac5770c0dec45fe080`; fresh main [#43714482943](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43714482943) **COMPLETED SUCCESS 4/4**. Old signed prompt CAS not ported.
 - Original #551 has 171 changed paths, previously 58 exact main blobs / 105 absent / 8 different, and stacked #848 has 82 changed filenames (66 absent, 16 different at earlier checkpoint); these are **file counts**, not feature completion. Recompare against moving main before next batch. GPU/provider/paid AI, Azure/SQL, PROD and WineShopPOS unchanged by this run.
 
+## 2026-11-15 — #249 code-first Y1 continuation checkpoint
+- Read current AGENTS and canonical docs/issue/PR state; verified original Flex #249 OPEN, Y1 hosted historical 40/40 HTTP and 12/12 negative-auth results, PR #939 open with zero independent reviews. Removed #939's unsafe push autoactivation; manual-only workflow + regression and scoped runbook updates committed on PR head `1f2ead12713e8d08fcb2eea5a5c1fef0cdd968f1`; [CI #43707648803](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43707648803) **4/4 PASS**, unmerged/unactivated.
+- Opened independent source-only [PR #954](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/954) for bounded existing JWKS reuse in Y1 shadow, fresh per-request TenantStore and offline cache partition tests. Diagnosed first Python CI failure as stale exact import-string assertion (1 failed vs 1390 passed); fixed packaging guard at branch head `a871c49403f6f154f6419ab876132a302ec22429`; final [PR CI #43708057346](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43708057346) **4/4 PASS**, squash-merged source PR #954 to main `9289fd792641a637c3cc23a93c88889016863ed8`; [fresh main #43708417378](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43708417378) COMPLETED SUCCESS **4/4**. No hosted Y1 activation. No Azure, Supabase data, PROD, paid GPU/AI or WineShopPOS modifications. Issue comment checkpoint #249 posted for traceability.
+- Follow-up: #939 branch source was merged forward onto main without dropping its six original changed Git blobs (merge commit `e8f5e16d3e4344eb1d4d997232e7598bf78ef8f9`), but remains **OPEN/unreviewed**; no workflow dispatch, appsetting activation, real JWT test or cutover occurred.
+
+## 2026-11-15 — #249 second code-first security pass
+- Original open #939 reconciled to modern main without source loss/force. Fixed DEV signed Auth admin helper: `sb_secret_` now uses only API-key header (per current Supabase docs), legacy JWT retains Bearer. Extended uncertain user-create ACK reconciliation from first 100 users to bounded 10-page exact synthetic-email cleanup, failing closed on malformed pagination or exhausted scan. Added offline regressions; the first current-main PR CI exposed a pre-existing string-based source guard rejecting the new explanatory comment, fixed the comment without removing that guard. Re-run latest exact PR CI before claiming 4/4. No real identities created, workflow dispatched or appsettings modified.
+- Read-only Supabase DEV metadata showed `campaigns` INSERT triggers job outbox and subscription reservation, so separate positive two-shop seeded campaigns cannot be considered safe without queue/budget isolation. Flag remains OFF, original Flex unchanged, PROD/WineShopPOS/GPU untouched; docs are in [PR #955](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/955).
+
+## 2026-11-15 — #249 resumed source bug and regression work
+- Re-read live #249, #939/#955 heads, exact root `function_app.py`, and current source test inventory. Found a real mismatch after #946: enabled Feature2 builder called undefined `SupabaseJWTVerifier` after the root import changed to `cached_supabase_verifier`. Opened source [PR #965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) with one-line fix plus offline execution-style tests for actual builder and Feature2 disabled fail-closed path. Initial Python CI #43733817178 had exactly one failed historical source-string assertion, not a runtime test failure; changed lazy-import test to inspect current AST security import, reran final-head CI. Shared root requires affected review. No Azure, Supabase data, GPU, paid AI, PROD or WineShopPOS operations.
+
+## 2026-11-17 — #249 continued current Y1 source cleanup hardening
+- Re-read live AGENTS and four canonical docs, source #939/#955/#965, and original issue #249. No recorded independent reviews, original Flex 503 still OPEN. Inspected existing two-user protected Auth trial and found that privileged deletion trusted a potentially mismatched created-account UUID and accepted weak marker prefixes. Amended **existing #939** (not duplicate PR) in `tests/e2e/p0249_dev_signed_jwt_read_once.py`: enforce exact synthetic marker, fresh GoTrue Admin GET with exact ID/email, deny mismatches before DELETE; and `tests/e2e/p0249_y1_signed_auth_shadow_once.py`: check initial Admin-create response email. Extended original `tests/infra/test_p0249_y1_real_signed_shadow_source.py` with positive/negative deletion, mismatched create and malformed marker cases, updated existing uncertain-ACK second-page fixture. Initial current code-head Python mandatory CI passed; require the latest exact head four checks before merge. Updated existing protected trial runbook with JWT non-revocation limitation.
+- No hosted GoTrue identities created or removed, Azure site/settings changed, actual hosted signed RLS test, Azure HTTP deployment, paid provider, GPU, PROD or WineShopPOS mutation. Protected PR #939 requires independent security/ops review. [#965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) source verifier fix remains separately review-gated (exact-head 4/4 passed). No false #249 DONE receipt.
+
+## 2026-11-17 — Issue #249 real source continuation: deny credential redirects
+- Continued existing Y1 protected Auth trial [PR #939](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/939) without creating another PR or cloud app. Original Python `urllib.request.urlopen` followed redirect responses by default despite initial allowlisted hosts; replaced it with explicit no-redirect openers in `tests/e2e/p0249_dev_signed_jwt_read_once.py`, `tests/e2e/p0249_y1_signed_auth_shadow_once.py` and `ops/p0249_y1_public_shadow_trial_guard.py`, plus synthetic redirect regressions in two existing infra test suites. Source head `58d27135e29bc997cf3204ff814c8691e1cc5230`; [CI #43997434346](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43997434346) Python/FFmpeg completed success at this checkpoint, other two jobs in progress.
+- No protected workflow dispatch, temporary public Y1 appsetting, real test-account mutation, signed hosted test, original Flex repair or tenant/queue/GPU/paid/PROD/WineShopPOS change; #249 remains OPEN. Existing security/ops review requirement remains unmet. The four-doc checkpoint is a reviewable source-only PR #955, **not** merged/main or hosted acceptance.
+
+## 2026-11-17 — Continued Issue #249: original JWT-backed PostgREST redirect hardening
+- Inspected source on live [PR #965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965), preserved existing optional Feature2 cached-verifier fix. Found `azure-functions/campaign-api/tenant_store.py` defaulted to redirect-following `urlopen`, exposing the original API's JWT-backed PostgREST calls to off-origin credential forwarding after a redirect. Added a fail-closed default no-redirect opener, `tests/infra/test_p0249_tenant_store_redirects.py` covering five redirect types and injected transport, and updated the original synthetic two-shop signed/RLS fixture to patch the safe opener. Source branch head `0a6828249a16110f19059899d14b79917a5b7668`; [CI #44000033699](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44000033699) Python, FFmpeg, Supabase succeeded as checked, frontend pending. Record exact final job status separately, not a fabricated pass.
+- This is source and disposable CI only; **no** Azure settings, deployment, synthetic Auth mutation, real signed user/tenant E2E, original pre-handler Flex 503 resolution, private media, queue, GPU/paid provider, PROD or WineShopPOS changes. Existing protected [#939](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/939), shared #965 and these canonical docs still need independent review; #249 OPEN.
+
+## 2026-11-17 — #249 additional original JWT reader defense-in-depth
+- Continued same existing [PR #965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) rather than creating duplicate source PRs. Tightened `TenantStore.__init__` to require strict complete HTTPS project origin; expanded `test_p0249_tenant_store_redirects.py` with invalid-host/URL negative cases and synthetic redirected POST assertions for exactly one original-host send (no auth replay to Location destination). Latest source head `4b75a0b2eb8cc8d77d5a4e710e22f6a8fda93d60`; [CI #44007592073](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44007592073) **NOT claimed green until four jobs verified**. Previous source head #44000033699 and previous docs #44000489172 each verified 4/4. #965, manual protected #939 and docs #955 remain under independent review, not merged/deployed. No Azure, Supabase hosted writes, GPU/paid model, PROD or WineShopPOS changes; Issue #249 stays OPEN.
+
+## 2026-11-17 — #249 original HTTPError socket/response close repair
+- Inspected [prior source exact-head CI #44007592073](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44007592073) Python log: 1,485 pytest passed and infra redirect unittest cases passed, but synthetic HTTPError redirects emitted resource warnings for unclosed response handles. Extended [#965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) original `TenantStore._request` catch to close errors on every branch, and added assertions that the 30x transport response is `.closed` after both GET and POST. Source head `5790d4fcd787800455707d58dafd82a953281fe4`; new [exact-head CI #44008226907](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44008226907) launched, status requires final verification. Previously source #44007592073 and docs #44007839043 each 4/4 succeeded, but are superseded for current heads. No Azure/Supabase writes, new cost, PROD or WineShopPOS; issue #249 stays OPEN pending protected hosted tests.
+
+## 2026-11-17 — #249 original elevated AdminStore security and test batch
+- Confirmed previous source [#965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) `5790d4fc` and docs [#955](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/955) `62a3cdf8` had exact-head 4/4 passed. Read original `AdminStore` and found its default urllib transport still followed redirects while carrying a privileged key, including mutations. Continued **same existing review-gated #965**, changed `admin_store.py` to validate HTTPS origin, deny redirects for privileged GET/POST and close `HTTPError` sockets while retaining injected/patchable transport, and added `tests/infra/test_p0249_admin_store_redirects.py` with synthetic no-network negative fixtures (legacy/opaque keys, 301–308, GET/POST, error cleanup). Latest source head `69758c5ccc3298f65c4dd59727d2d27f91adac08`; new [exact-head CI #44029160113](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44029160113) started, NOT claimed fully passed until verified. No Azure/Supabase live writes, cloud provisioning, GPU/paid inference, PROD or WineShopPOS; issue #249 still OPEN.
+
+## 2026-11-17 — #249 original JWKS failure classification (source-only)
+- Read current main and original Y1 shadow verifier/HTTPAPI integration. Confirmed `PyJWKClientConnectionError` is a subclass of broad JWT error handling and could turn a temporary public JWKS fetch outage into 401 even for otherwise valid signed retailer JWT, complicating #249 response attribution. Continued same existing reviewed [source #965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) and amended `security.py` + `http_api.py`: dedicated sanitized transient signing-key exception now maps to 503 and all invalid/missing/forged JWTs still map to 401 before tenant DB. New `tests/infra/test_p0249_jwks_outage_classification.py` uses original verifier/API with offline simulated JWKS connection and key-ID failures, no Supabase/merchant secrets. Source head `8a713825ce1aa6dde602d76e00f878ebb04dcbad`; [exact-head CI #44087947443](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44087947443) launched, pending final outcome at checkpoint. No DEV setting/deploy, Supabase account/DB mutation, GPU, paid model, PROD/WineShopPOS; Issue #249 OPEN, original ingress 503 unaddressed.
+
+### 2026-11-17 — #249 real shadow handler failure-path fixture
+- Extended existing original signed Y1 two-shop test `tests/infra/test_p0249_y1_signed_two_shop_transport.py`: test patches only external JWKS key-fetch with a synthetic connection outage, calls actual Y1 `campaign_read.main`, asserts marked 503 sanitized response, no tenant DB calls, and cleared verifier cache afterward. Source [#965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965) head `681ec17dee7a5a64a50f31c5b486c2f4cc8deedc`; [source CI #44088585523](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44088585523) pending final exact-head 4/4. Earlier `8a713825` 4/4 passed but superseded. No Azure changes/identity writes/GPU/PROD/WineShopPOS; Issue #249 OPEN.
+
+## 2026-11-17 — #249 current read-only host refresh plus signed idle code
+- Started existing approved Azure read-only Y1 2-route/240-second idle job **rerun** of #42964811296 and existing original Flex GET/POST route matrix **rerun** of #40100546239; both re-run commands accepted, later real HTTP statuses/attempt logs need inspection. No Azure/Supabase writes, workflow edits or deployments occurred.
+- Amended **existing protected PR #939**, not a duplicate: signed tester now rejects JWT exp within 360s before test, keeps two disposable tokens in memory only, waits exactly 240s without traffic after immediate JWT/forgery tests, rechecks both handler-marked 404s under 18s, and prints success only after both Admin UUID/email-verified cleanups. Added offline post-idle success/second-user failure cleanup and near-expiry negative tests, updated its existing trial runbook. Its manual-only DEV trial is still **unmerged and not dispatched**; no real JWTs were minted by this code-only step. Mandatory final 4/4 and independent security review gate outstanding. Original Flex P0 #249 remains OPEN.
+
+## 2026-11-17 — #249 read-only re-run completed with contrasting host evidence
+- Used existing already-merged reviewed protected Azure workflows only, no new privileged workflow: original Flex route-matrix #40100546239 rerun SUCCESS as diagnostic but **6/9 HTTP anomalies** (five 18-second markerless timeouts, and a 26.081s marked 401). Its DEV RG/site identity and HTTP function indexing passed. Existing isolated Y1 two-route idle check #42964811296 rerun SUCCESS: exact two GET functions, 20/20 first and 20/20 after 240s idle, no-JWT 6/6 and 6/6 handler-marked 401, unchanged original Flex FC1. Actual comparison establishes persistent original ingress trouble vs healthy limited Y1 no-JWT boundary in those samples, not signed tenant/API cutover.
+- Existing protected source PR #939 gained 240s signed two-user after-idle GET check, JWT expiry margin, mandatory exact two-account cleanup before PASS and failure regressions. Exact-head #44088736861 **4/4 PASS**; still unmerged with zero independent security reviews, and no real signed-user test dispatched. Reviewable four-doc PR #955 preserves all parallel feature history. No Azure settings/deploy, live Supabase Auth/shop/campaign changes, billable services, GPU, PROD or WineShopPOS changes.
+
+### 2026-11-17 — #249 original Feature2 verification outage follow-through
+- Reused [source PR #965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965); inspected actual `feature2_adapter.py` and `dispatch_feature2`. Found that newly distinguished original JWKS `SigningKeysUnavailable` propagated past Feature2's separate 401/503 handlers and would become generic 500 for signed trend GET, prompt preview POST, and private drafts GET. Added one import and three existing 503-handler branches, preserving codes and no JWT/RLS relaxation; expanded `test_p0249_jwks_outage_classification.py` to execute those original adapter methods with offline transient JWKS errors and zero data reads. Source head `63f5cbe4bbc3840b3ced6aeb60938976137782bc`, [CI #44089856853](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44089856853) pending exact final 4/4. Previous source `681ec17d` CI 4/4 passed, but is older. No Azure, database, GPU, paid model, PROD or WineShopPOS mutation; Issue #249 remains OPEN.
+
+## 2026-11-17 — #249 protected trial independent cleanup implementation
+- Discovered longer signed 240s idle test would extend the window for leaked Auth fixtures if the transient GitHub runner died. Implemented deterministic two-slot marker derivation from exact GH `GITHUB_RUN_ID`/`GITHUB_RUN_ATTEMPT`, added `cleanup-only` mode that reconciles only those two identities via exact bounded Admin lookup and UUID/email re-read. In the existing unmerged protected #939 workflow, its separate `independent-restore` job now attempts this reconciliation after Azure public-setting rollback even if that step fails. Added negative offline tests for invalid run/slot, valid two-slot reconstruction, partial cleanup failure and independent workflow binding. Whole-workflow cancellation still needs operator recovery. CI and review pending. No workflow dispatched, real users created, secret logged, Azure settings changed, paid providers/GPU, PROD or WineShopPOS mutations.
+
+## 2026-11-17 — #249 verified safe future two-shop test boundary without writes
+- Queried read-only DEV PostgreSQL catalog definitions for `enqueue_new_job`, `reserve_subscription_unit`, `bootstrap_shop`, `bootstrap_trial_subscription` and exact FK cascade constraints. Confirmed DRAFT skips outbox, but always reserves one synthetic trial unit; new shops bootstrap membership/profile/trial; shop deletion cascades campaigns/days/subscriptions/reservations while user deletion is blocked by non-cascading `shops.owner_user_id`. No test shop, campaign or Auth user was inserted or deleted. Recorded source-first separate fixture acceptance plan, independent review required, #939 remains Auth-only.
+
+## 2026-11-17 — #249 fresh original Flex low-level transport repeat
+- Re-ran existing main protected **read-only** Azure workflow #40176054781: successful telemetry capture; six of eight GET observations produced 20.0s curl timeout **after successful DNS/TCP/TLS** (TLS ~0.64–0.65s, no first byte/handler correlation marker). Successful samples returned 401 with app marker and unknown 404. Host worker-start aggregate buckets were present but not tied to individual failed request; causality still unproven. Previous same-day original Flex route matrix had 6/9 anomalies; isolated Y1 passed 40/40+12/12 after idle. No Azure resource/config/host changes, no Auth/SQL/media/customer writes; #249 remains OPEN.
+
+## 2026-11-17 — #249 real host ingress recheck, staged independent read-only status routes
+- Verified actual **successful observation** GitHub jobs: [original Flex #40100546239 attempt 3](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40100546239) had **6/9** no-token HTTP anomalies, including three status GETs timed out after 18s with no handler marker, unknown GET and poster-select POST 18s, final campaign GET 401 after 26.081s; [Y1 #42964811296 attempt 3](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42964811296) exactly indexed health+campaign GETs, **40/40 + 12/12** accepted over 240s idle. Both protected read-only reruns made **zero Azure configuration, app deployment, tenant or SQL writes**.
+- Continued actual source work as new independent [PR #968](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/968) instead of duplicating #939: stage three additional GET-only Python v1 route sources for render-job, poster-job and poster-draft status, original signed JWT/RLS per-request backend adapters, double off-by-default flag, strict UUID/GET and no privileged worker imports. Added eight offline regression cases (no Authorization, missing flags/config, wrong ID, hard-coded delegation, no JWT eager import, read constructors without admin/queue, GET-only binding, sanitized 405/500). Initial Python CI found only a test fixture UUID whose .upper() did nothing because it contained digits alone; corrected fixture to genuine hex-letter uppercase, preserving the negative. Final CI/review pending. No actual deployment, new Azure functions index, Supabase Auth/SQL media writes, paid services, GPU, PROD or WineShopPOS mutations. #249 remains OPEN.
+
+### 2026-11-17 — #249 add actual original JWT/RLS two-shop offline status-GET execution
+- In [PR #968](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/968), added five local-RSA-signed two-shop regressions under `tests/infra/test_p0249_y1_extra_get_signed_two_shop.py`. Actual project `SupabaseJWTVerifier` and `TenantStore` use a synthetic PostgREST transport that deliberately returns a foreign shop row; each of the three GET status adapters still must return 404 without current membership, return 200 for own shop, deny following revocation, reject wrong/expired/forged tokens before SQL and never issue a non-GET. The exact latest source Python job passed, while other required CI jobs remain to be checked on final head. No real Supabase Auth account, SQL row, Y1 setting, Azure ZIP, paid model, GPU, PROD or WineShopPOS changes. Original #249 OPEN.
~~~~

## Non-acceptance
Every original changed path can be reviewed here. Work still needed in newer live Issue #249 implementations #939/#965/#968/#995 with independent affected security/ops review; original ticket and signed two-shop + Azure hosted tests remain OPEN. No GPU, paid AI, cloud, PROD or WineShopPOS mutations.