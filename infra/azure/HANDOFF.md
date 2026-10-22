# Coordinator handoff — feat/p1-azure-deploy-prep

Owned paths changed: infra/azure/** and scripts/deploy/** only. No Azure resources created/deployed; no Supabase mutations; WineShopPOS untouched.

Prepared Bicep DEV-only StorageV2 Standard_LRS, Flex Consumption Python Functions and exact two queue names, bounded scale, private deployment container and CORS. Added deployment ZIP packager for nested renderer/ai_agents/approved Linux FFmpeg with tested queue host concurrency and deterministic ZIP; read-only checks and approval-gated scripts.

NEXT (coordinator-owned):
1. Review and document Flex cost/shared-key/timeout decisions in docs/DECISIONS.md; update PROJECT_STATE.md, NEXT_TASK.md and append WORK_LOG.md when merged.
2. Add bash scripts/deploy/check.sh into .github/** CI (this branch cannot edit coordinator-owned workflow). Four existing CI jobs will not exercise it.
3. Require explicit approval for existing RetailGrowthAI DEV Supabase migrations, new Azure resource group/resources, protected backend credentials, audit of licensed FFmpeg binaries and deployment.
4. Reconcile renderer's 780-second subprocess timeout versus 4-minute function timeout and DB lease using measured video benchmarks; adjust code/migration under separate ownership, or choose approved Container Apps Jobs.
5. Run hosted function indexing, real auth/JWT/CORS, user-licensed uploads, cross-shop/VIEWER denial, queue retry/poison, signed MP4, 30-second E2E and cost/monitoring tests.

Status: preparation only; no deployment or end-to-end verification.
