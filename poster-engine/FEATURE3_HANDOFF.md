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

