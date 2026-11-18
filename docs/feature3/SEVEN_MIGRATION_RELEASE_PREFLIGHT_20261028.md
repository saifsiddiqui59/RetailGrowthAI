# Feature #3 — Seven pending migrations: live baseline and fail-closed release rehearsal (2026-10-28)

The connected **RetailGrowthAI** DEV Supabase project `jeearzffnjbvghwjjjrf` is healthy and still reports **24 applied migrations**, last `20261028101328_feature3_gpu_budget_jobs`. Seven chronological SQL files exist on source `main` but **none has been applied to hosted DEV**. The exact seven-file order is pinned by `tests/security/feature3-migration-release-gate.mjs`, using existing `verifyPreflight` SQL capability checks and the official Supabase history (not a fake schema advance). The current hosted database is neither a disposable DB nor a valid signed multi-role acceptance fixture.

## Work completed in this branch
- Implemented a **read-only** signed-release plan: rejects foreign/stale/partially applied/gap/divergent histories, new migrations, missing transaction boundaries and dangerous DDL. Each version, SQL byte length and SHA256 is emitted to enable human review and audit. A repeat execution is **not** assumed idempotent: these CREATE migrations must be applied exactly once under the canonical version ledger.
- Node tests cover 24 + seven positive plan, 31 already-applied informational plan, every partial history 0–30, stale/foreign/future/gapped history, and transaction/destructive-DDL injection. These are **local/offline** source tests, not live signed-user proof.
- Dependency order: Feature1 inbox → Feature3 review/evidence → verified evidence writer → pending model import → private generated CAS → GPU outbox recovery → model-original registration. All seven must preserve active-role ACLs and default-off GPU controls.
- **Rollback**: original migrations are not safely replayable and no generic DOWN migration is claimed. Before a protected hosted change, verify a DEV backup/restore, staged exact-version deployment, post-DDL negative tenant tests and a recovery owner; abort on first mismatch.

## Still blocked
1. **Approval gate**: `docs/DEV_DEPLOYMENT_APPROVAL.md` has independent Supabase DEV and hosted E2E gates; this report and passing CI do not approve or execute either.
2. **Signed identities**: no actual isolated hosted OWNER, EDITOR, VIEWER and independent curator JWT authentication test was run. Existing mock/disposable SQL role tests remain distinguishable.
3. **Real virtual try-on**: an official Commons CC0 garment file has independently verified original-byte provenance in existing #576, but no independent person-likeness release or tenant-private approved model original exists. The existing #571 six-trait candidate test is offline only. No paid FASHN / provider GPU, account impersonation or generated try-on has occurred.
4. **Hosted website/Function**: public UI presence and read-only infrastructure checks alone cannot verify signed import/review/upload/download. Original Azure #249 gateway 503 remains independently open.

No production, Azure spend, paid inference, hosted schema writes or WineShopPOS modification.
