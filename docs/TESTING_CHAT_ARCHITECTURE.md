# Testing Chat / Feature Trace Console (2026-10-29)

## Intent
Give an authorized retail business OWNER/EDITOR a normal-language testing chat that
follows **actually wired** feature endpoints, saves each verified request/response
handoff, and allows a human to mark which feature needs quality improvement.
This is **not** a promise that all seven features are assembled into one
production pipeline or that a successful API call guarantees good output.

## Source implementation
- React route `/testing-chat`; sidebar "QUALITY LAB" link.
- Modes: prompt-only (Feature2 free deterministic), real seven-day DEV campaign
  through existing campaign API, or campaign plus first-day 30s FFmpeg render.
- Uses existing user JWT; membership and licensed input read via existing Feature1
  client; Feature2 through existing `createTrendApi.improvePrompt`; planner and
  render through `createCampaignApi`.
- Uses additive `feature_test_runs` and append-only `feature_test_events`
  PostgREST tables, protected by current signed-user shop OWNER/EDITOR RLS.
  A VIEWER, revoked account or foreign shop cannot read/write. No browser
  service key, direct API-key-backed worker jobs or privileged bypass.
- Release-candidate SQL in `supabase/release-candidates/20261029090000_feature_test_trace.sql` must be explicitly reviewed and moved into the canonical migrations inventory, then **applied to RetailGrowthAI DEV**. The current exact-history preflight must remain unchanged. The updated frontend must also be deployed before the route can store persistent live logs.
  No hosted change is implied by committing the SQL.
- The output shows prompt transformations, campaign IDs, actual first-day
  LinkedIn/Instagram text, storyboard scene count, render job IDs/terminal
  status, measured browser latency and response errors; it deliberately
  does not store signed storage URLs, JWT, provider keys, raw stack traces,
  cloud instance identities, cost secrets or session passwords.
- User reviews include feature, score 1–5 and explanation; successful execution
  and human quality ratings remain separate and are never conflated.

## Truthful feature mapping
| Feature | What this version truly observes | What it does not imply |
| --- | --- | --- |
| #1 | Current authenticated shop OWNER/EDITOR and licensed-media metadata | Independent license adjudication |
| #2 | Deterministic improve-prompt reply and the Part1 planner draft | Paid Foundry text/voice/trend coverage or model-level spans |
| #3 | Explicit NOT_RUN receipt | VTON poster/model generation |
| #5 | Explicit NOT_RUN receipt | Wan/other paid text-to-video or image-to-video |
| #4 | Existing Part1 30-second FFmpeg worker when selected | Entire Feature4 professional compositor/editor |
| #7 | Explicit NOT_RUN receipt | Smart editor output or integrated scene-level QA |

A stage with no receipt is `NOT OBSERVED`, not PASS. `NOT_RUN` means this
test intentionally did not call it. `UNKNOWN` includes ambiguous non-idempotent
POST acknowledgement and bounded polling. No automatic campaign/render POST
retry; read saved Campaign Studio state before manual recovery. No public
publishing, licensed stock fetch, real Wan, GPU or provider cost is triggered.

## Added regression diagnosis (source only)
- Pure `trace-diagnostics.mjs` computes first FAIL/UNKNOWN stage without silently hiding it behind a later PASS. Reports per-feature observed status, latency, and separately scoped human quality scores.
- Bounded read-only history analysis fetches up to ten authorized saved runs on explicit user action; summary counts PASS, FAIL, UNKNOWN and NOT_RUN separately. p95 is only a sampled browser observation, not a backend SLA claim.
- Compare one saved same-shop baseline against current test: per-feature execution status, latency delta and score delta only when both real human scores exist. Unknown/unobserved comparisons are never reported as quality improvements.
- Frontend permits human output-quality feedback only after a completed observed feature output. No quality of absent Feature3/5/7 execution is implied.
- CI security stage executes a proposed SQL schema in disposable `127.0.0.1:54322` PostgreSQL independently of protected migration history, then tests actual OWNER, EDITOR, VIEWER, foreign, revoked EDITOR and anonymous policies. This remains **offline source qualification**, not approval to deploy SQL to hosted DEV.

## Next architecture contracts (not implemented)
1. Extend each feature service with a server-generated span writer:
   `{trace_run_id, shop_id, feature_id, operation, attempt_id,
   parent_span_id, status, input_artifact_refs, output_artifact_refs,
   duration_ms, error_code, model_provider_version, rights_evidence_ref}`.
   Persist trustworthy service-only spans in an RLS-protected internal store,
   never allow the browser to assert that a worker actually ran.
2. Pass trace context across the campaign DB outbox, Azure Queue workers,
   poster/model job, approved Feature3 private assets, Wan provider callbacks,
   Feature4 FFmpeg composition, Feature7 editor and social publishing.
   Correlate to immutable tenant-scoped artifact hashes, source rights,
   cost ledger and final MP4. Do not carry JWT or raw prompt in queue messages.
3. Add optional quality rubrics by output type (copy, brand fidelity,
   garment identity, model anatomy, transitions, voice/music, audio levels,
   captions, video resolution and publish safety), human approval and
   regression comparison. Automated heuristics are not independent quality proof.
4. Add a server-side summary by feature/release/model version:
   success rate, unknown rate, p95 latency, quality rating distribution,
   expected vs actual assets, cost per accepted result and first failing span.
   Enforce retention, limits, sensitive-data redaction and operator-only access
   before scaling test volume.
5. Integrate authenticated backend telemetry and feature-specific artifact
   previews through approved additive contracts. For Feature3/5/7 currently
   missing real runtime integration, show NOT_RUN, never synthetic PASS.

## Execution / release gates
- Test front-end Node fixtures, Vite build, Python backend and isolated
  Supabase migration/RLS negatives with mandatory four-job CI.
- Hosted DEV schema migration and frontend release are **separate**
  integration gates; current branch is source-only.
- Azure issue #249 intermittent gateway 503 remains open; classify unknown
  outcomes accurately and do not replay POST, bypass JWT/RLS, change SKU,
  or claim missing client response means a failed DB/worker operation.
- Never use WineShopPOS resources or touch PROD.

## 2026-10-29 — Source additions after original design
- F2 planner/Part1 F4 FFmpeg worker outcome spans now have strict status/metadata and optional backend-only service RPC sink. A separate private-schema ledger plus signed OWNER/EDITOR read RPC is staged (not applied) and the Testing Chat UI can read it by job IDs already present in browser-observed receipts. This is not a trusted run→job mapping until independently verified. Duplicate public-ledger draft #626 was discarded; no second table.
- Mocked Chromium now renders the saved StageCards without the former undefined-variable error, checks signed backend RPC, missing-schema fallback and viewer denial. Source PR #628 4/4 CI, merged at 4a3acd3e. Real hosted Supabase, SWA and Functions deployment and genuine tenant/job acceptance are separate gates. F3/F5/F7 continue NOT_RUN.


## 2026-10-29 — Source-only human QA improvements
- `trace-guidance.mjs` ranks observed execution failure, uncertain POST/readback, human-rated low-quality output and NOT_RUN/UNOBSERVED features separately. It suggests feature-specific next checks, never automatically reruns non-idempotent requests.
- `quality-rubrics.mjs` and `trace-quality-analysis.mjs` define user-selected review dimensions and compare only like-for-like reviewer aspects, not provider scores. A completed API/worker operation is not equivalent to approved creative quality.
- The pending `trace-output-evidence.mjs` source gate (#666) distinguishes job ACK from actual observed F2 text/seven-day or Part1 F4 finished private output; unintegrated F3/F5/F7 cannot be scored by current Testing Chat path. Test-run→job is still browser-referenced rather than backend attested; hosted SQL/SWA/Functions activation remain separate.
