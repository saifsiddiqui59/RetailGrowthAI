# Feature2 real AI cost reservation gate — source only

PR/issue: Feature #2 integration [#403](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/403).
This is a **SQL proposal and backend facade** kept outside executable\n\`supabase/migrations\` to preserve the coordinator-reviewed manifest. It is not a hosted database change. Do not apply to RetailGrowthAI DEV or PROD without normal migration
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

**Important manifest gate:** Reviewed SQL is stored only under `docs/feature2/sql/PROPOSED_20261026_feature2_ai_cost_ledger.sql`. Future coordinator-approved migration integration must choose a nonconflicting version number, update the immutable manifest deliberately, run full disposable DB security tests and obtain protected DEV migration approval before enabling any model calls.


## 2026-10-26 — Superseding SOURCE SQL integration (not DEV application)
- Actual reviewed versioned candidate landed via #431: `supabase/migrations/20261026194000_feature2_ai_cost_ledger.sql`. Historical proposal remains at `docs/feature2/sql/PROPOSED_20261026_feature2_ai_cost_ledger.sql` for audit, but CI now applies the versioned migration once in disposable PostgreSQL only. The old ad-hoc proposal was not applied to hosted DEV.
- 5-arg reserve `p_request_id`, per-shop unique request, RG005 replay denial, conservative ceil micro-USD plus existing serial subscription row lock/role/subscription/budget checks. Winning request ID replay after settlement/unknown ACK is denied. Python signed HTTP path carries the draft `submission_id` as reserve ID (#433); new distinct HTTP submission IDs remain distinct billable intent. Do not blindly retry requests.
- Verified disposable two blocked sessions: USD0.004 cap, two USD0.003 requests, one success and one AI_QUOTA_EXCEEDED, then replay of winner RG005. CI exact #40391854844/#40391861411, independent main #40392713409 all 4 green.
- Latest hosted read-only prefix 21 through 20261026152102; later Feature3 20261026173000 precedes Feature2 20261026194000 in source. Blind `supabase db push` is prohibited. Written protected DDL/backup/restore approval, separately authorized nonzero expiring budget and Microsoft regional rates/prices still absent. No Azure paid execution, hosted writes or PROD.


## 2026-10-26 — Confirmed published model pricing does not authorize DB spending
- Protected read-only OIDC #40401262949 proved official South India GPT-4.1-mini Regional Standard uncached input $0.44 and output $1.76 per 1M token from Microsoft 1K-token meters. Source #437 validates unit conversion. Owner's USD0.20 TOTAL test ceiling is distinct from hosted DDL permission and is not an expiring shop budget row. With no hosted ledger tables, zero paid inference is the only safe state. Do not bypass the service-role reservation, subscription, model credentials, or ROOT synthetic user gates.
