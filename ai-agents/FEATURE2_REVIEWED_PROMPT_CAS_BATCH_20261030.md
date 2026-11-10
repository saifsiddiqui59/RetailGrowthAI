# Feature #2 reviewed-prompt source/CAS batch — 2026-10-30

Original assigned tasks **F2-03 and F2-31 IN PROGRESS**. Source only; no real LLM billed or independent signer connected.

1. Approved-provider test callback can no longer add new price/offer/stock/delivery claims not present in the vetted canonical prompt, even if it preserves the original exact retailer request. A multiset of bounded claim tokens is compared; legitimate original claims remain flagged for review rather than certified.
2. Server-side private prompt revision CAS receipt must echo exact original SHA, source revision, proposal ID, review-event ID, pending DRAFT status, private/committed flags and NO publish, motion, or provider-call authority. Recheck signed current editor after storage callback; the DB must transactionally fence authorization and clean up changes on revocation.
3. Existing browser reviewer receipt verifier now binds proposal ID/source revision/original request SHA, not just improved SHA and next revision. Existing receipt and injected test fixtures updated and extended with negative cases. This verifier is for presentation only; backend signed human review remains authoritative.

All changes grouped in ONE branch commit and one CI boundary with existing offline retailer tests; do not call a fixture a verified retailer approval. Parent unified PR #551, other F2 draft branches, coordinator issue #650 immutable Azure Functions package limit and #249 DEV HTTP 503 are separate integration gates. Coordinator owns merge to latest main and fresh 4/4. No paid models, GPU, PROD, hosted writes or WineShopPOS changes.
