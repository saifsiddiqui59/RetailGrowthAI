# RetailGrowthAI Feature #4 — Coordinator handoff (2026-10-26)

## Branch scope and current verified boundary

Branch: feat/feature4-professional-video-studio (based on main 140a9f8617). This is a first **implementation increment**, not Feature #4 completion or approval to change the shared API. PR #318 is an **unmerged draft architecture**.

Added:
- video-engine/professional.py: strict rg_video_v2 compiler producing a private HyperFrames HTML project from tenant-bound, trusted, staged, rights-approved media IDs. Supports text, image, poster, media and beat-grid synchronized modes as a **source contract** (15/30/60 seconds, 540/1080 portrait, 24/30 FPS), three styled templates, approved offer/title/CTA escaping, finite contiguous scenes, trim ranges, an authorized music ID, no raw customer HTML/CSS/JS/remote media.
- video-engine/audio_catalog.py and empty audio_catalog.json: operator-curated fail-closed rights/territory/platform/usage/expiry guard; no commercial music or SFX approved or bundled. This is a local policy gate, not a claim of third-party license review.
- video-engine/beat_grid.py: bounded CPU-only onset estimates for trusted PCM16 WAV (source must already pass backend audio authorization and FFmpeg normalization). This is approximate transient detection, not source-aware voice ducking or a professional rhythmic transcription.
- video-engine/hyperframes/: pinned versioned Node producer adapter with local MP4 render and ffprobe checks; no hosted API, no provisioning and no activation in Azure.
- frontend/src/features/video/{video-model.mjs, VideoStudio.jsx, VideoStudio.css}: isolated responsive video-specific draft editor, mode/template/media/music selectors, scene reordering, mobile storyboard mock, guarded render callback and signed output slot (not mounted into shared routes).
- tests/frontend/video-model.test.mjs: React-independent video plan controls and authorization-flag tests under existing frontend tests.
- tests/media/test_feature4_audio_catalog.py and test_feature4_beat_grid.py: offline rights restrictions and synthetic percussion timing.
- tests/media/test_feature4_professional.py: compiler authorization, modes, source-audio behavior and injection regressions under existing FFmpeg CI job.
- Legacy video-engine/render.py, queue/outbox, DB/Auth, React root app and Part 2/3 source all deliberately unchanged.

### Versioned proposed contract (coordinator approval required before live API integration)

```json
{
  "version": "rg_video_v2",
  "shop_id": "11111111-1111-4111-8111-111111111111",
  "mode": "image",
  "template": "cinematic",
  "duration_seconds": 15,
  "output": {"width": 1080, "height": 1920, "fps": 30},
  "scenes": [
    {"start": 0, "duration": 15, "asset_id": "approved_product_1", "headline": "THE NEW COLLECTION"}
  ],
  "cta": "Visit our store",
  "music_asset_id": null
}
```

Trusted backend creates separate server-staged manifest (shop_id and asset ID -> kind, relative file path, rights). A caller-supplied manifest is **not an authorization mechanism**. Server must resolve current tenant, verified rights, approved claims, idempotent job, quota and signed private output via existing services. For Feature #7 use this same v2 plan as a final renderer instruction: it supplies already approved timed inserts, while Feature #7 performs transcription/semantic timing independently. No alteration to docs/INTERFACES_V1.md in this worker branch.

### Offline usage (no cloud, when ffprobe installed)

```sh
python3 video-engine/professional.py --plan /trusted/plan.json --manifest /trusted/manifest.json --asset-root /trusted/assets --output-dir /tmp/new-empty-project
cd video-engine/hyperframes
npm install --ignore-scripts
node render.mjs /tmp/new-empty-project /tmp/validated-private-output.mp4
```

Producer integration follows current @hyperframes/producer 0.8.x JavaScript createRenderJob + executeRenderJob API. It has now been exercised in the actual isolated GitHub CI CPU producer render (see latest verified note below). Browser rendering may need template/time/clip/audio adjustments after actual output inspection. The CPU job must restrict network egress, process time, memory, concurrency, local scratch and private upload. Never execute arbitrary HTML or service secrets in the browser.

## Explicit pending work (not claimed complete)

1. **Real synthetic 30s HyperFrames/Chromium MP4 now verified on CI**, including six extracted frames, H264/AAC, exact 30.000 seconds and a deterministic synthetic source-tone preservation check. Still pending: actual approved retailer clothing and Feature #5 footage, 1080p/full 15/60s benchmarks, speech intelligibility, visual acceptance and reliable CPU/RSS/cloud unit pricing.
2. Improve three templates visually and verify real rendering behavior, not just HTML source/CSS. Improve true fade/audio duck automation and sound effects; source-only PCM16 beat-onset detection now exists, but real source-licensed mix, automatic binding to video plan and quality-checked beat sync remain outstanding.
3. Curate and individually audit license evidence for Mixkit/Pixabay assets including SaaS redistribution; currently there is **no third-party music bundled or cleared**. Audio requires a preapproved manifest.
4. Coordinator-approved v2 transport, central quotas/claim-fenced worker/private storage/subscription usage and Azure Container Apps Jobs cost gate. **Do not change shared APIs, migrations, Functions ingress or #249 settings without review.**
5. Feature #1 layout review, video-specific React editor, live status/preview/history/private signed download, review/save/approval, signed-in browser E2E, invalid media, job idempotency/timeouts/retries and tenant negative integration.
6. Three actual reviewable MP4 sample artifacts, four inspected green CI checks on the final PR, hosted DEV acceptance under separate approval. No hosted run, resource change, public API, production or WineShopPOS modifications here.

## License and references

HyperFrames upstream https://github.com/heygen-com/hyperframes LICENSE is Apache-2.0 (HeyGen 2026). Pin producer 0.8.185; verify its published package and transitive notices before deployment. FFmpeg remains the existing fallback. MoneyPrinterTurbo is only a reference; no code was copied. No Mixkit/Pixabay track was downloaded or granted rights by this PR.

## Coordinator document policy

AGENTS.md and docs/PARALLEL_WORK.md reserve docs/PROJECT_STATE.md, docs/NEXT_TASK.md, docs/DECISIONS.md, docs/WORK_LOG.md and docs/INTERFACES_V1.md to coordinator. Please update these upon accepting/integrating this branch; this feature-owned handoff avoids competing updates to shared tracking.

## 2026-10-26 — Additional cross-feature final Reel development

- Implemented private `creative_reel_v1` internal plan adapter (`video-engine/creative_contract.py`) for Feature #2 approved copy, Feature #3 image/poster assets, Feature #5 genuine clips or labelled still fallback, Feature #7 reviewed timeline flags and tenant-authorized shop branding/logo.
- A six-scene 30s Diwali composition contract is covered by `tests/media/test_feature4_cross_feature.py`: 0–3 brand, 3–10 fixture motion clip, 10–16 product image, 16–22 exact 20% offer/poster, 22–27 collection, 27–30 CTA. Test media is synthetic; no real AI human motion or licensed song was supplied.
- Extended `video-engine/professional.py` with authorized brand name/color/logo, poster overlays, timed SFX, bounded animation/transition presets and preserved source video audio metadata. Exact prices/offers must belong to the approved script.
- Added bounded backend-only `video-engine/render_adapter.py` for local compilation/private HyperFrames producer subprocess, 780-second maximum, video/AAC ffprobe validation, no-overwrite artifact publication and measured runtime. It does not authenticate HTTP, charge usage, enqueue, save jobs, upload or return signed URLs: existing coordinator-owned durable infrastructure remains authoritative.
- Added actual short synthetic H264/AAC output validation tests and cross-feature security/failure/regression cases. See `video-engine/CREATIVE_REEL_CONTRACT.md` for proposed additive v1 interface, provenance, fallback and coordinator integration conditions.
- Created an early separate synthetic FFmpeg concept reference **and subsequently rendered an actual 30-second 540x960 @24fps HyperFrames MP4 using synthetic clothing/logo/poster/short silhouette footage with original test music/SFX**. Sample is a technical + visual regression fixture, not genuine human AI-model footage or production grade quality.
- Canonical tracking docs and frozen public v1 APIs are coordinator-owned and deliberately unchanged by this worker PR. Azure ingress #249, Azure resources, PROD and WineShopPOS remain untouched.


## Real offline HyperFrames acceptance checkpoint — 2026-10-26

- Exact tested branch commit `a1ba3251a147a428c71562be98ae48047fffff61`: [GitHub Actions #40293681969](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40293681969) independently **4/4 SUCCESS** (media, Python, frontend and Supabase security jobs).
- `video-engine/hyperframes/ci-smoke.sh` generated the original illustrated Diwali 30s fixture, installed pinned producer in isolated media CI, actually executed CPU Chrome capture + H264/AAC encode, verified 540x960 at 24fps, **720 frames and 30.000s**, and uploaded original MP4 plus frames at 1/6/13/18/24/28 seconds as artifact [#12637372256](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40293681969/artifacts/12637372256) (3-day expiration).
- `check_feature4_output.py` passed scene contrast/diversity, and independently decoded produced MP4 audio: original synthetic 480Hz source-clip tone amplitude ~2039.78 at t=5s vs ~0.27 at t=12s. **This tests source-audio preservation, not real speech intelligibility**.
- Recorded end-to-end HyperFrames producer trace on `a1ba3251`: ~72s pipeline on Ubuntu GitHub Actions for 30s 540p. This is not the Azure Container Apps cost, memory benchmark, 1080p SLA, or paid provider estimate. No cloud deployment or paid resource creation.
- Six representative frames inspected; visually show logo, edited product, exact offer, clip motion and CTA. This fixture is original illustrated art, **not professional photorealistic fashion photography or real Feature #5 generated human motion**. The opening/logo and final poster safe-zone refinements are in newer commits and must separately pass full CI after modification; the earlier green evidence never certifies new commits.
- Remaining coordinator-controlled integration: actual Feature #2/#3/#5/#7 persisted signed assets, human-reviewed claims, one-charge fenced usage and job retries, signed output storage, retailer preview/download, React route ownership, GPU optional premium provider, standalone security audit/no-egress container, licensed music clearance, mobile acceptance, 15/60/1080p/per-video cost benchmarks, and robust hosted DEV E2E. Keep PR draft until integrated/accepted.

## 2026-10-26 — Owner review: earlier Diwali reference is too basic (visual redesign, not DoD)

Owner rejected the flat original illustrated scene cards as insufficiently professional. Feature #4 remains **visual-quality NOT ACCEPTED** despite working MP4, valid encoding and previous 4/4 CI. Do not call the synthetic fixture a production-grade fashion advertisement.

- Implemented separate editorial composition roles for opening brand reveal, full-frame video hero, product image reveal, prominent approved offer, and non-obscuring poster + CTA outro. Deterministic motion classes use only application-owned CSS and enum-gated presets; never accept tenant HTML or expression values. The editor now uses graceful serif headline styling for the cinematic template and preserves source footage.
- Real 30-second offline CPU HyperFrames sample from head `1e2e102b59c783c1b5db259f7d07466f086ee977` rendered with GitHub Actions [#40305558151](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40305558151) **4/4 SUCCESS**. [Artifact #12642087798](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40305558151/artifacts/12642087798) contains the original synthesized MP4 and six frames (retained temporarily). Security and authored exact "20% OFF" tests still pass. Actual 540x960 24fps 30s sample remains a low-fi synthetic test, not an acceptable retailer ad.
- Before/after visuals were manually inspected: scene-specific art direction and typography are stronger, original source clip is visible, discount is readable and poster footer is not obstructed. However the silhouette fixture still cannot demonstrate realistic fashion, real kurti texture, human walking motion or brand-accurate product representation.
- Next actual creative gate: obtain an **approved retailer kurti image/poster** from Feature #3 and real premium motion footage from Feature #5. Test them together in HyperFrames at 1080x1920; human-review full-frame playback, wardrobe fidelity, source audio, realistic motion, transitions and non-obscured safe zones. Never fabricate a real retailer product or mislabel animated image fallback as generative video.
- Keep feature PR draft and do not integrate into production until both actual media visual acceptance and coordinator-owned private queue/storage/download integration gates pass. No PROD, WineShopPOS or new Azure resource changes were made.

## 2026-10-26 — Full-resolution output verification and visual-quality release gate

- See [FEATURE4_VISUAL_ACCEPTANCE.md](FEATURE4_VISUAL_ACCEPTANCE.md) for the owner-rejected baseline, precise premium fashion requirements, and hard human-approval gate.
- Fixed the private compiler's `render-config.json` to include exact output width/height. The Node HyperFrames producer now rejects mismatched actual encoded dimensions, fps, pixel format, H.264/AAC codecs and duration, rather than merely checking aspect ratio.
- Extended synthetic CI fixtures with an actual second HyperFrames encode: `15 seconds / 1080×1920 / 24 fps`, with five editorial roles, motion-source audio, approved 20% offer and closing CTA. It probes final file via the independent `render_adapter.verify_mp4`, extracts real high-resolution frames and rejects visually blank or repeated-looking frames. The 30s/540p regression sample and the earlier real FFmpeg fallback remain untouched.
- Added offline unit coverage for exact 1080×1920 30fps project configuration and 60-second compiler acceptance, without pretending to have a 60-second production render.
- The real media artifact and full CI status must be checked from the most recent Feature #4 head run before claiming these new tests passed. No commercial-media quality acceptance is inferred from synthetic fixtures.

### Full 30-second 1080p source render and safe-zone verification (2026-10-26)
- Actual `30.000s / 1080x1920 / 24fps / yuv420p / H.264+AAC` output confirmed in GitHub Actions **4/4 success** at commit `e9f9f4673662a0a6505bf6bd4ea926abc6027bb3`: [run #40309070130](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40309070130). Result MP4 **5,616,633 bytes**; [synthetic evidence artifact #12644461146](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40309070130/artifacts/12644461146) (three-day retention). Both legacy 30s/540p voice/audio baseline and 30s/1080p art-direction samples passed.
- Human visual inspection of 5 extracted 1080p frames confirms the pipeline but **fails photorealism** (drawn, faceless test avatar / garment). A product-image lower-third overlap was observed and a CSS safe-zone refinement is included in the next source commit. No user-facing premium-fashion acceptance claimed.
- Feature-owned editor controls added for validated motion presets, slide/fade/cut transitions, and separate approved poster overlays. These and project notes require verification on the final PR head before coordinator merge.

## 2026-10-26 — Real 60-second Full-HD acceptance-stage render and worker seam

- **Verified 60-second real CPU HyperFrames output:** exact [GitHub Actions run #40318231205](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40318231205) succeeded 4/4, 81 media unit tests, MP4 output **60.000s / 1080×1920 / 24 fps / H.264+AAC / 9,219,022 bytes**. The 30s/540p and 30s/1080p regressions also passed. Synthetic artifact [#12648098245](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40318231205/artifacts/12648098245) contains six sampled one-minute frames. The full HD 60s producer encoded in approximately **4m 42s** on the GitHub CPU runner (from 11:57:06 to 12:01:48 UTC); this is not an Azure latency/cost benchmark.
- Reduce routine branch CI cost: the 60s/1080p test is retained with `FEATURE4_FULL_MINUTE_CI=1 bash video-engine/hyperframes/ci-smoke.sh` for release/full regression; the default job still exercises the verified 30s/540p, 30s/1080p and original FFmpeg fallback. Do not classify the deliberate 60s opt-in default as evidence that 60s source support was removed.
- New `video-engine/feature4_worker_handoff.py` is an **additive private queue worker seam** that requires trusted v2 claim, server-generated approved source manifest, tenant-private download through the existing `PrivateMedia` interface, source/MIME/license checks, <=36 media IDs, <=300MiB staged total, current token recheck before upload, and compare-and-set existing ledger finalization. It does **not** modify or deploy coordinator-owned Azure Functions or provision new queues/resources; backend callbacks are not yet implemented in existing admin store. Source-only mock regression suite: `tests/media/test_feature4_worker_handoff.py`.
- See [FEATURE4_AZURE_HANDOFF.md](FEATURE4_AZURE_HANDOFF.md) for precise callback and coordinator v1/v2 dispatch/ledger instructions. The public `instagram_reel_30s` API remains unchanged.
- Proposed scene-level music ducking now lowers *rights-cleared soundtrack* while original source-video audio is retained, then raises the bed for other scenes. A synthetic 293.66Hz probe is required to verify actual mix output. This is a deterministic scene-source-aware envelope, **not** live human speech/VAD transcription, SFX mastering, automated loudness normalization or proof of intelligibility. Verify newest head CI after audio source change.
- No approved retailer kurti, real Feature #5 AI-model inference, genuine Feature #3 photographic asset, private hosted v2 download, usage-ledger RPC migration, Azure DEV e2e or owner visual sign-off. Feature #4 PR remains **draft**.

## 2026-10-28 — Feature #3 / #5 inputs assumed available for integration testing (not a real delivery)

- Owner authorized Feature #4 to **proceed without waiting for real upstream media**. This means existing `creative_reel_v1` can be exercised using **synthetic, contract-compatible fixtures** representing a reviewed Feature #3 product image and Feature #5 motion clip. No live AI-human model footage, actual kurti fidelity, approved commerce rights or tenant-uploaded asset was received; do not present tests as production photorealism.
- Hardened `feature4_worker_handoff.py` to verify local renderer proof against the immutable approved request (job ID, idempotency, exact width/height/fps/duration, H.264/AAC, actual output bytes), and to **enforce exact `fallback_events` and `rendered_as` lineage**. A synthetic fallback must never be silently relabeled as realistic Feature #5 video. Additional source-only tests cover Feature #3 + Feature #5 combined manifest, malformed output proof, forged fallback labels and permitted still-fallback disclosure.
- Canonical docs, shared API/DB/RLS, Azure infrastructure and production flags stay coordinator-owned; continue retaining PR #322 as draft pending real footage and reviewer acceptance.

## 2026-10-28 — Frontend-to-Azure v2 source-only integration controller

- Added `frontend/src/features/video/video-transport.mjs`, an explicitly **disabled-by-default** authenticated API transport, and `VideoStudioConnected.jsx`, a Feature #4-owned integration bridge using the existing `useRetailAuth` JWT provider. This bridge accepts RLS-verified `shopId`, saved `campaignId`, approved script revision and coordinator-owned additive v2 route builders as inputs; no old v1 route is repurposed.
- Creates **one** POST intent (no retries on a lost acknowledgement), then GET-polls the specific job. All job receipts must include the exact active shop UUID, job UUID and valid state. Signed download links are validated for Supabase HTTPS origin, private bucket and exact shop/job/lease path. A changed shop, campaign or signed-in user clears job and signed URL. Bounded GET polling fails closed; no local mock is misrepresented as an actual generated video.
- `tests/frontend/video-transport.test.mjs` covers disabled mode, route/origin injection, JWT requests, no duplicate POST, job/shop mismatch, malicious signed URLs, invalid IDs and status safety. VideoStudio storyboard now displays a neutral media placeholder instead of abstract geometric shapes and retains an explicit non-rendered label. This has **not** been mounted in coordinator-owned `frontend/src/App.jsx`, has no live Azure v2 route, and does not imply Feature #3/#5 real assets are available.
- **Coordinator handoff:** mount `VideoStudioConnected` in the existing authenticated Feature #1 route with a server-selected authorized tenant, approved image/video asset rows, actual saved campaign and reviewed Feature #2 script revision. Provide RLS/JWT checked create/status/download paths implementing the exact response and private-path requirements in `video-transport.mjs`. Add versioned v2 DB preset/outbox/claim/lease/usage-ledger transaction and only then enable `enabled={true}` under a separate DEV deployment gate. No settings change or deployment was performed on this branch.

## 2026-10-28 — Source-only authenticated Azure HTTP adapter (coordinator handoff)

- New `video-engine/feature4_http_handoff.py` provides `Feature4HTTP.create/get/download` methods and is **not** a registered Azure function or deployed endpoint. It expects the existing HTTP layer to verify Supabase JWT; user-store callbacks recheck campaign ownership and shop membership. Source-only `tests/media/test_feature4_http_handoff.py` checks cross-tenant denial, malformed request rejection, derived idempotency, durable result receipts and private signed output lineage.
- The feature-owned browser `video-transport.mjs` and `VideoStudioConnected.jsx` consume those exact output shapes but are **disabled by default**. The coordinator must integrate route dispatch into `azure-functions/campaign-api/http_api.py`, queue trigger in `function_app.py`, and RLS-backed stores only after frozen v2 contract and plan/claim/ledger migration review. This branch never edits those coordinator files.
- The `admin.create_feature4_intent` callback is a REQUIRED **single atomic, DB-authorized transaction** to check actual approved Feature #2 script, shop-owned Feature #3/#5 media, immutable review revision, sufficient active quota and idempotency. The browser's `authorized` flags are never authoritative. If this callback is not implemented, the endpoint remains unavailable and cannot be advertised as working.
- Real authenticated hosted Azure E2E, API gateway issue #249 resolution and real photorealistic AI human motion remain explicit blockers.

## F4-02 — 28 October: strict approved storyboard-to-render translation

`video-engine/feature4_intent_compiler.py` now translates a `rg_video_v2` browser draft into the *existing* `creative_reel_v1` backend contract from a trusted immutable Feature2 approval snapshot. It refuses unreviewed offers/headlines/CTA, cross-shop or unlicensed Feature3 posters and Feature5 clips, claimed browser-provided origin/type, bad timing/format and unapproved beats. Only server-reviewed media IDs are included in the returned bundle. It reuses `feature4_worker_handoff._bundle` to enforce **the same actual Supabase private-bucket/rights/MIME/path validations used at worker claim time**. `tests/media/test_feature4_intent_compiler.py` covers combined F3 + F5, idempotent lineage, approved 60s still-only export and malicious inputs.

Coordinator's one atomic `create_feature4_intent` must supply frozen `snapshot` with shop, campaign, job, approved Feature2 script/brand, current reviewed media DB rows and idempotency key; call compiler *inside that transaction*, persist `result["bundle"]` and only then make existing usage reservation/outbox. This changes no HTTP route, DB migration or Azure runtime and **does not certify realistic AI motion**.

## 2026-10-28 — Visual release records (F4-10 source gate)

`video-engine/feature4_release_gate.py` is an additive **trusted-record-only** release eligibility validator. It denies still-animation fallbacks, test/unknown fixtures, missing real Feature3 product and Feature5 video references, expired/mismatched human review, any failed quality checklist, unapproved rights and non-Full-HD proof. `tests/media/test_feature4_release_gate.py` uses a **fake signed-off record solely to validate error handling**, not actual human approval. The coordinator must store and verify the owner/reviewer record against the immutable job and media ledger, then apply this gate before *commercial publication*. It must not trust a browser-supplied approval flag. No real human model footage is thereby produced or approved.

## 2026-10-28 — F4-04 verified same-shop source previews

`VideoStudioConnected.jsx` now sanitizes per-tenant Storage `preview_url` from authenticated `mediaAssets`, and `VideoStudio.jsx` independently checks active `shop_id`, Supabase HTTPS origin, signed `retailgrowth-media/{shop}/...` path and nonempty signature token before mounting approved image/poster thumbnails or native video clip players. Non-previewed media retains the neutral placeholder, and the UI explicitly states **SOURCE ASSET · FINAL REEL NOT RENDERED**. It never draws a geometric human, invents model imagery or loads public/foreign URLs. `tests/frontend/video-transport.test.mjs` adds negative cross-shop/origin/path/protocol tests. Actual signed source previews require coordinator provision of authenticated per-asset URLs; this code remains source-only and v2 default-off.

## 2026-10-28 — F4-15 editing execution / F4-08 runtime qualification handoff

- Feature #4's `feature4_edit_execution.py` accepts only independently persisted/reviewed Feature #7 shot ordering, duration, approved animation/transition and source-video trim/mute directives; a stale/foreign plan or new media/claim cannot bypass `feature4_intent_compiler.py` and existing tenant/private rights checks. This **executes** decisions but does not independently plan cinematic shots or run a multimodal model. [Exact code CI #40669534025](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40669534025) 4/4 and 111 media tests.
- [Current code CI #40672638751](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40672638751): 4/4, **117 media tests**, real synthetic Full-HD 30s MP4. New local HyperFrames runtime preflight checks Node >=22.12.0, pinned producer, Chromium Headless Shell and FFmpeg/FFprobe; observed GitHub sampled peak RSS ~1.77GB and render ~135s. Not Azure-hosted or customer media, no GPU or real AI vision.
- Final release depends on coordinator v2 route/DB/ledger/queue, signed DEV tenant E2E, actual retailer-approved original kurti/model assets, Feature #5 genuine walking video, Feature #7 real editing semantics and explicit human commercial review. The downloaded CI package lock is **not tracked in Git**, so `npm ci` reproducibility and transitive license review remain pending.

## 2026-10-28 — F4-16 professional open-source editor code adoption

Selected actual pinned MIT [Timeline Studio](https://github.com/MartinDelophy/ai-video-editor/tree/e1091feccca3be8832b507eb7e17c9e55eb2233a); source adaptation and file map [here](FEATURE4_TIMELINE_STUDIO_ADOPTION.md). Reused original timeline/clip/undo/redo/zoom/split/caption code instead of adding a second video renderer. User-facing React timeline contains scene, caption, licensed music and voice/SFX tracks, playhead/zoom, split/trim/reorder and undo/redo. Unsupported independent effects/gain are disabled. Feature2 creative package preview is strictly review-locked and not a server approval. New F2-to-F5 handoff is source-only and explicitly cannot run paid model inference. Original upstream's own CI at pinned commit passed lint, typecheck, build; original app was not locally launched. Current exact-head CI and future hosted/real licensed media QA must be observed separately.

## 2026-10-29 F4-04 duplicate renderer parity handoff

Stacked Feature4-only branch `feat/feature4-encoded-duplicate-parity-20261029` adds separately encoded 30s/540p synthetic duplicate of the genuine Timeline Studio JS action through the **same** trusted Python compiler and HyperFrames renderer, with SHA-linked four-point FFmpeg pixel-restart check and negative regressions. Split/reorder remains an independent unchanged regression. This is technical-only mock evidence; 31-task registry F4-04 remains IN PROGRESS until accepted coordinator main merge/postmerge CI, and private retailer quality/rights/live UI remain blocked. The coordinator, not this branch, owns shared docs, #650 packaging, Azure #249 and hosted integration. No paid service, GPU, PROD or WineShopPOS.
