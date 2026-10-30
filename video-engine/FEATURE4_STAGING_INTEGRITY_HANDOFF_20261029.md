# Feature4 staged-byte integrity handoff — 2026-10-29

**Task IDs:** F4-13 (private input integrity), F4-15 (worker failure/race negative tests). Both remain **IN PROGRESS**, not integrated DONE.

**Owned branch:** `feat/feature4-stage-input-integrity-20261029`, forked at Feature4 draft #322 SHA `e32a8da61a6272666d757b6c51b0ec2576d7602f`. Does not alter the other isolated F4-04 duplicate-parity branch.

## Source-only change

The existing authenticated worker's downloaded, reviewed private media staging files are now SHA-256 and stable-fstat checked using no-follow regular-file opens. The worker compares each original before and after CPU rendering, refusing changed, appended, replaced or symlink-swapped inputs **before private output upload and claim finalization**. The existing per-claim total staged-byte budget, tenant authorization, lease fence and one-charge coordinator RPC remain unchanged.

Existing injected renderer tests now cover three negative mutation classes (same-run overwrites, appends and symlink swaps) and require no media upload or completion, plus permanent input-error receipt. The tests remain deliberately fake renderer and synthetic source fixtures, NOT genuine Azure/Supabase JWT/RLS, commercial original-byte grant verification, source identity, licensing, rights approval or live retry success.

## Verification and integration

- Required tests: `python3 -m unittest tests.media.test_feature4_worker_handoff -v` or the repository's `video-engine/ci.sh`; at batch boundary require 4/4 branch and PR checks.
- Coordinator must review and integrate into main with **fresh 4/4 main CI** before marking either F4 task DONE. Update original 31-item task ledger and `coordination/task_progress.json` only through coordinator after accepted integration.
- Other blockers: F4-22/ISSUE-650 coordinator packaging, F4-29/ISSUE-249 Azure HTTP, F4-30 real two-tenant signed DEV E2E. These do not invalidate this independent source work.

**Safety:** No GPU, paid inference, hosted SQL, PROD, customer media, new services or WineShopPOS.

## 2026-10-30 — F4-15 no-cost lease preflight and staged inode proof

This **independent feature-owned source batch** branches from existing draft #816, avoiding any source or doc edits from concurrent F4-05 branch #822. F4-15 remains **IN PROGRESS**, not integrated DONE.

- Private staging source is now capped **before hashing** at the existing 300MiB combined cap, denies empty files and confirms the local path still identifies the same no-follow descriptor inode after SHA. An atomic replace with identical bytes now fails closed rather than passing hash-only checks.
- The worker checks the authoritative coordinator-provided lease/CAS claim state before it downloads any private media and again after the assets are staged / before CPU encoding. A claim revoked before staging performs zero private downloads; a lease lost during staging stops before rendering. Existing post-render fence remains unchanged. No new billing, queues, Azure resources, HTTP endpoints or signed output.
- Synthetic deterministic race tests verify both stale stages with no uploads and no completion. Actual local same-content inode replacement during SHA, empty source and sparse oversized source are rejected. Tests use fake admin and local media and **do not** prove production lease RPC or Supabase RLS semantics.
- Exact-head 4-job branch CI, coordinator integration/main reconciliation and fresh main 4/4 remain mandatory. Hosted retry/poison cleanup, worker lease race and billing are coordinator dependent. No paid models/GPU, PROD or WineShopPOS.
