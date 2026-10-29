# Feature #3 F3-09 / F3-13 — generated-history state allowlist (2026-10-30)

This independent CPU-only source change prevents arbitrary metadata from being forwarded when the signed-in UI projects local generated-job history into the current tenant's view. The scoped view now returns exactly `shopId`, validated strict job metadata, a bounded local status message and a strict boolean busy flag. Untrusted caller properties such as signed URLs, storage paths, JWT-like strings, forged publication approvals and GPU authorization flags are never retained.

The existing shop-identity check and strict job-row validator remain unchanged. Added Node negative regressions for foreign-shop state, forged metadata, malformed busy/message types and frozen snapshots.

**Status:** proposed source-only. A merged PR, fresh four-job main CI and signed hosted DEV tenant-isolation tests are still needed. No generated commercial output, independently verified source license, signed download or GPU inference is asserted. External blockers include `F3-LICENSED-MEDIA` (independently reviewed customer originals/rights), `#249` (host reliability) and `#471/#325` (signed mounted binary route). This change does not satisfy those gates.

No SQL, Azure deployment, paid provider, PROD or WineShopPOS changes.

## Same-shop session-identity privacy fence (F3-11/F3-13)

The private decoded model library previously used only `shopId` to decide whether old pixels could render. A signed-in host can replace its API/JWT client while keeping the same shop; the old model preview could remain visible until React effect cleanup. `scopedFeature3Preview` now optionally requires exact current API identity; `Feature3PosterHost` tags pending and completed private previews with the API instance and passes that identity during render. A stale session's decoded pixels are synchronously hidden even when the shop UUID is unchanged. Existing async nonce and explicit Blob revocation remain in force. Offline negative tests cover an API-client rotation; no live sign-in was simulated.
