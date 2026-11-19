# F2-12 private workflow trace fence — source-only recovery, 2026-11-15

Original [#767](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/767) head `3dc03d1c3a7c67f68acc4f3c0a3c814d9f859196`, built on conflicted parent #551. Copied the original exact Git blobs **unchanged** from that head to current main:

- `frontend/src/features/voiceover/voiceover-trace-request-gate.mjs` — `7c02928eafee3a731a3605cd209c52c74f0b4607`.
- `tests/frontend/feature2-private-trace-request-gate.test.mjs` — `3c7fc29006c75a7878b690374da1fd9400003c33`.

This is a client-side stale-response generation fence: overlapping requests or changed shop, campaign, workflow, source, or enabled state invalidate old tickets. Tests are actual Node test runner assertions with synthetic scope strings, no retailer tokens, credentials, network, paid inference or media.

**Critical boundary:** this fence is NOT authentication, RLS authorization, signed-HMAC verification or a hosted API. The older #767 React panel depends on additional unintegrated VoiceStudio/trace modules and must not be bolted into current main without separate reviewer and backend JWT/RLS checks. Original F2-12 remains IN PROGRESS for signed private trace/real UX integration; #551/#848 source work stays open. Original #767's remaining code and handoff are separately archived if the redundant stacked PR is closed. No GPU, Azure/Supabase mutation, PROD or WineShopPOS.
