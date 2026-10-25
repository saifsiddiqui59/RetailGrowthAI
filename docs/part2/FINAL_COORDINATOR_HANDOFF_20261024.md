# RetailGrowthAI Part 2 — Source Handoff to Final Coordinator

Date: 2026-10-24 · Branch: `feat/part2-integration` · Mode: **source-only, all outbound posting OFF**.

## In scope and verified

- Social accounts/OAuth state/token vault, revocation and refresh foundations; isolated tenant grants and read-only social dashboard.
- Facebook Page/LinkedIn text adapters with authorization, approved revision, quota reservations, queue and claim-CAS send barrier. **Adapters/fake transport only, not confirmed real account posts**.
- Instagram 30s and YouTube Shorts review-only backend: private P1 render source, bounded sha256 + real FFprobe H.264/AAC checks, independently verified commercial-rights receipt contract, exact job/media/revision binding, append-only finalized render digest and license evidence ledgers; no video approval grant.
- Private provider container intent/session/receipt CAS and poison reconciliation; created-media upload adapters and optional claim-scoped PostgREST bridge.
- `retailgrowth-media/<shop>/social-exports/<job>/<revision>/<sha>.mp4` protected service-only prefix within original Part1 private bucket. **No second media bucket**; do not use the historically superseded early P2 191400 version. Immutable copy-once source writer is disabled by default.
- Exact PR CI for #271 (run 40133836637), #273 (40134333301), #274 (40134812401), #275 (40135312766), #278 (40135730975), #279 (40136209686), #281 (40136421553) — all four jobs green per PR. #283 source-only upload bridge internally merged `267bebee` after 4/4 exact-head [Actions #40137590410](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40137590410); post-merge [#40137732617](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40137732617) must be inspected independently.

## Unhosted migration order

P2 SQL is held under `supabase/part2/pending`, versioned `20261023190000` through `20261023191600` inclusive, applied **only to an approved disposable test database**. Latest requires all preceding versions, after current hosted Part1 migration set reconciliation.

- 190000 social foundation/account credentials
- 190100 OAuth transactions
- 190200 plan caps (starts intentionally EMPTY) / reservation
- 190300 dispatcher claims + inflight receipts
- 190400 authoring / hard-deny video approval
- 190500 claim context/token vault
- 190600 poison reconciliation
- 190700 OAuth refresh
- 190800 asset license/FFprobe reviews
- 190900 draft revision protection
- 191000 safe pre-send cancellation/quota refund
- 191100 job/revision review binding
- 191200 private Instagram/YouTube session and remote receipt ledger
- 191300 Part1 finalized render SHA + independent commercial clearance
- 191400 **same original bucket** protected social-exports prefix, no bucket creation
- 191500 active Instagram export lease/source/rights/consent predicate
- 191600 claim-scoped Meta container lookup + AES-256-GCM YouTube session versioned save/read (source CI 4/4, merged #283 to Part2; NOT hosted)

Never skip the gap/cross-tenant negative tests or assume migration compatibility with advancing Part1 `main`.

## Actual blockers to a hosted social release

1. Part1 operator must provide a trusted finalized-render byte SHA producer; immutable source checksum MUST be established at original FFmpeg render finalization, not retroactively inferred from tenant-mutable storage.
2. Licensed media review: independently validate publisher commercial rights, musical/audio copyright, brand ownership, provider permitted use and expirations, with real reviewer and evidence records; never let an uploaded JSON hash replace evidence.
3. P2 video publish SQL currently **hard-denies Instagram/YouTube approval**. Before lifting the deny, require exact approved revision/media/account/time CAS, active shop plan+role+grant, immutable service-only export with final byte proof and a provider-specific negative E2E suite, including provider receipt verification.
4. Real Meta/Google/LinkedIn OAuth app permissions, channel roles, owner selected accounts, OAuth secrets, approved plan publishing caps and revocation behavior cannot be invented from unit tests.
5. Register/publish Azure timer/queue/poison worker with `RETAIL_PART2_FUNCTIONS_REGISTER_ENABLED` only after independent owner approval of migration, provider app grants and publishing quotas. Keep the outbound transport disabled and all live posts OFF in interim.
6. Validate on licensed DEV test accounts: duplicate queue deliveries, provider timeout after acceptance, Meta container FINISHED/media_publish ID, YouTube encrypted 308 offset + remote video ID, cancellation/refund correctness, system health and usage per shop. Source CI alone cannot prove this.
7. Final Coordinator alone integrates Part2 to **latest** `main`, preserving P1 JWT/auth, account notifications, super admin, subscriptions, billing, FFmpeg and separate Part3 Wan feature; requires exact-head four GitHub Action jobs for PR and post-merge main. No modification to WineShopPOS.

## Release classification

`SOURCE_FOUNDATIONS_TESTED` is not `SOCIAL_PUBLISHING_RELEASED`. This record grants **zero** authorization to apply hosted migrations, enable OAuth, publish to a customer social account or incur external cloud costs. Do not claim an offline gallery is a real platform-posting demo.

## 2026-10-25 — Verified Part2 continuation; coordinator action required

**Latest source integration (before this docs checkpoint):** `feat/part2-integration` `f01f3134abf2bb1734953dde6486bb1d254dcdf1`. The advancing standalone Part1 `main` was `d3002915515a8b071b8f5ea6517e4bfb35b4f9e9` during verification; reconcile through Final Coordinator, never overwrite it.

- [PR #286](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/286): deterministic AES-GCM tamper-test assertion, 4/4 exact-head and post-merge.
- [PR #288](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/288): source-only `20261023191700_p2_reviewed_video_approval.sql` adds a separate service-only, exact-revision/license/render-hash/FFprobe/social scope/atomic publish-quota CAS. **The existing social authoring route still denies video and this new SQL RPC has no public caller.** 4/4 exact-head [CI #40168290469](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40168290469) and post-merge [#40168434230](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40168434230).
- [PR #290](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/290): unregistered backend `ReviewedVideoApprovalService` requires verified JWT/membership, rereads DRAFT and private receipt+rights, calculates its OWN canonical digest and passes the DB CAS. No browser digest/rights input; no provider transport; OFF unless constructed with explicit flag. 4/4 exact-head [#40168667475](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40168667475) and post-merge [#40168792555](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40168792555).
- [PR #292](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/292): disabled service-only `FinalizedRenderReceiptWriter` computes SHA-256 and H.264/AAC FFprobe from an existing trusted private Part1 FFmpeg scratch output, rechecks file mutation, and calls append-only source SHA ledger. **Not wired into Part1 renderer**; applying the source library is not evidence that any real asset was finalized. 4/4 exact-head [#40169072335](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40169072335); independent integration [#40169220089](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40169220089) was running when handoff was authored; verify final success separately.

**Staged migration count:** 18 P2 source SQL files, ordered `20261023190000` through `20261023191700` inclusive. They are only validated against disposable Supabase. None have been applied to hosted DEV or PROD.

**Remaining owner-specific boundaries:** Actual Part1 finalization callback wiring and media-byte retention; actual reviewed licensed commercial music/stock/brand rights and legal expiry records; consented provider OAuth production/test app grants and secrets; explicitly approved publish-plan quota caps; full real account remote receipt/duplicate/timeout testing; complete claim-bound video worker integration; Coordinator Part2→latest main reconciliation and approved hosted migration/rollout. No live Instagram/YouTube/Facebook/LinkedIn posting has been verified. Keep all release flags OFF; protect WineShopPOS.
