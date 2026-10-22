# Workstream B handoff — coordinator integration

Owned scope: ai-agents/**, azure-functions/campaign-api/**, tests/ai/**.
Canonical docs remain coordinator-owned and unchanged.

- Planner accepts the exact INTERFACES_V1.md brief fields; en-IN, LinkedIn
  and Instagram are mandatory for the current mocked 7-day pilot.
- Mock generation produces 1-7 v1 day records, each with a 30-second
  three-segment manifest. Asset UUIDs are never synthesized; clients must
  supply authorized assets. There is **no video render** and no live Foundry.
- AzureFoundryProvider needs a reviewed real model-client implementation and
  robust factuality/prompt-injection policy before enabling live credentials.
- Coordinator + Workstream A must wire verified Supabase JWTs, ACTIVE tenant
  membership, private media rights and RLS-aware durable persistence.
- Coordinator must wire a durable queue and worker retries/idempotency; HTTP
  service methods are not Azure Function endpoints and are not deployed.
- Generated review_status stays DRAFT. Reviewer issues/approval flags are
  separate persistence metadata (never bypass human approval).
- The API boundary requires all dependencies and rechecks permission in
  the worker. Integration tests with real isolated Supabase DEV projects
  remain blocked until that infrastructure is provisioned.
- Regulated industries are marked for policy review; the deterministic
  planner intentionally omits promotional offers for regulated briefs.
- python pytest CI validates mock/planning/review/security boundary behavior.
  Cross-tenant database RLS testing remains Workstream A's responsibility.
