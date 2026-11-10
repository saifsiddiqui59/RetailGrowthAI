# Feature #2 — signed RSS2 snapshot parsing handoff (2026-10-29)

**Status:** source-only parsing, provenance and reviewer tests; **not** a live RSS crawler, Internet provider license grant or automatic trend publication.

## Implemented in Feature #2

`ai-agents/src/ai_agents/feature2_creative_quality.py::rank_verified_rss_snapshot` processes up to 25 RSS 2.0 items from a **bounded (<=200 KB), SHA-256-pinned** original XML byte string. Its trusted context must contain a currently authenticated OWNER/EDITOR shop. The separate callback `verify_current_private_snapshot(shop_id, snapshot_id, xml_sha256)` must be implemented by a trusted backend that verifies current rights/membership and the actual privately stored original bytes, both before and after ranking.

The parser uses Python's stdlib `xml.etree.ElementTree` **with DOCTYPE/ENTITY markup rejected**, no network parser, no outgoing RSS URLs and no public feed content mirrored into the response. It accepts RFC 2822 zone-aware `pubDate` and a plain bounded title, hashes each GUID into a stable opaque trend ID, rejects duplicates, future-dated items and nested/script headlines, and omits items older than the existing 14-day relevance window. Unicode-aware relevance preserves Hindi/Marathi grapheme words. The exact same SHA of the original private snapshot flows into every candidate's source proof and is verified by the already implemented `rank_source_backed_trends` reviewer.

**Return remains `REVIEW_REQUIRED` or `EVERGREEN_FALLBACK`.** It explicitly carries `can_publish:false`, `can_auto_create_trend_draft:false`, `verified_live_trend_claim:false`, `source_is_real_time_trending_proof:false` and `raw_feed_url_published:false`. A signed snapshot does **not** establish that the topic is commercially useful, legally reusable, trending on Instagram or accurate.

Offline regression tests are in `ai-agents/tests/test_feature2_editorial_basis.py`: source hash tampering, lack of current source authorization, rechecks/revocation, Doctype/XXE, script markup, duplicate GUIDs, stale/future dates, >25 items, no relevance evergreen fallback and Marathi headline matching.

## Coordinator handoff

1. Implement independent server-owned **feed allowlisting**, TLS/certificate verification, SSRF/IP/dns private-host denial, strict request timeout/byte limit, acceptable provider terms, original immutable object storage and active source grants. **The browser must never choose an arbitrary feed URL.**
2. Atomically persist the exact unmodified original RSS2 response bytes plus SHA, current shop, source/provider grant, signed snapshot ID, observation time and private ownership. Set an explicit retention policy. No signed, current source → no ranked candidate.
3. Implement the trusted `verify_current_private_snapshot` backend callback, including RLS role revocation and post-read source recheck. Do not allow a client to set `server_verified=true`.
4. Map editor-reviewed candidate IDs into the existing guarded copy/Director workflow only after current retailer fact rights and human review. Do not auto-generate claims/discounts or auto-post because a title overlaps a keyword.
5. Run hosted DEV same-shop and cross-shop negative tests after coordinator contract approval, with exact-head 4/4 CI. [Release ZIP manifest blocker #650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650) is independent.

No paid services, hosted provider fetch, Supabase migration, PROD resources or WineShopPOS changes occurred for this source-only work.
