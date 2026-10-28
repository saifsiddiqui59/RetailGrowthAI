# Feature3 — real hosted DEV READ-ONLY acceptance and blockers (2026-10-28)

**Target**: Supabase project `jeearzffnjbvghwjjjrf` (RetailGrowthAI, ACTIVE_HEALTHY, PostgreSQL 17.11). This is a real read-only DB preflight using the connected project's actual catalogue, NOT a source fixture or a hosted functional release.

| Gate | Actual observed result | Decision |
| --- | --- | --- |
| Migration history | 24 versions applied, last `20261028101328_feature3_gpu_budget_jobs`; source repo includes 7 subsequent distinct versions | FAIL live activation: pending unapproved SQL |
| Missing chronological versions | `20261028173000_feature1_retailer_inbox`, `20261028190000_feature3_model_review_audit`, `20261028210000_feature3_private_evidence_commit`, `20261028223000_feature3_pending_model_import`, `20261028230000_feature3_gpu_private_output_cas`, `20261028231000_feature3_gpu_outbox_recovery`, `20261028232000_feature3_model_original_registration` | SOURCE COMPLETE, NOT HOSTED |
| Tenancy | 2 shops, 2 auth users, only 1 active membership | Cannot claim signed OWNER/EDITOR/VIEWER/curator cross-tenant acceptance |
| Original private media | Private `retailgrowth-media` bucket exists, 1 registered media row and 1 original private object; no bytes accessed | Bucket/RLS presence proven; pixel rights/tenant JWT not proven |
| Feature3 model | 0 approved models, 0 pending models; unhosted `feature3_import_pending_model` / `feature3_review_model` / `feature3_register_model_original` functions absent | Import/review FAIL readiness |
| GPU / cost | 0 RUNNING GPU jobs, 0 enabled Feature3 GPU budgets | Safe default OFF preserved |
| Advisor review | RLS no-policy INFO for service-only private outbox and similar service records; authenticated SECURITY DEFINER WARN for older signed RPCs; unindexed FK INFO | Review privileges before release, do not automatically broaden authenticated RLS |
| Real licensed image | Separate `#576` test on independently published Wikimedia Commons CC0 photo verifies real source byte SHA1, dimensions and copyright metadata via network | Only copyright of that photo; not an owner's private garment/model approval |
| Actual VTON | No approved same-shop person photo/likeness release, no FASHN paid account or actual output/visual comparison | NOT TESTED, not pass |
| Azure reliability | Earlier #249 administrative issue closure lacks a conclusive original gateway-503 fix | Explicit release gate pending |

**Current outcome:** `DEV_HOSTED_FEATURE3_ACCEPTANCE=BLOCKED`, `HOSTED_SQL_APPLIED=false`, `REAL_SIGNED_TENANT_E2E=false`, `GPU_STARTED=false`, `PAID_INFERENCE=false`.

The user asked for hosted DEV acceptance. We performed the safe read-only portions against the genuine target. To complete a real PASS requires separately approved chronological seven-version DEV migration rollout with verified restore/rollback, source deploy and flags, real current owner/editor/viewer/independent-curator identities, licensed garment/model rights and consent, genuine private SHA image upload, and actual signed role/revocation/foreign shop tests. Paid FASHN tryon-v1.6 remains disabled absent explicit billing authorization and rights. No secrets, PII, or WineShopPOS data was read.
