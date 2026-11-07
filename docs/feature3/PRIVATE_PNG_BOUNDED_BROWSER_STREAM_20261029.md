# Feature #3 private PNG bounded browser streaming — 2026-10-29

## Source-only correction (F3-08 / F3-13)
- The existing future private PNG browser client checked Content-Length and SHA after using `response.arrayBuffer()`. A misconfigured/hostile response could allocate arbitrarily large memory before the check.
- The client now requires a streaming response body, allocates **only the validated 100-byte to 25 MiB announced size**, copies chunks without overrun, actively cancels oversized/invalid streams and verifies exact length, PNG magic and SHA256 as before. Network request count, no-redirect policy, signed bearer identity and local private Blob output are unchanged.
- Node tests cover normal fragmented PNG, truncated, absent, malformed and deliberately overlong streams. Mocked data is not genuine media, live JWT proof or rights review.
- This does not mount a private Azure route; existing signed URLs are unchanged. No GPU, paid model, DEV/PROD deployment, SQL, queue, media approvals or WineShopPOS changes.

## Coordinator handoff
- Branch: `feat/feature3-private-png-stream-size-fence-20261029`; review after exact-head CI 4/4 and fresh postmerge main 4/4. The original 33-package ledger is being edited by concurrent PR #683; coordinator must append this evidence after integration rather than allowing concurrent overlapping ledger writes.
- Keep **0/33 fully hosted DONE**; F3-08/F3-13 remain partial due #471/#325 signed no-URL endpoint and rights callbacks, #249 503 and F3-LICENSED-MEDIA approval.
