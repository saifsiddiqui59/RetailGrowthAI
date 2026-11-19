# #249 historical PR #1002 four canonical documentation patches — 2026-11-19

- Original source PR https://github.com/saifsiddiqui59/RetailGrowthAI/pull/1002 pinned at exact head `a5f531aab5d448a22fc898d8d893f75a2f2e218b` (DRAFT, four shared canonical docs).
- **All four original changed-file GitHub patch hunks** are retained verbatim as historical input for a newer independent reviewer of #249 Y1 five-GET rollout. This archive is **not** a merged update to `docs/PROJECT_STATE.md`, `docs/NEXT_TASK.md`, `docs/DECISIONS.md`, or `docs/WORK_LOG.md`. Current main canonical docs stay untouched. The separate reviewed integration docs #1007 remain active.
- No Y1 deploy, original Flex markerless 503 cure, signed two-shop JWT/RLS hosted acceptance, public write route, automatic cloud cost, GPU, PROD or WineShopPOS is authorized. Original issue #249 and protected Y1 route/rollout reviews remain OPEN.

## docs/DECISIONS.md

~~~~diff
@@ -1130,3 +1130,12 @@ Owner direction to reuse original VoiceStudio code implemented with unchanged pi
 - Owner-requested integration of [#967](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/967) increased only the existing media CI cap from 15 to **25 minutes**, keeping all four required gates. [#977](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/977) adds a separately **manual-dispatch only**, read-only GitHub Actions 60s F4 source acceptance runner, with 25m overall / 18m render-step / 900s actual Node-command caps. No cron or automatic branch-push trigger remains after first proved smoke.
 - Actual branch smoke [#44261849124](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44261849124) completed SUCCESS (382 seconds job; H264/AAC Full-HD source-only synthetic proof). Uploaded receipt JSON only, not media/customer rights. Allow no GPU, Azure/Supabase, paid model, production or WineShopPOS use; record actual runtime not a minimum duration promise.
 - Preserve normal reviewed workflow policy: PR CI and fresh main CI are mandatory; independent human/affected-lead review is a governance follow-up because **neither #967 nor #977 has a recorded GitHub review**, despite owner-requested merges and no bypass of GitHub merge enforcement. CI success is not independent approval. This decision is about reproducible offline CPU testing, not F4 product release, customer speech/music licensing, source integration or hosted acceptance.
+
+
+## 2026-11-19 — #249 Y1 five-route protected release boundaries
+- Allow ONLY a manually dispatched, exact reviewed-main-SHA protected DEV workflow to alter the existing tagged Y1 code ZIP after verifying original FC1 unchanged, exactly two current indexed functions and absent public/shadow settings. Never tie Azure writes to push/PR merge.
+- Allowlist precisely five Python v1 GET-only manifests and unchanged original JWT/TenantStore/renderer/poster GET source. No root function_app, queues, timer, service-role, POST/PATCH or active API flags. Before attempting ZIP deploy, build and preserve a two-route fallback package; attempt same-run and independently protected rollback if acceptance fails.
+- Two-route rollback reproduces the proven route SHAPE using reviewed main source but cannot promise byte-identical historical hosted bytes, and cancellation or blocked approval may still need operator action. Protected anonymous/no-JWT GET probes are NOT positive signed two-shop RLS acceptance. No frontend cutover/#249 closure without independent review, live rights/tenant/POST/PATCH/media tests and measured latency. See #968/#995/#1001.
+
+### #249 five-route staging source identity — 2026-11-19
+- Source preflight must validate a **bounded snapshot and stage exactly those bytes**, not copy mutable paths a second time after validation. A race between checking `function.json` GET-only manifests and copying them could otherwise stage a POST/queue change that never passed the gate. Current #995 uses immutable byte snapshots, fail-closed per-file size, exact readback and negative regression tests (4/4 CI #44459814242). No external deployment, commercial approval, or production acceptance follows from this source-only security repair.
~~~~

## docs/NEXT_TASK.md

~~~~diff
@@ -1508,3 +1508,14 @@ Feature3 NEXT: verify main CI #41820799158, integrate reviewed 24-component sour
 3. F7 #513: reconcile 521-commit historical source branch against moving main by comparing unique approved source/test behavior; get independent auth/media review and exact-head + fresh-main tests. Do not wholesale overwrite current security.
 4. F3 #879/#880/#944: complete independent rights/tenant/auth review and dependency-order source reconciliation; keep offline 4/4 green separate from hosted acceptance. F2 #925/#848 remain separate protected work.
 5. F3/F4/F7 coding schedules may resume only for one **verified unclaimed original source/test defect**, not to idle-recheck green PRs. The hourly health monitor owns real run duration and lease reporting; **do not promise longer ChatGPT AI execution**. The extended CPU workflow runs only on manual GitHub Actions dispatch, at most 25 minutes per job; avoid unnecessary repeat minute usage. No Codex requirement, GPU or paid inference.
+
+
+## 2026-11-19 — #249 Y1 five GET replacement follow-through
+1. Preserve original Flex FC1 and two currently hosted Y1 GET routes. Compare actual original Flex latency to Y1 without claiming that source-only Y1 route code fixes original markerless 503.
+2. Obtain independent affected JWT/RLS/render/poster/Azure ops review and exact-head four-job CI for parent [#968](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/968), staging [#995](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/995) (4/4 green), and protected release [#1001](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/1001). Integrate parent before stacked children, retaining latest main source.
+3. Only on independent review and explicit protected DEV manual dispatch against exact reviewed main SHA, test five GET-only Y1 indexing, two 20/20 anonymous health windows 240 seconds apart, handler-marked 401 for the four original JWT GETs, and unchanged original FC1. Verify two-route rollback on failure; manual verification still needed after canceled/blocked runs. No settings, frontend, queue/timer or original Flex mutation.
+4. Complete separately reviewed real signed Auth-only trial [#939](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/939), safe no-worker two-shop RLS fixtures with cleanup (campaign/shop insert triggers can enqueue work/reserve subscription units), original POST/PATCH/private media, and measured p95/p99 before Y1 cutover or closing #249.
+
+### #249 Y1 after #995 TOCTOU fix — 2026-11-19
+1. Preserve #995 exact-head `aad2c453b490e97721624a89a76a8ac6097a9073`, [#44459814242](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44459814242) 4/4 PASS; check the new stage source bytes regression, size limit, and authorization independently. This is **source-only** and still stacked on #968.
+2. Continue the reviewed order #965 original auth/JWKS security, #968 three GET handlers, #995 staged source, #1001 protected build/rollback, #1002 docs. Protected signed two-shop DEV check, published rights and real p95/p99 observations remain separate blockers; never bypass manual owner approval to deploy.
~~~~

## docs/PROJECT_STATE.md

~~~~diff
@@ -1498,3 +1498,12 @@ Feature3 verified source-integration checkpoint:
 - PR [#977](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/977) merged to main `cb36c7dac8f6d2ec747685f0d668d1a5cd43c144`. New `.github/workflows/retailgrowthai-f4-extended-cpu.yml` is **manual `workflow_dispatch` only**, read-only, CPU-only, max 25-minute job. Source-run [#44261849124](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44261849124) passed an actual 382-second (6m22s) synthetic 60s/1080x1920/24fps H.264/AAC encode with hash/JSON receipt, not a customer or hosted demonstration. Latest-head PR CI [#44374499610](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44374499610) passed all 4. Postmerge main CI [#44375688944](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44375688944) **completed 4/4 PASS** on exact merge SHA `cb36c7dac8f6d2ec747685f0d668d1a5cd43c144`; this is source/CI integration, not commercial acceptance.
 - **Do not confuse runtimes:** existing ChatGPT coding automations still run for tens of seconds and do not have a configurable duration floor; GitHub Actions CPU test ran 382 seconds. F3/F4/F7 coding automations were paused because their original next work is security/visual/integration review-blocked, not because the CI runner lacks CPU time. Human visual quality, original commercial rights, signed DEV tenant flows, main conflict reconciliation and Feature4 acceptance remain incomplete. No Azure or Supabase deployment, paid model, GPU, PROD or WineShopPOS mutation.
 - Both shared workflow PRs were merged on the owner-requested integration path with passing CI, but **no independent GitHub review is recorded**; human/affected-lead review remains a governance follow-up. No branch protections were bypassed by tool.
+
+
+## 2026-11-19 — Issue #249 Y1 five-GET source release prepared; no deployment
+- Original Flex FC1 gateway 503/latency remains unresolved. Separate tagged Linux Y1 still has ONLY TWO indexed GET routes, with hosted 40/40 anonymous health/unknown GET and 12/12 handler-marked no-JWT 401 over two 240s-separated windows (protected Azure #42964811296). This is not hosted signed two-shop RLS.
+- [#968](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/968) (source-only, unmerged) adds three original JWT/RLS status GET handlers. Stacked [#995](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/995) introduces exact five-route fail-closed source staging/tests, with [exact-head CI #44375583051](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44375583051) completed success 4/4.
+- Stacked draft [#1001](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/1001) adds source-only two-route rollback build and an explicitly manual, protected reviewed-SHA five-route ZIP release and rollback workflow. NOT merged/dispatched/deployed here. No authenticated hosted positive JWT, original API POST/PATCH/private media migration or frontend cutover. Independent shared ops/JWT/RLS review mandatory. #249 OPEN. No DEV cloud/Auth/SQL/PROD/GPU/WineShopPOS writes.
+
+### #249 five-route source staging hardening — 2026-11-19 follow-up
+- Stacked #995 advanced from `b0bfd329a8a53c7cfab8a21754c01a7d1fe9dce8` to **`aad2c453b490e97721624a89a76a8ac6097a9073`**. Original preflight validated GET manifests then re-read live source during copy, allowing a source swap (e.g. POST handler) between validation and staging. The script now captures bounded validated bytes once and stages only that immutable in-memory snapshot; added a post-preflight malicious-method swap regression and a >2 MiB source rejection. Latest exact-head [#44459814242](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44459814242) completed **4/4 PASS**. #995 remains stacked on unmerged #968 and must NOT trigger a Y1 deployment or a claim of signed hosted acceptance.
~~~~

## docs/WORK_LOG.md

~~~~diff
@@ -911,3 +911,12 @@ Work completed: #859 merged & postmerge 4/4, #866 merged (postmerge running), #8
 - Original #551 has 171 changed paths, previously 58 exact main blobs / 105 absent / 8 different, and stacked #848 has 82 changed filenames (66 absent, 16 different at earlier checkpoint); these are **file counts**, not feature completion. Recompare against moving main before next batch. GPU/provider/paid AI, Azure/SQL, PROD and WineShopPOS unchanged by this run.
 
 - 2026-11-18 UTC / 2026-11-19 IST — Implemented non-Codex longer **GitHub Actions CPU** verification while keeping original ChatGPT scheduler runtime honest. PR #967 (`.github/workflows/frontend-bootstrap.yml`, video timeout 15→25min) exact-head CI #44000894199 4/4 PASS; merged to main `2bb2613c786f36de8cd0357a3f1fa32bbcb5b1ad`; fresh main CI #44374847280 4/4 PASS. PR #977 (manual-only `.github/workflows/retailgrowthai-f4-extended-cpu.yml`, docs) latest-head CI #44374499610 4/4 PASS; merged to main `cb36c7dac8f6d2ec747685f0d668d1a5cd43c144`. Real CPU native-minute smoke #44261849124 PASSED (382s) with source hash, 60s 1080×1920 H264/AAC and tiny proof artifact; two earlier setup retries failed from missing FFmpeg then Pillow and were fixed without skipping gates. Second merged-main four-job run #44375688944 independently verified **4/4 PASS** on `cb36c7dac8f6d2ec747685f0d668d1a5cd43c144`. Both shared-workflow PRs had no recorded independent GitHub review, so follow-up review remains; no feature accepted or product launched. Existing ChatGPT schedules still measured in seconds; F3/F4/F7 paused for verified review/integration blockers. No GPU, paid model, Azure/Supabase deployments, PROD or WineShopPOS changes.
+
+
+## 2026-11-19 — #249 Y1 release development checkpoint
+- Confirmed Issue #249 OPEN; original Flex intermittent markerless 503/timeout unresolved, separate Y1 two-route 240s idle 40/40 +12/12 live negative auth proof. No signed positive 2-shop RLS.
+- Implemented fail-closed exact-five-GET source PR [#995](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/995), original JWT/tenant/render/poster module copying, POST/queue/timer/pin/manifest/symlink protection and offline tests. Head b0bfd329a8a53c7cfab8a21754c01a7d1fe9dce8, [CI #44375583051](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44375583051) four jobs passed. Superseded CI-inert #994 closed unmerged.
+- Opened stacked draft [#1001](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/1001) with two-route rollback package, pinned Python3.12 vendoring, reviewed-SHA/manual-only protected five-GET deployment workflow, exact function indexes, immediate/240s idle HTTP and independent recovery. Detailed source handoff: docs/part1/P0249_Y1_FIVE_GET_RELEASE_20261119.md. Source only; exact-head CI and reviews required, no Azure, Auth, SQL, GPU, PROD or WineShopPOS actions.
+
+### 2026-11-19 — Issue #249 #995 preflight/copy race corrected
+- Committed source fix `602c49ecbe0bb394395af0b485ec75ad23d750e1` and regression tests `aad2c453b490e97721624a89a76a8ac6097a9073` on stacked original #995. The staging loop now saves 22 bounded original Python/JSON/requirements byte snapshots, validates GET-only route manifests and pins once, then writes **only those validated byte copies**. Regression mutates a render GET source to POST after preflight but confirms staged output still has the validated GET, and tests reject oversized module input. Latest exact-head push [#44459814242](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44459814242) verified **4/4 PASS**. #995 and parent #968 still open; independent JWT/RLS/ops review + protected Y1 release/rollback is pending; no Azure, PROD, SQL, GPU, paid inference or WineShopPOS changes.
~~~~

