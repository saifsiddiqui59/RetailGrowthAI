# F4 CPU DEV private-trigger rollback audit — 2026-11-23

Protected run #45089361586 passed DEV Supabase service-role, zero jobs and API-OFF checks, but did not index the expected three queue/timer triggers after eight bounded polls. Its failure handler attempted to restore worker and render flags OFF and delete the temporary service key. This does not prove those changes took effect.

The new protected one-shot GitHub Actions audit reads only the exact F4 DEV worker, original customer API, settings metadata and function names through already configured Azure OIDC. It does not write Azure settings, secrets, queues or code. It fails if the private worker is ON, a service key remains, the original API is active, a foreign resource is returned or any function unexpectedly remains indexed. It logs only fixed categories and counts, not setting values or customer objects.

If the read-only audit passes, investigate startup/import/extension issues using sealed ZIP offline import tests and platform-safe logs before attempting a bounded follow-up private-only activation. Do not treat source/CI green as hosted proof. Retailer CPU_RENDER, Feature #3/#5 GPU, PROD, WineShopPOS and Issue #249/Y1 remain untouched.
