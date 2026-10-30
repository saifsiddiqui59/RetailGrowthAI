# Feature #3 — AI Poster Studio source handoff (2026-10-26)

Branch: `feat/feature3-ai-poster-studio` (coordinator reviews/merges PR). This
handoff deliberately lives under Feature 3 ownership, not coordinator-owned
`docs/**`, `supabase/**`, API routes, CI workflows or shared dependencies.

## Latest main verified

- Existing `PosterStudio.jsx` local 3-template PNG preview/consent/download,
  registered-media v1 private draft, render polling, short-lived signed download,
  saved poster history/reopen, banner selection all already exist. **Do not
  overwrite or replace these**.
- Existing `poster-engine/render.py` Pillow exporter supports square/portrait,
  three approved v1 templates and only staged rights-validated media.
- Existing `poster_worker.py` uses private materialization, DB-fenced leases,
  immutable output paths and RLS-aware product ownership. The new contract is
  NOT silently sent to those v1 routes or persisted in v1 SQL.
- GitHub PR #318 is an open **video-architecture** PR (HyperFrames). It does not
  authorize a new poster media API or dependency changes.
- Azure #249 remains OPEN: intermittent Functions HTTP gateway-origin 503;
  real DEV poster worker generated private 1080x1350 PNG successfully, but
  signed-in `select` hosted canary is not reliably complete.

## Added and verifiable in this branch

- `studio_v2.py`: deterministic CPU text-to-poster and authorized
  image-to-poster; versioned allowlisted layered JSON; 10 retail intent
  classifications; Instagram square/portrait/story sizes; Pillow raster;
  strict bytes/path/rights/tenant reuse from legacy `_asset`.
- `animate_v2.py`: static layers -> CPU animated flashing offer GIF/MP4,
  exact visible words from approved offer only; capped frames/duration and
  FFmpeg timeout. **No Hunyuan/GPU required**.
- `ai_providers_v2.py`: versioned capability/status and strongly gated
  provider runner injection; FLUX.2 Klein 4B, FASHN VTON 1.5, rembg
  definitions. Disabled by default; no weights, CUDA, network or paid APIs.
  Runner/output writer always live outside Azure HTTP Functions.
- `frontend/src/features/creative/feature3-design.mjs`: same schema and
  immutable 25-step undo/redo/layer reordering and validation.
- `Feature3KonvaEditor.jsx`: not mounted until the coordinator approves
  `react-konva`/`konva` package pins and browser/server text/image parity,
  v2 save-version backend and tenant-verified media preview image supply.
  No unreviewed change to coordinator-owned frontend package files.
- New synthetic tests exercise prompt->layout, no fabricated offer,
  PNG, cross-tenant and unauthorized image denial, provider gates,
  GIF/MP4, version/schema and browser undo/redo.
- `sample_feature3.py` generates four clearly marked **synthetic/non-AI**
  evidence outputs (retail garment PNG, text-only PNG, flashing discount GIF,
  flashing discount MP4). The media test populates `ci-artifacts/feature3/`
  for the existing CI artifact upload; it is not a real fashion model or try-on.

## P0/P1 gaps before product-ready or hosted demo

1. Coordinator add additive `poster_design_v2` JSONB versioned persistence
   migration, RLS/RPC, history/idempotency, private export storage and
   source-revision-preserving approved variations, with negative SQL tests.
   Old v1 API must remain compatible. Freeze shared contracts first.
2. Pin compatible `react-konva` and `konva` in coordinator-owned
   `frontend/package.json` (React 19.3 already present), mount editor
   only behind a v2 feature flag and validate visual parity with Pillow,
   mobile E2E and secure private shop media. Export must not silently
   differ from preview. Add explicit approved asset selector, text-to-poster
   UI, draft-save endpoint, image-to-poster UX and template visual review.
3. Add tenant-checked queue claims, usage once-per-idempotent-job, max two
   paid retries, readback on uncertain HTTP 503, cost/seconds accounting,
   provider audit/rights version, private immutable synthetic outputs.
   Do not execute model in Function HTTP process.
4. Virtual try-on requires real *licensed* parser replacement or a
   commercial clearance and real garment comparison review. Current
   contract is MOCK/disabled; synthetic fixtures are NOT inference.
   FLUX 4B adapter has no deployed weights/real inference.
5. Real browser/auth/cloud E2E, caption/offer writer Feature 2
   handoff, backend preview/export parity, annotated visual acceptance,
   rate limits, accessibility, rights review and all four latest CI jobs.

## Third-party license gates (verify release tags and weight licenses before deploy)

- [FLUX.2 Klein 4B](https://github.com/black-forest-labs/flux2):
  the 4B distilled/Base rows say Apache-2.0; **9B and dev are
  non-commercial**. Selected FLUX source/weights not installed.
- [FASHN VTON v1.5](https://github.com/fashn-AI/fashn-vton-1.5):
  Apache-2.0 core/weights; default `fashn-human-parser` inherits
  [NVIDIA restrictions](https://github.com/fashn-AI/fashn-human-parser).
  **Do not run unchanged pipeline commercially**.
- [react-konva](https://github.com/konvajs/react-konva): MIT;
  [Pillow](https://github.com/python-pillow/Pillow): open-source HPND-compatible;
  [rembg](https://github.com/danielgatis/rembg): MIT library,
  **not automatic permission for its default BRIA weights**.
  No rembg models downloaded or automatically selected.

## Illustrative unit economics — assumptions, NOT Azure quotes or benchmarks

`total cost = (active GPU seconds + billable boot seconds)/3600 * quoted USD/hr
+ CPU seconds/3600 * quoted CPU USD/hr + storage/egress/retry costs`.
Cloud startup/idle and rights review can dominate single-poster costs.

| Scenario | Illustrative assumption | Estimate (USD per job, excluding storage/egress) |
| --- | --- | --- |
| Basic Pillow PNG | 3 CPU-s at hypothetical $0.10/CPU-h | $0.00008 |
| FLUX 4B image | 20 GPU-s at hypothetical $1.50/GPU-h | $0.0083, plus boot |
| FASHN try-on | 30 GPU-s at hypothetical $1.50/GPU-h | $0.0125, plus boot |
| Full AI fashion poster | FLUX+try-on+3s CPU | $0.0209, plus boot |
| Hunyuan video | 180 GPU-s at hypothetical $3/GPU-h | $0.15, plus boot |
| GPU boot sensitivity | extra 90s at $1.50/GPU-h | **+$0.0375 per cold job** |

For **1,000 monthly posters**, 80% CPU-only, 15% FLUX and 5% VTON,
illustrative *active compute* is around $2; if every 200 AI requests
requires a 90s cold boot at $1.50/h, add $7.50. These are algebraic
scenarios, NOT real Azure rates, and exclude storage, network, inference
latency variance, retries, model warmup, min billing increments and taxes.
Before any GPU: obtain Central India/East US *actual SKU availability,
quotas, regional prices, measured cold-start+inference*, monthly ceilings
and privacy/data-egress approval. No paid deployment authorized.

## Coordinator handoff for canonical docs

When integrating, coordinator to append verified PR/CI evidence and the v2
contract/license state to `docs/PROJECT_STATE.md`,
`docs/NEXT_TASK.md`, `docs/DECISIONS.md`, `docs/WORK_LOG.md`,
and revise `docs/INTERFACES_V1.md`/`docs/PARALLEL_WORK.md` only
after coordinated API/schema ownership review. The feature branch must
NOT directly alter those shared contracts. Keep #249 as distinct P0.

## 2026-10-26 — Continued implementation beyond initial PR checkpoint

- **Animation effects expanded (CPU only):** `animate_v2.py` now accepts
  allowlisted `flash`, `pulse`, `fade`, `slide`, `zoom`, `sparkle`,
  `reveal` (up to three concurrently, max 60 frames, max four seconds,
  bounded FFmpeg process, no untrusted filter expressions). The saved design
  is not overwritten. Exact approved promotional text remains server-rendered
  through Pillow, not a generative model.
- **Deterministic text protection:** `studio_v2.py` now shrinks and wraps
  each text layer to fit; it throws rather than silently trimming approved
  prices, offers, SKUs, conditions or calls-to-action. Tests include
  impossible clipping limits.
- **Fashion image review:** `garment_review_v2.py` produces a private
  authorized original-vs-try-on review sheet and validates explicit human
  checks for colour, pattern, neckline, sleeves, length and embroidery.
  It never auto-approves publishing. Synthetic fixture comparison is explicitly
  labeled unverified, not actual VTON model output.
- **Browser/server contract:** `feature3-compose.mjs` mirrors the
  CPU-Pillow composition contract; tests compare exact JSON across Node and
  Python. Authorized source IDs are required by browser composition, with
  server-side RLS/rights checks still mandatory for final rendering.
- **Editor surface:** React Konva source now supports add/remove image/text/
  promotional badge, replace registered private product photos, cover-crop
  product placement, layer reorder, transforms, undo/redo and local JSON
  download/reopen after shop/asset checks. Editor is still deliberately
  *unmounted*; coordinator must pin npm dependencies and deliver auth-scoped
  v2 persistence + visual parity.
- **Provider-cost hardening:** No configured/verified hourly GPU rate or
  per-job ceiling means provider remains disabled even if an operator flips
  a GPU switch. Enabled runners require transactional tenant-scoped usage
  reservation/finalization callbacks, a verified single-frame PNG under
  25 MB and bounded execution. These callback interfaces are not a
  deployed Supabase ledger yet; coordinator must implement actual claims,
  quotas and usage RPCs before enabling any inference.
- **Feature #2 approval sidecar:** `content_bridge_v2.py` rejects
  unapproved versions, wrong shop/campaign/day, unauthorized asset IDs
  and incomplete business brand kit. It only uses approved offers; a free
  prompt saying "80% OFF" does not create a discount. It is a source-only
  adapter until coordinator integrates feature-owned Part 2 and 3 interfaces.
- **Offline fixtures and proof:** five synthetic/non-AI sample assets via
  `sample_feature3.py`: retail PNG, text-only PNG, flashing GIF/MP4,
  unverified garment side-by-side review sheet. Exact newest four-job CI
  run must still be verified on the final head before review/merge.
- **Shared integration tracked:** [coordinator issue #325](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/325).
  No shared migration, backend route, global npm file or coordinator docs
  were edited on this branch.

### Current public-source license and region findings (not billable approval)

- Official [FLUX.2 repository](https://github.com/black-forest-labs/flux2)
  explicitly lists *Klein 4B* and *4B Base* Apache-2.0; 9B and dev carry
  noncommercial terms. Use exact 4B snapshot only after dependency/weights
  audit, no automatic HuggingFace code loading from browser or Azure HTTP app.
- [FASHN VTON 1.5](https://github.com/fashn-AI/fashn-vton-1.5)
  lists `fashn-human-parser` as third-party, downloaded at first run.
  Continue to block unmodified parser for commercial use.
- [rembg README](https://github.com/danielgatis/rembg)
  states current default BRIA RMBG-2.0 weights require a paid agreement for
  commercial use. The rembg MIT source license alone is NOT sufficient.
- [Microsoft serverless GPU region table](https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview)
  lists **Central India: T4 supported, A100 not supported**; **East US:
  both T4 and A100 supported**. Consumption GPU billing is per-second with
  scale-to-zero, but container boot/warmup and CPU/RAM can cost extra.
  The [public price page](https://azure.microsoft.com/en-in/pricing/details/container-apps/)
  does not expose a reliable numeric regional rate in unauthenticated text
  (rendered placeholders). Cost scenarios above are **NOT quotes**. Acquire
  subscription-specific quote, region privacy approval, max monthly rupee
  ceiling and measured startup before any paid GPU activation.

### Final CPU/UI continuation checkpoint (source only)

- Added optional **registered shop logo** to Python and browser v2
  composition, with top-right alpha-preserving contain-fit instead of
  distorting/cropping logos. Feature #2 approved bridge may pass a verified
  brand-kit `logo_asset_id`. Legacy Part 1 API and its poster format
  are unchanged.
- Added deterministic visual uniqueness checks for all 10 actual Pillow
  raster templates, end-to-end JS/Python structured parity tests, private
  logo rights negative tests, and seven animation effect regression cases.
- `Feature3KonvaEditor.jsx` is syntactically testable via the existing
  Vite JSX transformer, but this is not a true React rendering/mobility
  acceptance until the coordinator pins/installs Konva and mounts it.
- Optional GPU license/cost/usage integration remains OFF. Do not
  characterize fixture-backed output as a live fashion model, live FLUX or
  real garment try-on.

## 2026-10-26 — Resumed worker and persistence implementation (after PR #321 review-ready)

Following the user's request to continue all independent work, committed:

- `render_workflow_v2.py`: **working offline CPU queue-worker execution**
  against injected durable claim, authenticated media staging, immutable private
  upload, completion and failure callbacks. Verifies full shop/campaign/day/
  draft/job UUIDs, frozen design SHA-256, revision, bounded retries (3 attempts),
  safe opaque `shops/{shop_id}/posters-v2/{job_id}/{fingerprint}.{format}` key,
  file/CPU limits, rights recheck on each attempt, object receipt, and cleanup.
  Tests render real Pillow PNG, GIF and FFmpeg MP4 into synthetic private media
  mocks. **Not yet registered as live Azure Function/queue trigger.**
- `persistence_contract_v2.py`: **versioned draft revision seam** requiring
  trusted JWT-derived member role/campaign/day, matching shop, fresh approved
  asset references, frozen design hash, optimistic compare-and-swap and
  immutable new-ID variation instead of overwriting an approved poster.
  Negative tests cover stale revision, wrong shop/lineage, revoked rights,
  approved overwrite and ambiguous storage acknowledgements.
  **Not a Postgres migration or a deployed save endpoint.**
- `studio_v2.py` corrected product alpha compositing: transparent
  merchant-owned garment cutouts now preserve original product colours and
  the authorized branded canvas background, without losing the PNG alpha.
  Tested with a deliberately transparent synthetic product image.
- Verified upstream FASHN 1.5 pipeline source at
  `src/fashn_vton/pipeline.py`: constructor calls `_setup_hp_model()`,
  and `__call__()` calls `self.hp_model.predict` on BOTH the person and
  garment; this happens even when `segmentation_free=True`. Therefore
  **segmentation_free does not bypass its restricted parser**. Commercial
  inference remains disabled until a fully patched dependency path and
  approved replacement parser/pose model license review are verified.
- Unit/media CI tests run on branch commits. The coordinator still needs
  to integrate audited atomic Supabase RPCs, private writer/authz, v2 router,
  real Konva dependency pins/mount and hosted Azure end-to-end signed tests.
  See [coordination issue #325](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/325).

**Cost and commercial rights:** No paid GPU, storage, external inference
service or model snapshot was provisioned/charged by these changes.
Existing illustrative estimates are not an Azure quote. Real FLUX/Hunyuan
output and real FASHN inference remain **unverified/unavailable**.

**CI:** The exact latest PR-head SHA and 4/4 job evidence must be verified
after all continuation commits. Earlier run #40291353845 applies to the
previous baseline only.

### Feature-owned creation UI, after worker checkpoint

- `frontend/src/features/creative/Feature3StudioPanel.jsx` now supplies an
  isolated, responsive and keyboard-accessible **Text-to-Poster /
  Image-to-Poster** creator: prompt, mode, source image, auto or selected
  retail template and Instagram format, then the versioned Konva editor.
  It supports approved business colours and optional logo, distinguishes
  source-authorized images from user-entered URLs, and never turns a
  prompt-mentioned discount into an offer unless approved copy is supplied.
- The new panel is **source implementation, NOT a mounted SaaS screen**.
  The connected host must supply only verified tenant/brand/media/approved
  content and must revalidate all fields at the server before saving or
  rendering. The coordinator pins/install `react-konva` and `konva`,
  mounts the route, implements secure v2 draft RPC and runs real browser E2E.
- Added isolated Vite JSX transform/approval-path tests. These do NOT
  replace Playwright mobile or snapshot parity acceptance.

## 2026-10-26 — Latest P0 source completion: trustworthy preview, safe editing, CPU packshots

- `review_export_v2.py`: a **single authoritative full-size Pillow PNG**
  is rendered once, and the browser-review thumbnail is downsampled from its
  exact pixels, not separately re-typeset in browser JS. Both output files
  carry SHA-256 hashes; a frozen binary hash and shop/design digest must match
  before a separately authenticated reviewer can approve it. This helper
  does not sign, publish or upload assets. Visual discrepancy is intentionally
  blocked rather than silently accepted. Four negative/positive media tests
  verify review parity, hash tampering, rights revocation and file overwrites.
- `Feature3KonvaEditor.jsx`: rapid repeated layer changes now use a live
  history ref instead of a stale React closure, avoiding lost undo/redo state
  under batched updates. Adds a bounded ResizeObserver fallback for mobile
  and older browsers. Browser mounted/Playwright parity remains untested until
  the coordinator installs/pins Konva and mounts the component.
- `feature3-context.mjs` and `Feature3StudioPanel.jsx`: approved
  offers/brand inputs must match the exact authenticated
  **shop + campaign + day**, not just shop. Same-shop stale day and
  cross-tenant brand kits are discarded. Switching the selected day/shop
  suppresses previously composed edit panels before they can be saved
  against the new context. Browser fixture tests cover these denials.
- `cpu_background_v2.py`: optional, zero-GPU Pillow **flat-backdrop
  product cutout** for simple uniform packshots, with conservative corner
  colour rejection, bounded images, rights + tenant checks, alpha output,
  immutable file paths and mandatory manual review/registration. It is
  explicitly **not AI segmentation/rembg**, and is unsuitable for complex
  hairstyle/fabric/studio scenes. Negative fixture tests cover rejection,
  cross-tenant access, expired rights and overwrite attempts.
- `sample_feature3.py` now adds the original full-size authoritative
  PNG + exact pixel-derived review thumbnail to synthetic CI outputs;
  sample evidence now contains **seven non-AI artifacts**. Feature media
  unit tests assert successful generation. CI evidence must correspond
  to the exact final head after rebasing latest `main`.

### Still blocked by coordinator/system ownership

- Coordinator [#325](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/325):
  actual versioned Supabase migration, tenant-validated authenticated save
  route, private cloud job/preview/download, `react-konva`/Konva pin and
  mounted route, hosted auth/mobile E2E. Feature-owned source seam exists,
  but none of those shared integrations was deployed or fabricated.
- Azure HTTP ingress [#249](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/249)
  remains independently open.
- Real commercial FASHN VTON requires a separately licensed approved
  parser/model stack and an authorized GPU; FLUX actual model generation
  requires approved snapshot+GPU pricing/quota. Neither is enabled.
- No change to PROD/WineShopPOS/other feature workers, and no paid services.


## 2026-10-26 — Strict minimum-cost CPU delivery (Feature #3 owned files)

**Implemented, source-tested; no new billable cloud resources or dependencies:**

1. `studio_v2.py` now has private `_prepare_authorized_images` and
   `_render_prepared`: rights-verified staged images are opened/decoded
   **once per individual render job**, including if an image appears in
   several layers. `animate_v2.py` uses the same in-memory source image
   for every GIF/MP4 frame (up to 60), eliminating redundant file and decode
   operations. No cross-job or cross-tenant cache exists: revoked rights
   are rechecked for each new render job. Regression assertions in
   `tests/media/test_feature3_low_cost.py` count source reads.
2. `preview_v2.py` renders a **quarter-width/height draft PNG**, roughly
   **1/16 of full output pixels**, with an injected server-owned,
   idempotent per-tenant preview quota callback. It is **not pixel-parity
   evidence** and cannot replace the existing immutable full-resolution
   final + downsampled approval copy in `review_export_v2.py`. No GPU,
   network fetch, additional packages, new database or disk cache.
   `tests/media/test_feature3_preview.py` covers all 3 formats,
   budget rejection, revoked media, cross-shop denial and overwrites.
3. `Feature3CpuEditor.jsx`: basic layer/text/colour/placement/image-selector,
   undo/redo and local editable JSON workflow using **existing React
   only**. It is the default within `Feature3StudioPanel.jsx`;
   the optional advanced `Feature3KonvaEditor.jsx` remains unmounted
   pending coordinator-owned pins/QA. No canvas preview is represented
   as approved Pillow output.
4. The already mounted Part 1 `PosterStudio.jsx` now offers an opt-in
   **local CPU v2 Text-to-Poster editor** solely for authenticated/persisted
   days with well-formed shop/campaign/day IDs. It does not override the
   existing authorized v1 cloud save, queue, banner selection, download
   or mock-mode fallback. The editor correctly blocks Image-to-Poster
   until the host supplies authenticated loaded media; no unregistered
   photo or arbitrary external URL is trusted. Local JSON is **not**
   a cloud-saved or published poster. Mounting the offline editor is a
   bridge, not completion of secure v2 backend integration.

**Operational savings:** No always-on GPU, no paid FLUX/FASHN inference,
no new app/dependency, no new cache server. One image decode per job and
~6.25% preview pixel count target lower CPU/storage work; **no measured
cloud billing savings or Azure quote yet**. Keep price/offer from approved
retailer records, not prompt text.

**Still coordinator-owned / do not mark complete:**
- Add RLS-secured v2 draft+revision persistence and render/preview
  endpoints to existing DEV infrastructure; securely deliver licensed
  media imageMap to React and quota callback.
- Connect final server image review, signed downloads, approved variation
  selection, quota ledger and tenant/VIEWER/access-expiry hosted tests.
- Optionally mount Konva after cost/quality justification. It is NOT
  necessary for initial CPU poster editing.
- Verify live cloud E2E and current post-merge CI. Real FLUX and virtual
  try-on remain rights/GPU blocked until separate explicit approval.

**Branch** `feat/feature3-ai-poster-studio`, PR
[#321](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/321)
and coordinator issue
[#325](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/325).
Canonical `docs/PROJECT_STATE.md`, `docs/NEXT_TASK.md`,
`docs/DECISIONS.md` and `docs/WORK_LOG.md` are coordinator-owned;
this handoff requests those updates at review/merge.

### 2026-10-26 — Final incremental CPU efficiency and integration checks

- `studio_v2._render_prepared` accepts an **optional job-local in-memory
  resized image cache (max four RGBA images)**, while the single-job staged
  media authorization remains mandatory. `animate_v2.export_animation`
  provides its own bounded cache, so typical static flash/pulse posters
  resize a product once rather than every frame. No global/shared cache;
  next job re-checks rights. `test_feature3_low_cost.py` asserts
  16-frame GIF invokes Pillow's image fit just once and that a newly
  revoked asset fails at the start of the next job.
- `PosterStudio.jsx` now offers an explicit authenticated, persisted-day
  **local-only** CPU v2 text-poster editor. It does **not** change the
  v1 createPosterDraft/render/select/download API. A dedicated
  `test_feature3_v1_integration.test.mjs` guards the original v1 cloud
  controls and checks JSX compiles with existing Vite tooling.
- For real v2 image-to-poster, authenticated host must supply an
  authorized/private `imageMap`; no arbitrary URL or unattested local
  photo may be saved as a registered business media asset.
- Coordinator: integrate versioned database and readback, E2E mobile
  and signed download; only then promote v2 from local JSON to cloud.
  Not necessary to add Konva, GPU or additional always-on capacity to
  deliver basic CPU poster editing.

### 2026-10-26 — Browser-only no-GPU PNG draft and context-locked backups

- Added `frontend/src/features/creative/feature3-local-png.mjs`, a
  bounded 1080x1080/1350/1920 **local Canvas PNG draft** renderer.
  It draws real editable text, background/badge layers, rights-limited
  preloaded private image layers, alpha-preserving logo contain and
  product-image center cover. All text is wrapped to fit or export
  is blocked; it never truncates a shop name, offer or disclaimer.
  No URLs are fetched; no GPU, cloud queue or additional npm dependency
  is used. Browser output file explicitly says `unreviewed-local-draft`.
  This is a convenient local/fixture output, **NOT** the final reviewed
  Pillow render, approved media object, campaign banner or production
  publishing receipt.
- `Feature3CpuEditor.jsx` has a clearly labeled
  `Download local draft PNG (unreviewed)` button in addition to
  editable JSON backup. Offline standalone contract tests cover all
  required 1080 layout formats, image/brand placement, text-preserving
  rejection, unregistered image denial, excessive image dimensions
  and no prompt-invented discount (`feature3-local-png.test.mjs`).
- `feature3-local-backup.mjs` now binds every local JSON backup
  to the **exact original shop/campaign/day** and
  `approved=false, cloud_saved=false`; importing a backup from
  another day, shop, campaign, or from a media ID no longer allowed
  is rejected. Legacy raw v2 design-only JSON backups are not
  imported under the stricter day binding; such designs can still be
  reconstructed manually, but old raw backup migration requires
  explicit review. Negative tests in `feature3-local-backup.test.mjs`.
- Existing secure Part 1 cloud APIs are not modified; the CPU
  editor remains local until coordinator issue #325 provisions the
  reviewed versioned Supabase/RLS API and private output workflow.
  `feature3-local-png.mjs` is not an alternative secure server.
- **Exact confirmed CI on feature head `087ac10dffc13241b07ea674db2a40034cd14dd2`:**
  [PR run #40320930298](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40320930298)
  and [push run #40320924298](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40320924298)
  both **4/4 PASS** (existing frontend fixture contract/build,
  Python/uv, FFmpeg/media, disposable local Supabase isolation).
  Live React browser click-and-download tests on authenticated,
  hosted customers are **not** covered; do not claim they passed.
- **Cost**: zero new Azure/Supabase service, dependency, external
  model call, GPU or inference charges. Download uses retailer's
  local browser CPU. Actual cloud savings are not priced or benchmarked.
- **Next coordinator gates**: private-media imageMap, verified
  React mobile/browser interaction, v2 durable save/reopen and
  genuine signed immutable production PNG/GIF/MP4 downloads.
  Human approval and licensing still mandatory before publishing.

## 2026-10-26 — Assigned real fashion model/product visual integration actively resumed

The user's original requirement **"generate posters, fashion models and
product visuals" is NOT fully met by CPU template fixtures**. Continue until
actual FLUX 4B CUDA inference and a reviewed, private output is proven.

**Implemented this sprint (isolated feature-owned code, no cloud spend):**

- Reviewed official upstream [BFL FLUX.2](https://github.com/black-forest-labs/flux2),
  specifically commercial-use **FLUX.2 Klein 4B Apache-2.0**.
  Do not substitute 9B/dev or call 4B Base with distilled 4-step settings.
  Model card estimates ~13GB VRAM for local 4B inference.
- New `real_visual_demo_v2.py` invokes **real existing**
  `OfflineFluxKlein4B` with two local GPU calls when a compatible
  licensed, preinstalled 4B Diffusers snapshot and CUDA are available:
  synthetic adult fashion model; product visual (optionally locally
  reference-conditioned using explicitly owned garment image); then
  `studio_v2` renders a real 1080×1350 branded portrait poster using
  the model output. Writes verifiable SHA-256 and non-approval flags.
  NO fake model preview or virtual try-on is claimed.
- New `gpu_preflight_v2.py` checks exact source repo identity,
  40-character pinned revision, Apache-2.0, human-review approval of
  dependencies, hash of `model_index.json` and Klein pipeline class
  before any CUDA/model import. Shard hashes are NOT all audited yet,
  so this is a minimum local operator gate, not a full supply-chain
  audit or automatic customer deployment permission.
- Added `tests/media/test_feature3_real_visual_demo.py` exercising
  the actual Pillow composition stage and conditional image-edit route
  with an *explicit synthetic fake model runner*; negative tests cover
  cleanup on OOM, unsafe reference, wrong 9B/noncommercial manifest,
  invalid dependency rights, and changed pipeline index. Mock tests
  are not real CUDA inference evidence.
- `FEATURE3_REAL_MODELS.md` contains executable operator commands
  and exact no-network safeguards; no model downloads at runtime, no
  keys, paid external API, Azure GPU, PROD, WineShopPOS, or schema writes.
- FASHN VTON 1.5 remains disabled for commercial use until parser
  license clearance/replacement. Official upstream includes
  `fashn-human-parser` trained with NVIDIA SegFormer and a separate
  license; being segmentation-free for *user input* does not eliminate
  that parser dependency.

**Feature3 definition of done still pending:**
1. Fully review SHA-pinned 4B snapshot files/weights and run **actual**
   GPU inference on approved machine with approved 4B, save fashion
   model/product visual/real CPU-composed poster and visually evaluate.
   No CUDA or Diffusers runtime exists in this active build environment.
2. Confirm generated clothing accuracy; image editing is NOT a
   deterministic substitute for validated original garment virtual
   try-on. VTON parser clearance plus genuine try-on evaluation pending.
3. Wire provider to existing tenant/RLS, cost/usage ledger, retries,
   private media, authorized shop uploads and cloud dashboard under
   coordinator #325. Real signed-in hosted E2E and cost benchmark pending.
4. Coordinator integrates PR #321 and canonical docs after 4/4 exact
   head and post-merge main CI, never feature-worker self-merge.

**Current demos:** Existing artifact bundles demonstrate seven
*synthetic/CPU* outputs from the actual Pillow/FFmpeg engine (geometric
garment, not AI human); real fashion model sample MUST NOT be declared
available until an actual GPU run succeeds.


## 2026-10-26 — User-directed import-FIRST synthetic fashion library

The desired product is NOT "generate every model on GPU": **curate/import
commercially reusable existing synthetic adult human-model stills, share
across approved retailers, and retain separate optional Create New AI Model**.
This is the minimum-spend path, and it supersedes the prior default
AI-creation-first concept.

**Delivered in feature-owned source:**
- `model_library_v2.py` imports locally staged PNG/JPEG/WebP avatar image
  bytes, validates size, strips metadata, creates immutable SHA256 PNG and
  deterministic UUID/key, and uses mandatory trusted callbacks for
  independent license/rights, shop membership or platform-curator grant,
  private Blob upload, and durable registry write. No remote download.
- Supports **two scopes**: owner-shop private and curator-approved shared
  platform; server rights rechecked before every `poster`, `try_on` and
  `video_reference` reuse. Imported models start `PENDING_REVIEW`,
  never automatically approved/published. CC-BY attribution is required.
- Both `opensource_render` and `created_ai` supply exactly the same
  `retailgrowth.model-library.v1` record; existing FLUX model creation
  remains an opt-in separate cost-based operation, not duplicated storage.
- `tests/media/test_feature3_model_library.py` contains offline Pillow
  fixtures and rights/security tests: metadata stripping, same-hash
  dedupe, tenant denial, curator-only global publish, source provenance,
  revoked rights, forged private storage receipt, malformed/mismatched
  rights, animation rejection, CC-BY attribution and reuse by all three
  consumers. Fixtures are synthetic, **not externally sourced models**.
- `MODEL_LIBRARY_IMPORT_FIRST.md` documents reviewed initial source
  MakeHuman core CC0 assets/renders (separate third-party source licenses
  are mandatory), and explicitly forbids bulk scraping/importing random
  people photos or stock libraries with restricted redistribution.
- **No cloud migrations, live import UI, end-user library, real upstream
  images, commercial virtual try-on or GPU inference deployed.**
  This is source-only for coordinator interface/schema/backend review.

**Coordinator P0 next:** additive model registry RLS, platform curator
and tenant roles, rights evidence, immutable private media uploads and
signed previews, human approval/revocation, import browser UX and asset
handoffs to Feature4/5. Live tenant/VIEWER/expired-JWT E2E must prove no
cross-tenant leakage. Do not promote platform assets on self-declared
rights. Update canonical PROJECT_STATE, NEXT_TASK, DECISIONS and WORK_LOG
when PR reviewed/merged. **Cost default: zero GPU** for imports and
reuse; on-demand model creation still available when approved.


### 2026-10-26 — Pre-generated OpenPeople candidate for import-first AI avatar library
- Reviewed [OpenPeople](https://github.com/Prompt-Haus/OpenPeople) as
  closer match to the user's precise request than generating new people
  or MakeHuman 3D renders. Upstream claims 100 ready-made synthetic
  people (portraits/full-body) under **CC-BY-4.0 IMAGE licensing**.
  Its GitHub LICENSE is MIT **for code only**; README's development-only
  disclaimer and provider image rights still require independent legal
  review for a Redistributable SaaS catalog.
- Added `openpeople_import_v2.py`, an **offline-only**, commit-pinned,
  no-download adapter for `P001`–`P100` selected studio and
  casual JPEG stills into the generic
  `retailgrowth.model-library.v1` model rights/storage/review contract.
  Explicit signed-off license evidence, platform-curator approval and
  private immutable blob receipt remain mandatory. It refuses symlinked
  input, traversal, non-allowlisted kinds and malformed IDs. No model
  weights, GPU inference or CDN fetch needed to import.
- Added `tests/media/test_feature3_openpeople_import.py` with real
  local synthetic JPEG->PNG encoding, attribution, source lineage,
  rights/foreign-shop denies and try-on/poster/video reuse tests.
  **These tests do not load actual OpenPeople JPEGs.**
- No complete set of upstream images has been vetted or seeded in
  DEV. To be complete, coordinator must approve a small exact-source
  pilot, implement shop/global RLS catalog and private storage/preview,
  importer+approval UI and real browser/asset cross-feature test.
  Retain existing FLUX `Create New Model` separately as optional
  user-initiated paid generation.


## 2026-10-26 — Actual source-pinned Indian-profile library review slice

**User-approved strategy:** Start work importing pre-generated synthetic
Indian/South Asian-themed human stills from source repositories; keep
Create New AI Model optional, with the same saved model library for poster,
try-on and video references. No new Azure/GPU spend for this slice.

**Verified actual OpenPeople GitHub source:** pinned exact upstream commit
`231f73aa43b32a38001759944baa01d7d154ce26`; confirmed eight
metadata profiles and their two JPEG files each in the exact upstream
tree (P009, P006, P079, P033, P054, P059, P025, P016). Read and stored
Git blob hashes for all 16 image stills and eight metadata JSON files.
Descriptions like '80% South Indian' are fictional dataset prompt profiles,
not verified human origins. OpenPeople README says images CC BY 4.0 and
code MIT, but its testing disclaimer and external image/model rights still
need independent commercial advertising/SaaS redistribution review.

**Implemented inside Feature3-owned paths:**
- `feature3-indian-model-review.mjs`: immutable 8-character candidate
  metadata, full-body/portrait SHA pins, exact source GitHub links,
  and noncommercial/nonapproved, nonimported, zero-GPU review packet.
- `Feature3ModelLibraryReview.jsx`: accessible React 8-character selector
  for five female-presenting/three male-presenting source profiles,
  view immutable original links, download JSON packet locally. It
  never fetches/imports/upload/publishes media, performs no GPU work and
  preserves a separately disabled 'Create New AI Model' CTA.
- `Feature3StudioPanel.jsx`: mounts the opt-in model library reviewer
  through existing authenticated poster studio rather than modifying
  root App global routing or coordinator-owned source.
- `openpeople_import_v2.py`: for any locally staged approved source JPG,
  verify **Git blob SHA of physical source file bytes** against the
  independently pinned reviewed SHA before private PNG upload; rejects
  a fake same-named JPG and symlinked file paths. Existing tenant/curator
  role, licensing and immutable storage callbacks remain mandatory.
- `openpeople_indian_review_v2.py`: independent server-side 8-candidate
  and 16-image hash allowlist; fail-closed parse of client review packet
  with exact static status/permission/source fields and no extra keys.
  Never accept browser `approved:true` as business license evidence.
- Tests `feature3-indian-model-review.test.mjs`,
  `test_feature3_indian_source_review.py` and extended
  `test_feature3_openpeople_import.py` cover JSX compile, no browser
  imports, cross-language exact 16 packets, source replacements/rights
  spoofing, local source bytes Git-object mismatch, prior tenant gates.
  These test samples are offline and **do not contain actual upstream JPG
  bytes** or prove commercial rights/real model image appearance.
- `INDIAN_OPENPEOPLE_IMPORT_PILOT.md` is operator/curator runbook.

**Coordinator P0 outstanding:** real consent/license-cleared upstream
source image selection and 2–3 asset pilot on privately staged images;
catalog RLS/migrations/platform-curator role/private signed assets;
server API for authenticated rights review/import; real blob uploads;
visual QA, rights revocation and cross-feature integration to try-on
and video; signed-in owner/VIEWER/other-shop/expired-token E2E.
Feature worker must NOT deploy, edit canonical docs or self-merge PR #321.
Update PROJECT_STATE/NEXT_TASK/DECISIONS/WORK_LOG on integration. Actual
FLUX model generation, FASHN VTON licensed try-on and Feature5 video
remain independent GPU/quality/licensing gates.


### 2026-10-26 — Private source-image pilot QA (feature-owned; unmerged)

- Added `openpeople_pilot_qa_v2.py` to turn 1–3 **genuine, locally staged
  pinned OpenPeople JPGs** into a private 0600-mode, visibly
  UNAPPROVED contact sheet and an SHA256/provenance JSON receipt.
  The operator's 0700 private review folder must be new and is never
  overwritten. Source candidate, review packet, Git blob and symlink
  integrity are checked before rendering any preview.
- Added `tests/media/test_feature3_pilot_review.py` negative/positive
  **synthetic-image** tests. These cannot substitute for visual inspection
  of actual upstream people. No upstream image bytes were downloaded,
  imported into Azure or published to any SaaS tenant.
- The audit receipt permanently defaults rights, likeness, fashion quality,
  import eligibility and production-readiness to FALSE; no browser packet
  or script can bestow curator approval. Commercial source-image/provider
  rights and exact locally supplied genuine JPGs remain external blockers.
- Updated the owned Indian pilot runbook. Main integration still belongs
  to the coordinator; no canonical docs, migrations, shared APIs, WineShopPOS,
  Azure GPU or production infrastructure were touched.
- Cost: review and CPU thumbnails only, zero inference GPU calls; local
  private storage has ordinary disk costs. Full online catalog still
  needs coordinator-owned authenticated private Blob/RLS/signed preview.
- CI evidence for this addition must be checked at its **new exact SHA**;
  do not reuse the prior PASS 4/4 for `86b341d`.

## 2026-10-26 — Owner-approved reduced scope, and no-GPU model reuse

User removed genuine upstream Indian model-image inspection, independent
third-party license verification investigation, and live Hosted DEV/browser
E2E from the **current sprint work list**, not from commercial-release
safety gates. Explicit separate status and integration contract:
[`FEATURE3_REDUCED_SCOPE.md`](FEATURE3_REDUCED_SCOPE.md).

**Code now committed on Feature #3 only:**

- `feature3-approved-models.mjs`: zero-fetch UI filtering of authenticated
  server-provided model-list rows; no private Blob paths/URLs, no unreviewed
  source-review candidates. OWNER/EDITOR/VIEWER server checks still required.
- `Feature3StudioPanel.jsx` adds Saved AI model poster (CPU), composed
  from an already authorized, loaded registered image, not fake try-on.
  Tracks image SHA and registered asset on draft creation so an altered
  or revoked model source hides that draft until reselected.
- `PosterStudio.jsx` now passes optional `approvedModels` and
  `authenticatedModelImageMap` from its signed-in host; both default to
  empty so v1 customer poster workflows remain unchanged.
- `model_catalog_projection_v2.py`: backend-owned model + private media
  reauthorization adapter to produce limited browser picker metadata.
  **This adapter is not an authenticated HTTP endpoint or live RLS.**
- `model_reference_v2.py`: tenant-scoped, rights-revision-fenced private
  reference/cache key contract for poster, Feature4/5 video-reference
  and try-on integrations. No paid inference, garment try-on or moving
  video is executed.
- Test files `tests/frontend/feature3-approved-models.test.mjs`,
  `tests/media/test_feature3_model_reference.py` and
  `tests/media/test_feature3_model_catalog_projection.py` cover
  duplicates, private-asset availability, revoked rights, foreign shop
  selection, supplier-grant spoofing, and cache fingerprint changes.
  **Only synthetic mock-authorizer/source fixtures.**

**Coordinator to integrate when ready:** add durable model registry/RLS
and current-rights RPC, private media registration and imageMap preview
service, authenticated model list API to mounted PosterStudio, versioned
server v2 draft persistence and secure poster outputs, plus optional
Feature4/5 private reference consumer approval. This handoff does not
change global docs/contracts or the coordinator-owned migrations/APIs.
Model creation and actual VTON remain disabled unless license, provider,
rights, residency and cost quota gates are satisfied.

**Current exact-head CI:** check the newest Actions run after these
commits. No claim of completed deployment, genuine upstream import,
hosted browser E2E or production readiness.


## 2026-10-26 — FLUX GPU source continuation, operator gating

- #420 real offline FLUX one-shot source worker and #426 complete v3 checkpoint digest attestation are integrated, not live.
- #430 merged `d376518cf247c46256bd67c4a6960259b4ae6974` after exact 4/4 CI #40390460968. The worker checks post-inference torch CUDA synchronization/allocated device memory and **refuses to write a success receipt when the runner is mocked**. Docker entrypoint has 900s GNU timeout. One-shot billing admission requires protected operator `RETAIL_FLUX_PAID_ONE_SHOT_APPROVED=1`, verified all-in rate `RETAIL_FLUX_TOTAL_RATE_USD_PER_SECOND` and explicit maximum `RETAIL_FLUX_MAX_USD_PER_RUN`. None is enabled in hosted DEV.
- CUDA compatibility, Docker build, paid inference, model private mount, signed tenant/ledger/outbox and actual fashion sample remain unverified; only fake CUDA modules/synthetic PNG are tested offline. Azure last audited T4 managed-environment quota = 0 and no running GPU. Request **1 Managed Environment Consumption T4 GPU** on existing Feature5 `rgai-f5-gpu-canary-eastus`; verify positive quota, exact pricing and owner cap before any GPU start. Defer third-party image licensing and hosted browser E2E per owner sprint instructions without waiving production restrictions. WineShopPOS untouched.

## 2026-10-29 — Independently verified synthetic-input delivery to Feature4+Feature5
- New source: `poster-engine/feature3_demo_inputs_v1.py`, `tests/fixtures/feature3/openvto_demo_sources_v1.json`, MIT notice, and [real artifact #12874751370](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40820810387/artifacts/12874751370) from [SUCCESS #40820810387](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40820810387) contain actual upstream synthetic model/garment/portrait photos, byte-pinned and image-decoded. Supply first frame `model_posture.jpg` to Feature5 dry-run only; Feature4 may load model/garment files independently. Do not claim model is wearing unrelated shirt or generated by Feature3.
- For actual customer PRIVATE media, `poster-engine/feature3_worker_inputs_v1.py` provides `materialize_feature4_inputs` (model, garment, reviewed frame bytes) and `materialize_feature5_input` (verified first-frame bytes) under current tenant approvals and durable render/motion leases. The consumer MUST supply trusted live readers/lease callbacks and never use test fixtures as permissions. Full instructions: `docs/feature3/FEATURE4_FEATURE5_SHARED_INPUTS_20261029.md`.

## 2026-10-30 — F3-13/F3-25 strict offline FLUX JSON source proposal (run 3)

- Feature-owned proposed branch `feat/feature3-flux-strict-json-review-20261030-run3` rejects duplicate JSON keys and nonfinite JSON constants in the reviewed FLUX full-snapshot manifest and pinned model index, and rejects ambiguous index JSON during candidate creation. A last-key-wins approval field must never count as a trustworthy operator attestation.
- New offline regression in `tests/media/test_feature3_flux_t4_snapshot.py` uses synthetic tiny shard/config bytes and explicitly falsified approval/index JSON. No checkpoint downloads, inference, GPU start, Azure, hosted SQL, PROD, WineShopPOS or paid services.
- Source-only pending coordinator review and exact-head four-job CI; **F3-13 and F3-25 remain IN PROGRESS/BLOCKED for their full acceptance**. This is not licensed commercial media, a signed approval, a deployed provider, or integrated DONE. No change to shared task progress registry until coordinator accepts and merges.
