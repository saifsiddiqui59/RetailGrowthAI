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
