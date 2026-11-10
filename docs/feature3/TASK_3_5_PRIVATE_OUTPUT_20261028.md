# Feature3 Task3.5 — JWT-scoped private generated image downloads

Source-only feature-flagged route:
`GET /api/shops/{shop_id}/feature3-gpu-jobs/{job_id}/download`

The current signed user's active shop membership is checked first.
The server then obtains the GPU job through the *same JWT* and PostgREST
RLS. Only `SUCCEEDED` with an existing output media ID proceeds. It
independently queries `media_assets` under the JWT and demands matching
shop, job ID, generated source, PNG MIME, private bucket and exact
content-addressed `{shop_id}/feature3/gpu/{job_id}/{sha256}.png` key.
Only then is the already-existing 60-second `TenantStore.sign_download`
used with that user's JWT. No public media path, unsigned URL, browser
asset override, model-approval or GPU job creation is supplied.

This is intentionally OFF in hosted DEV until Task3.4 GPU schema source
and protected deployment are integrated, a real private output has been
generated/registered, storage RLS grants are verified and the current
authenticated actor is signed in. It does **not** claim actual FLUX CUDA
or human approval. API tests assert foreign/revoked/unready/malformed
output denied before signing and no cross-tenant Blob exposure.

Remaining: real output writer/storage integrity and cleanup, UI download
button, approved model reuse, hosted signed OWNER/VIEWER/foreign acceptance
and current-rights revocation; these are not waived.

No paid GPU, PROD or WineShopPOS modifications.
