# #249 — isolated DEV Y1 private versioned Blob release

**Scope:** Existing tagged Linux Consumption Python 3.12 Y1 only. Do not modify the original Flex, PROD, WineShopPOS, GPU workloads, Supabase, private customer media or billing.

## Evidence and deployment choice

- Previous original protected five-GET ZIP test #44618073780 and corrected remote-Oryx #44629301025 returned Azure HTTP 202 but indexed only **two** functions. The latter also auto-removed `ENABLE_ORYX_BUILD`; both automated rollback jobs returned error.
- Protected owner-authorized read-only #44668555433 then demonstrated current `WEBSITE_RUN_FROM_PACKAGE` **equals the saved original external Blob URI**, original two functions indexed, **20/20 live health/unknown requests passed**, original Flex unchanged. The previous rollback errors therefore were not evidence of an ongoing outage.
- Microsoft guidance documents a **private Blob package URL** as a supported Linux Consumption deployment method without remote build; the host runs from the URL named by `WEBSITE_RUN_FROM_PACKAGE`, and its triggers must be synced after activation. Repeating a config ZIP with a stale URL is not proof that the new ZIP was activated.

## New protected deployment (manual-only + owner one-shot)

1. Build exactly five GET-only handlers from source byte allowlist, verify staged no-redirect original JWT/PostgREST module, approved Python dependencies, manifest index and no worker/queue functions. Install dependencies into `.python_packages` on the Linux GitHub runner and ZIP the exact vetted root.
2. Before any mutation verify the original Flex + precise Y1 identity/tag/plan/region, exact saved original private Blob URI equals the active URI, prior failed-run owner `44629301025`, exactly two original indexed functions, no customer/shadow settings, and the **existing** private container in the expected DEV storage account.
3. Require OAuth `--auth-mode login` Blob data access **and** user-delegation read-only SAS generation before any upload; never use shared account keys or expose a SAS. Use a unique `p0249-y1-trial/<current-run>/five-readonly.zip` object, never overwrite existing media/code. Confirm object length before switching.
4. Set a distinct new run ownership marker before updating only isolated Y1 `WEBSITE_RUN_FROM_PACKAGE` to the private **versioned** Blob URI. Sync triggers via the pinned ARM WebSites action; require exact five GET indexes and live health/unknown 20/20 plus all four JWT-missing negative-401 GETs, repeated after 240 seconds idle.
5. On any failure before or after switch, same-run and independent protected recovery set the **exact saved original package URI** (if not already active), require original two indexes and 20/20 live HTTP. No invalid CLI `sync-function-triggers` is a prerequisite for acceptance. Never overwrite any unknown route, unauthorized run, changed resource, or customer settings.
6. The delegated SAS expires in **six days** by design. This is DEV canary testing only; do not switch production/frontend traffic or rely on this URL for permanent hosting. Replace with an approved managed-identity package reference and independently verified tenant auth/rollback before removing the saved original URI.

## Remaining issue gates

Live signed JWT two-shop own/foreign/revocation for all four original GETs, original POST/PATCH/media/queue/billing parity, markerless original Flex #249 503 root cause and p95/p99 remain **OPEN** even after a successful five-route negative-auth canary. GitHub PR CI alone cannot establish live Azure success.

Safety controls: exact latest-reviewed main SHA, protected `dev` environment, manual-only permanent release workflow, one-time owner-verified GitHub dispatch, success only on actual indexed/live checks. Cost: reuse existing private storage and Y1, one small unique ZIP, GPU and paid inference OFF. Neither a key nor package URL may be printed to Actions output or committed.
