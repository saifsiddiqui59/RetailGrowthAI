# Feature #2 fixed tasks #2/#4 — human-readable retailer copy and signed RSS display safety

2026-10-29 · **IN PROGRESS**, branch `feat/feature2-mp3-dual-private-receipt-20261029`, stacked PR #684, source/fixture only.

## Scope
The existing reviewer-only `feature2_creative_quality` audit now fails closed on Unicode bidirectional overrides/isolates, invisible source separators, C1 text controls and Unicode line/paragraph separators in retailer headline/caption/CTA/narration and both standalone verified RSS rows and signed private XML RSS2 headlines. It deliberately permits Indic combining marks and ordinary Devanagari conjunct ZWJ, preserving Marathi/Hindi feed relevance. This reduces human-review deception but is **not** a full content-sanitization renderer and grants no publishing/real-trend authority.

Tests assert outright denial of six display spoof classes in the three ingress points plus preserved legitimate Indic joiner relevance. No live feed was fetched, paid LLM called or original commercial source approved. Actual RSS feed source allowlist, independent signed private snapshot, authenticated API, human editorial review, locale UI rendering and Azure reliability are still coordinator-owned.

## Acceptance
Require targeted `ai-agents/tests/test_feature2_editorial_basis.py`, exact-head four-job CI of stacked PR, coordinator source review, safe reconciliation into unified #551 and fresh postmerge main 4/4. Existing coordinator issue #650 ZIP package and Azure #249 remain separate. The original register does **not** advance source COMPLETE or integrated DONE on these source-only assertions. No GPU/PROD/WineShopPOS changes.
