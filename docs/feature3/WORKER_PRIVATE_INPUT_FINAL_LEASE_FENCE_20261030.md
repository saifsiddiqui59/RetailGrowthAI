# Feature #3 private worker input final lease fence — 2026-10-30

**Original tasks:** F3-02 and F3-13. **Status:** SOURCE PROPOSED; not integrated DONE.

The existing GPU-OFF worker handoff checked the durable lease before fetching private source bytes but did not revalidate that lease after byte reads or before exposing temporary files. A revoked/replaced/expired worker could receive formerly authorized private input paths during slow staging.

The proposed change makes two additional read-only exact worker-claim checks: one after final source rights and byte integrity checks, and another after private temporary file materialization but before yielding paths. A false/non-boolean current claim denies and the temporary folder is deleted. No queue ACK, billing, inference or unsafe automatic retry.

Deterministic offline tests simulate lease revocation after byte reads and during staging; they assert fail-closed denial and cleanup. Fixtures are not real approved customer imagery. Coordinator must verify exact-head four-job CI, merge reviewed code, then fresh main four-job CI before DONE.

**Live blockers:** F3-LICENSED-MEDIA (Feature3 rights owner: independently licensed original garment/model and current signed reviewer grant); #471/#325 (Feature3/coordinator: real private route and current rights); #249 (Azure lead: hosted signed 503-free DEV); two isolated DEV OWNER logins pending supported Auth Admin provisioning. GPU stays OFF; no paid provider, SQL migration, PROD or WineShopPOS.
