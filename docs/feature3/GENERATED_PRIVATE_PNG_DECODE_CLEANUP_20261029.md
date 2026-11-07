# Feature #3 generated private PNG decoder failure cleanup — 2026-10-29

## Scope (source-only; package F3-10 / F3-13)
- In `Feature3GeneratedHistory` an authenticated, SHA-verified `blob:` preview may still fail when the browser image decoder rejects its content. Previously that failed image remained in the local URL scope until manual clear or scope turnover.
- The image decode `onError` now calls `discardFailed(shop,job,exactObjectURL)` on the existing generated-preview registry. Only an **exact currently-owned** shop/job/URL can be freed; stale decode errors cannot revoke the user's newer preview. The selected failed Blob is revoked immediately and the UI reports an opaque error, without showing private paths.
- Targeted Node test exercises current, stale, foreign, duplicate and replaced Blob failures. Existing four-job CI must complete on the PR head. This does **not** prove actual signed hosted download, current independently reviewed source rights, GPU inference or approved commercial publishing.
- No hosted endpoint, SQL, Azure, queue, GPU, paid provider, PROD or WineShopPOS change. Existing old signed URLs cannot be retroactively revoked.

## Integration handoff
- Feature-owned branch: `feat/feature3-generated-png-decode-failure-cleanup-20261029`; coordinator to review and merge only after exact-head 4/4 PR CI and fresh postmerge 4/4 main.
- Keep the 33-package ledger at **0/33 fully hosted DONE**. This is scoped reliability progress within source-partial F3-10 and F3-13, not completion of either package.
- Main blocker for actual hosted F3-08/F3-10 remains **#471/#325** (coordinator + Feature3, mounted no-URL private endpoint and rights service); release also waits on **#249** (Azure gateway 503) and **F3-LICENSED-MEDIA** (independently reviewed actual rights).
