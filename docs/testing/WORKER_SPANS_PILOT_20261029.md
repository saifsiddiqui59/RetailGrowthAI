# RetailGrowthAI worker-authored feature span pilot — 2026-10-29

## What is actually implemented
The existing claimed/leased Part1 planner and FFmpeg render workers can now
offer one **backend-authored** span to an optional injected callable after
their authoritative DB terminal mutation is confirmed. The contract is
`retailgrowth.worker-span.v1`, feature `F2` for planning and `F4` for
the existing Part1 FFmpeg Reel (NOT the full Feature #4 professional editor).
It contains a fresh random span ID, trusted backend-resolved shop and job
UUIDs, fenced attempt number, duration, allowlisted operation/status and
minimal verified metadata (seven generated days, planner mode, codec,
video dimensions/duration). No text prompts, arbitrary exception contents,
raw private object paths, API keys or signed media URLs are accepted.

The default `span_sink=None` does **not** write to a database or cloud logger.
All such spans state `persisted=false`. The optional sink receives an
in-process dict and may fail without changing SQL claim/fencing or worker
business state. This is intentionally a source-only foundation for a
future reviewed service-only durable writer, **not** production evidence.

## Observed boundaries
- A planner `planning.complete` span is offered only *after* `admin.finish`
  confirms the fenced completion. Denied, unconfigured and failed results are
  separately recorded only after `admin.fail`.
- An FFmpeg `render.complete` span is offered only after validated H.264/AAC
  output was privately uploaded and `admin.complete_render` completed.
  Revoked users produce `render.denied` after the authorized DB failure;
  exceptions produce `render.failed` only after failure recording.
- Already-final or competing-lease queue deliveries do not produce invented
  new success spans.
- Negative tests cover unknown features/statuses/operations, invalid
  identifiers, arbitrary metadata/secrets, no-sink and broken callbacks.
  Worker tests assert successful output and revocation paths.

## Remaining release integration
1. Implement a **service-only, tenant/RLS/lease-aware** private span table
   plus reviewed versioned migration and durable ingestion. Current
   `feature_test_events` candidate is **browser writable** and must never be
   promoted to server-authoritative audit evidence.
2. Carry run-to-job correlation through a trusted database mapping,
   not a user-supplied queue message/JWT or public URL. Existing job IDs
   can correlate first under signed same-tenant user read. Durable worker
   span ownership must revalidate current identity, job and claim token.
3. Integrate Feature #3, #5 and #7 separately after their real runtime jobs
   have actual claims and private artifact receipts. Feature #5 paid
   providers are OFF absent independent budget authorization.
4. Only after reviewed deployment and signed two-shop role-denial E2E may
   Testing Chat label a backend span as **trusted, persisted**. Until then
   the browser shows its own receipts and the worker pilot remains internal.

No new Azure Functions endpoints, queue payloads, database/grants,
GPU/LLM paid calls, PROD or WineShopPOS mutation.

## Contract consistency hardening
- The operation now has an exact status mapping (for example `planning.complete` only `SUCCEEDED`, `render.denied` only `DENIED`). An arbitrary injected sink cannot be handed a contradictory outcome under the current validation contract.
- Completion metadata must match the observed operation: planning has exactly `planner_mode` and **seven** generated days; 30s FFmpeg completion has verified `h264/aac`, 1080×1920 and the same duration tolerance as the renderer. Denial/failure carries no unverifiable output metadata.
- Parameterized negative fixtures reject fabricated completion, inconsistent metadata, incomplete fields, invalid media geometry/duration and misreported denial. Actual source worker must still validate all provider and output results independently; these spans do not authorize publication or change billing.
