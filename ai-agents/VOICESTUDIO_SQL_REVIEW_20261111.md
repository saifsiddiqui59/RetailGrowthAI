# Feature2 — VoiceStudio original-key PostgREST SQL review (2026-11-11)

This is **review-only SQL, not a migration**. It has not been executed on the live RetailGrowthAI Supabase project. It is intentionally independent of F2 source PR #920's protected SQL client so reviewed backend code can progress while a separate reviewer checks all privileged database changes.

## Current DEV observations (read-only, 2026-11-11)
- RetailGrowthAI DEV is active on PostgreSQL 17 with existing `public.shops`, `public.shop_memberships`, `public.campaigns`, `public.media_assets` and private storage; all public tables listed have RLS enabled.
- `public.campaigns.status` is constrained to `PLANNING/DRAFT/READY/FAILED`; memberships to `OWNER/EDITOR/VIEWER`, with `active` flag.
- No Feature2 VoiceStudio job/plan tables are currently deployed. There are no campaigns in DEV at inspection; real signed two-shop voice output tests cannot be claimed.
- The old **unmerged** Feature2 private-voice SQL on PR #848 hardcodes `kokoro-onnx`, another bucket and one WAV object path; do **not** deploy it together with this new VoiceStudio schema. This file replaces that design rather than duplicating a second old engine.

## What the script implements
- RLS-enabled `feature2_voicestudio_plans`: approved script only with human-reviewed record, independent model/commercial rights evidence reference, current shop/campaign scope and revoked-at CAS.
- Service-only `feature2_voicestudio_jobs`: one original request ID, 25m claim lease, immutable private WAV path origin, both byte sizes and SHA-256, and `NEEDS_REVIEW` final state. No published media asset or browser-accessible job table.
- Four service-only **SECURITY INVOKER** RPCs exactly matching source client `feature2_voicestudio_sql.py`: `plan` reads current approved source, `claim` inserts only a new original-key request and never replays a duplicate, `register` atomically promotes a claimed job only with current editor, campaign and plan evidence, and `receipt` rechecks current membership before returning a **private review-only** asset ID.
- Explicit revocation of function EXECUTE from PUBLIC/anon/authenticated. No direct public job mutation, no security-definer privileges, no signed URLs, no automatic VO publish or billing claims.

## Required before any DEV/PROD migration
1. A separately reviewed **signed human-approval plan writer** must persist plan digest, reviewer, exact tested voice model/license evidence, consent and active subscription/budget. There is deliberately no public mechanism to assert `commercial_rights_confirmed=true` with this SQL alone.
2. Independent Supabase security and cross-feature review; check RLS on both tables, storage bucket policies, function grants, job lease/race behavior and any pre-existing migration names. Apply with a real migration only after acceptance, then run actual DB assertions and advisors.
3. Implement an authenticated public user initiation route that derives the actor from JWT and passes only the original source IDs to the trusted backend. Only worker-owned service key can call RPC; client never receives service_role credentials.
4. Register a **separate reviewed** signed Feature4 media asset after human listening approval and latest two-shop rights check; Feature7 HMAC word timing remains a separate gate.
5. Keep VoiceStudio GPU/paid/weights OFF until real commercial model component licensing and AGPL obligations are cleared.

**Status:** F2-19 / F2-20 SOURCE PROPOSED, NOT DEPLOYED, NO LIVE VOICE, NO AUTOMATIC DONE. WineShopPOS untouched.
