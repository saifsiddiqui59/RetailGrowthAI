# Feature2 real AI cost reservation gate — source only

PR/issue: Feature #2 integration [#403](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/403).
This is a **new migration proposal and backend facade**, not a hosted database
change. Do not apply to RetailGrowthAI DEV or PROD without normal migration
review, disposable Supabase CI and protected DEV approval.

## Contract and strict zero-spend default

- `shop_ai_budget_controls` has **no auto-created rows**, `enabled=false`
  by default, zero USD cap and no approval expiration.
- Only an operator using a trusted *server-side* service role can provision a
  positive limit, choose an expiration and deliberately enable a shop.
  Browser JWTs cannot grant, insert or update budgets/reservations.
- `feature2_reserve_ai_budget` is a service-role-only SECURITY DEFINER RPC.
  It checks real active OWNER/EDITOR membership for the JWT-verified actor;
  serializes on the existing per-shop subscription row with `FOR UPDATE`;
  checks active period, approved spend cap and fixed plan call limits.
- The monetary reservation is rounded **up** to six decimal USD places and
  a single call cannot exceed USD 0.05. The separate AI adapters compute a
  worst-case token bill first; no reservation means no HTTPS model request.
- `feature2_settle_ai_budget` is backend-only and confirms actual charge
  not exceeding the reservation. Missing, timed-out and unsettled receipts
  conservatively continue to count at their reserved maximum. No automatic
  replay on ambiguous Azure/Foundry acknowledgement.
- Uses separate AI spend tables instead of broadening the existing
  `shop_usage_reservations.operation` CHECK or altering render/campaign quotas.

## Remaining integration dependencies

1. Review/merge isolated migration with disposable SQL concurrency/security
   tests. **Do not apply to hosted DEV until authorized**.
2. Connect `Feature2BudgetStore` to the signed OWNER/EDITOR API, using the
   JWT-verified actor; never accept cost amount, model, verified retailer
   profile or service-role credential from the browser.
3. Settle the actual amount after a genuine model response; consume/reserve
   maximum on timeout. Introduce explicit opt-in UI and provider
   enablement only with a verified existing Azure Foundry deployment,
   secure model credentials, verified pricing and cost/operator approval.
4. Validate 7-day model copy/poster/video briefs as DRAFT in protected DEV
   with source-backed licensed media; collect actual token usage evidence.
   Deterministic fallback must be honestly labeled, not called real AI.
5. All cloud deployment/subscription changes and PROD are separately
   approval-gated; no WineShopPOS resources ever changed.

**Result claimed here:** source implementation and offline tests, NOT
real paid inference, production readiness or hosted quota/RLS evidence.
