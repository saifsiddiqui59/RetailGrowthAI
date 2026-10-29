# Feature #3: claimed GPU job lease expiry fence (GPU OFF)

## Scoped source change — F3-02 / F3-13
- The claimed-worker preflight previously checked that `feature3_gpu_jobs.lease_until` was a string, but an already expired, malformed or timezone-naive one-shot lease could still produce `current_lease_verified: true` if an injected reservation reader matched its token.
- `Feature3GPUJobPlanPreflight._snapshot` now requires an unexpired, timezone-aware current SQL lease for RUNNING claimed jobs, *before* independent private media/rights reads. The same check runs on the authoritative second DB snapshot. After the final private source/right verification, claimed mode checks expiry again to prevent a delayed license probe from certifying an expired lease.
- New offline negative tests cover past, malformed and timezone-naive leases; a claim expiring during the first private source proof; and expiry during the final rights proof. This is a read-only safety fence and is not a paid attempt or authorization to run the GPU provider.

## Owner/coordinator handoff
- Branch: `feat/feature3-claimed-gpu-lease-expiry-fence-20261030`; requires exact-head 4/4 CI, reviewed coordinator integration into main and fresh postmerge 4/4. The original 33-package ledger is concurrently touched by PR #683; coordinator should reconcile this handoff after integration instead of overwriting shared docs.
- No live private source/right authority, legitimate real apparel model, GPU invocation, Azure queue processing, hosting, production deployment, Supabase migration, spend, or WineShopPOS modification. **0/33 fully hosted accepted** remains unchanged. Live one-shot work awaits F3-LICENSED-MEDIA and F5-GPU-AUTHORIZATION / PART3-WAN22-CONTRACT where applicable.
