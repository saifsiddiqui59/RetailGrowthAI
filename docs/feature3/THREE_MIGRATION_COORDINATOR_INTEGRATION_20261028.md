# Feature #3 — three-migration coordinator integration (2026-10-28)

Source-only dependency fix across already tested PRs #565, #566 and #570. The existing canonical main is unchanged until coordinator acceptance.

**Ordered SQL (new sources, all unhosted):** `20261028230000_feature3_gpu_private_output_cas.sql`, `20261028231000_feature3_gpu_outbox_recovery.sql`, `20261028232000_feature3_model_original_registration.sql`. Follows merged import `20261028223000`. All three are present in `tests/security/dev-db-preflight.mjs` with exact-source security markers; the old Feature2 21-version scoped release gate now recognizes all ten pending versions and *still* returns `authorized_to_apply=false`. Disposable Feature2 rollback rehearsal safely removes new output evidence and outbox-recovery dependents, then rolls back to restore all records without CASCADE.

The combined branch retains exact business logic from #565/#566/#570: current active tenant reviewer and private source rights, one-shot token lease, generated SHA claim registration with private Storage prefix write protection, queue dispatch send ACK and uncertain paid recovery incident *without* inference replay or automatic billing, signed model-original (unverified source) registration. No new GPU, queue, Azure, hosted DB, PROD or WineShopPOS write.

**Hosted DEV note:** Connected Supabase RetailGrowthAI project `jeearzffnjbvghwjjjrf` read-only migration history is **24 applied versions**, through `20261028101328`. Earlier pending `20261028173000`, `20261028190000`, `20261028210000`, and `20261028223000` must be included and authorized before the three new versions. Never assume passing disposable Postgres grants production release approval. Signed current real tenant/curator acceptance, actual private garment/model copyright/likeness, real VTON, measured cloud billing and original #249 gateway behavior remain unverified.

QA: exact final-head 4/4 GitHub Actions (real disposable Supabase SQL + Python + Frontend + FFmpeg); independent post-merge main 4/4. Separate owner-approved, reversible, scoped hosted migration/role release and non-production verification required for DEV. GPU remains disabled.

