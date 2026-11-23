# F4 original DEV API ZIP: read-only rollback discovery

After worker 3/3 trigger activation passed (#45103369693), the guarded original API review-only stage (#45104337519, rechecked with safe diagnostic #45105096093) failed **before mutation** because the live original Flex API was missing one or more of the seven source-declared Feature4 HTTP routes (`original-api-f4-index`). Merely toggling flags cannot fix a stale deployed ZIP.

## Source-only next stage
A new protected `dev` one-shot `retail-dev-feature4-original-restore-inventory-once.yml` reads exact original DEV RG/site/tags, current settings and function names, then classifies the deployment backing store WITHOUT logging any setting value or customer information. It distinguishes a private `WEBSITE_RUN_FROM_PACKAGE` Blob URI and a Flex `functionAppConfig.deployment.storage` Blob container without claiming either is a pinned copy of the **currently running** immutable ZIP.

The check reports only storage mode and number of missing F4 routes, with `exact_active_package_backed_up=false` and `mutation_permitted=false`. No Azure or Supabase writes, new spending, customer routes, logs/artifacts of secrets, PROD, GPU, Y1/#249 or WineShopPOS changes.

Before a protected original API ZIP republish can be authorized, separately establish the exact live private package key/digest (or another source-backed identical restore package), an independently runnable same-run restore, original v1 HTTP and queue consumer parity, no pending jobs/duplicate consumers, service settings and CORS parity, and bounded rollback verification. Preserve `RETAIL_FEATURE4_CPU_RENDER_ENABLED=false` even if protected package staging later succeeds. Real signed two-shop retailer review/render/private download and actual Auth Admin test provisioning are distinct downstream gates.
