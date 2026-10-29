# Feature3 signed-retailer private PNG transport integrity — 2026-10-29

## Source change, not hosted release
- Extends the existing unmounted `Feature3RevocablePNGReader` authenticated private Storage GET. Besides immutable SHA256, Pillow decode, no-redirect, allowed MIME, JWT+RLS user and post-read current rights, the reader now rejects any provided `Content-Length` that differs from **actual** returned bytes, even if the image is otherwise decodable. An absent length is acceptable for legitimate chunked transport because actual bytes are still bounded and independently SHA-checked.
- An unexpected `Content-Encoding` (gzip, br, deflate, etc.) is rejected to ensure a transport cannot silently transform an immutable source. Explicit identity encoding is permitted.
- `tests/api/test_feature3_private_png_reader.py` uses actual Pillow PNG pixels and mocked authenticated HTTPS with non-public key/tenant fixtures to verify both positive and negative paths, including announced zero/truncated/overstated lengths and data transformations. All foreign-shop, revoked rights, invalid JWT, changed-output and current callback denial checks remain.
- This is defense in depth for package #08/#13/#20. It does **not** mount or enable the private binary Azure route, issue signed Storage URLs, establish independent commercial source rights, or prove hosted DEV user acceptance.

## Gates still required
- Coordinator review of an actual signed JWT/RLS authenticated binary endpoint and **genuine** server-owned current output rights+source-rights verifier; existing read-only model and output-evidence SQL are proposals, not hosted migrations.
- DEV negative signed users, revoked rights while streaming, role expiry, 503 ingress and provider-side output registration must be verified before route activation. Previously minted 60-second signed Storage links cannot be revoked by browser Blob cleanup.
- No GPU paid inference, queue ACK, billing/settlement, DEV/PROD hosted migrations, or WineShopPOS changes in this task. Validate exact-head 4/4 and fresh post-merge main 4/4.
