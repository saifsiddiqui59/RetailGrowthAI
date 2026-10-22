# Workstream B — campaign API boundary

The v1 handlers are implemented as dependency-injected application services in
service.py, not as deployed Azure Functions. This deliberate separation lets the
coordinator connect the Supabase authentication + RLS storage owned by Chat A and
a durable Azure queue after provisioned RetailGrowthAI DEV resources exist.

POST /api/campaigns should call CampaignService.post_campaign(Authorization, body)
and return its 202 status/payload. GET /api/campaigns/{id} should call
get_campaign(Authorization, id). Never expose run_planning_job publicly.
It must be invoked only from a trusted queue consumer.

Required dependencies have **no insecure defaults**:
- token_verifier: validates the signature, expiry, audience and issuer of the JWT
  (not just parsing it), returns the authenticated user UUID.
- membership_checker: checks ACTIVE membership for that user/shop.
- asset_checker: checks that each UUID belongs to the same shop and can be used.
- store: durable save_pending/load_pending/save_draft/fail/get with RLS-aware access.
- enqueue_planning: durable queue with retries/idempotency.
- provider: MockFoundryProvider for offline tests, AzureFoundryProvider with
  a separately reviewed authenticated real client for future live generation.

Planning jobs perform **a second membership and asset check**; revoked access
blocks the job. Review findings travel to the store separately and never change
the canonical v1 day JSON. Claims, discounts, regulated content and publishing
always require human review as applicable. No social auto-posting exists.

There is no configured Azure Function trigger, HTTP listener, JWT verifier,
database connection, durable queue or live Azure AI Foundry deployment yet.
Do not label this an API that is live or production ready.
