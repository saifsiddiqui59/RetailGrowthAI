# F4-13 — tenant-private canonical storage key hardening (2026-10-30)

**IN PROGRESS; backend source-only, not live private storage validation.** Feature4 branch `feat/feature4-canonical-private-media-path-20261030` stacks on F4-15 PR #851; it changes only feature-owned worker validation/tests/handoffs.

## Defect
`feature4_worker_handoff._bundle` receives authoritative approved database asset rows and passes each `object_path` to the existing private media downloader. Previously the only path gates were prefix `<shop_id>/`, no literal parent segment, no backslash, no double slash and no `://`. A key such as `<shop_id>/approved/./image.png`, `%2e%2e`, `?token=...`, `#fragment` or invisible Unicode control could therefore reach a downloader even though frontend `privateMediaPreviewUrl` already rejects it. This creates needless canonicalization and URL-encoding ambiguity at an authorization boundary.

## Fix and tests
Reject noncanonical keys **before** CPU, network download, billing, or renderer: require the authorized exact shop prefix, length <=1000, ASCII `[A-Za-z0-9._/-]+` characters and no empty, `.` or `..` segments. A normal uppercase/lowercase nested approved storage path remains accepted. Tests reject encoded traversal and encoded slash, dot segments, query/fragment characters, newline, hidden zero-width mark, whitespace, or duplicate slash, with zero download/upload/completion. The tests use synthetic records; no Supabase data is modified.

**Compatibility:** This is a stricter local contract. If RetailGrowthAI DEV has existing legitimate Unicode or whitespace object keys, the coordinator must explicitly review how they are issued, register canonical safe aliases with rights/tenant integrity, and migrate safely *before* enabling the worker. Do not silently rename actual objects or claim verified migration. No change to shared schema, API, uploader or signed-download contract.

Exact-head four-job CI, coordinator-reviewed main integration + fresh main 4/4, protected packaging #650, Azure #249, and independent approved commercial source rights still pending. F4-13 is NOT DONE; no GPU, paid service, PROD, public media export or WineShopPOS modification.
