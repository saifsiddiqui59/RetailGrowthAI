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


## 2026-10-28 — Later exact source/CI and coordinator status
- #574 migration coordinator integration merged `23efadf389a16fccab775bd15eadb9ad204c83ef`; independent main #40760090295 4/4 PASS.
- #562 staged private output adapter merged `3749e7119d8721224f3c1091989751df0435fc09`; independent main #40760987558 4/4 PASS.
- #576 official Commons real CC0 garment source byte/license verifier merged `a16c137059b77d382dfff5da380435ade07c7d5b`; one-off real source #40760612959 PASS; independent main #40761570610 4/4 PASS.
- #571 FASHN tryon-v1.6 **offline** six-garment-human-review quality gate merged `c76b46a0f32f91ad36a9c6bdd8e84e930e19cec9`. Immediate main CI #40762142732 was CANCELLED by a separate Azure #249 main commit; later cumulative main #40762519947 on `3722e98f70f82a964ac6d2652649b0770a87daf7` **4/4 PASS**, which includes #571. The separate one-job Azure #249 diagnostic #40762520040 succeeded but is not a substitute for four CI jobs.
- Cross-feature packets #561 and signed import/review UI #563 remain OPEN/unmerged source 4/4. A coordinator merge of #563 returned GitHub 405 because another team modified base `main` concurrently; no partial/inconsistent merge happened. Re-review new main and independent 4/4 before merge; do not silently force it.
- Actual virtual try-on inference still **NOT RUN**, because real signed consented person/model and tenant-approved original product and a funded provider call are absent. Real public-domain garment-image rights are **verified for only one particular photo**; actual human output image not created or evaluated, no fake pass.
- Live hosted DEV acceptance still **BLOCKED** and unchanged: the original connected project showed 24 applied migrations, seven newer source-only ones missing; no signed independent curator credentials and no approved model. No hosted DDL, model GPU, provider charges, Azure deployment or WineShopPOS changes.
