# Feature #3 private model preview Blob URL failure cleanup — 2026-10-29

## Source-only change
- Existing `Feature3PosterHost` already downloads a bounded maximum of five shop-owned, current JWT/RLS private model previews and cryptographically checks the returned bytes against the trusted model catalog. A failed browser `Image` decode after `URL.createObjectURL` previously left the failed object URL in the host registry until another refresh, shop switch or unmount.
- The host now tracks each candidate URL; on a failed decode/access exception it immediately calls the existing same-origin, local-only `discardFailedPrivateModelPreview` helper, removing that URL from the registry and revoking it exactly once. Successfully decoded previews remain in the existing registry and are revoked on refresh, shop/account change and unmount. Late changed-scope responses are still discarded and cleared, never moved to another tenant.
- Pure Node tests cover failed URL removal, duplicate-safe revocation, unowned/external URL denial and preserving a valid sibling preview. Vite/Chromium CI remains mandatory; tests do not prove a genuine signed DEV model exists.

## Security/release limitations
- This is a browser memory-lifecycle improvement, not an image-rights grant, live model approval, secure private-binary route activation or GPU inference. `VITE_FEATURE3_PRIVATE_BINARY_ENABLED` remains an independent reviewed gate. Signed 60-second Storage URLs already issued remain valid until expiration; memory cleanup cannot revoke them.
- No public image path, generated customer asset, hosted SQL, queue, provider, PROD or WineShopPOS change. Actual real licensed model/garment review and signed tenant acceptance remain blocked independently.
