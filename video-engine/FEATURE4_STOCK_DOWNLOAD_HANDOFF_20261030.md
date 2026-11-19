# Feature #4 — F4-13 private stock download integrity handoff (2026-10-30)

**Owner:** Feature4; **base:** draft PR #322; **task:** F4-13, source IN PROGRESS (not integrated DONE).

## Change

- `video-engine/feature4_stock_showcase.py` uses private random 0600 temporary files for **offline stock QA** download staging. Rejects preexisting/symlinked destination and symlinked parent, computes SHA-256 while streaming bounded bytes, and publishes by same-directory `os.link` (atomic no-clobber). A competing writer is not overwritten.
- `tests/media/test_feature4_stock_download_atomic.py` uses fake network responses and synthetic bytes to test hash, cleanup, destination race, preexisting private bytes, symlink and invalid MIME. No actual stock clip or generated customer video is produced.

## Acceptance and blockers

- Await exact-head four-job CI and coordinator review of this stacked PR; do not count source-only changes as DONE.
- Commercial attribution/transitive license notices and real tenant-granted media are separate F4-13 / F3-LICENSED-MEDIA gates. Test-only Pexels provenance is **not** approval of a retailer product or permission to redistribute media.
- Shared Azure Functions ZIP member cap issue #650 is coordinator-owned; Azure 503 #249 remains separate. Never bypass protected checks.
- No GPU, paid model, PROD, hosted SQL, user-facing sample, customer credential or WineShopPOS changes.
