# Feature #2 — Protected DEV signed Prompt Improver canary

**State:** source merged in [PR #397](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/397) as `8d9696a484d4b7b7b77ef0362b7364b977f73353`. This is **NOT** evidence of a hosted signed-in canary. Run only through the approved protected DEV workflow; no direct production/other app actions.

## Why there are two Feature2 acceptance modes

- `feature2-prompt`: isolated deterministic prompt preview. No live Google Trends requirement, no media upload, no DRAFT POST, no paid Foundry/Hugging Face or GPU, no FFmpeg install. It *still* creates two temporary, ROOT-approved RetailGrowthAI DEV identities/shops to exercise real JWT+RLS; checks OWNER and EDITOR 200, foreign/VIEWER 403/404, invalid bearer 401, forged profile/model 400, zero paid inference and before/after zero saved drafts.
- `feature2`: original full trend→media→DRAFT→RLS GET mode. Retains a **real unexpired clothing signal** preflight *before* fixtures and requires licensed/registered media. No source-faking or using generic Google RSS as fashion evidence. This path still cannot pass with zero relevant clothing trends.

## Exact approval-gated procedure (manual operator)

1. GitHub Actions → `RetailGrowthAI owner-authorized DEV temporary test accounts + live tenant canary` → Run workflow on **main**. Select `feature2-prompt`, and supply the workflow's documented static DEV-only approval code. The code is **not** ROOT onboarding approval.
2. The protected `dev` environment must grant execution, and a ROOT operator must **separately approve only the two newly generated disposable `@example.invalid` onboarding requests**. Do not approve existing real retailer requests as part of this canary.
3. The runner performs a bounded unauthenticated Azure 401+X-Request-ID ingress check on the standard four API paths plus `POST /api/shops/{id}/improve-prompt` **before** creating users. It fails closed if Azure #249 intercepts the request or the Functions handler does not answer in budget.
4. After ROOT-approved disposable onboarding, the runner uses only ordinary signed user JWTs for exact canary-owned profile/membership modifications and prompt POSTs. OWNER must get a deterministic `NEEDS_REVIEW` preview with original intent, checked business profile, all six output formats and `paid_inference_calls=0`; foreign and VIEWER fail; OWNER-only role change to EDITOR allows EDITOR preview. Saved draft readbacks must remain empty.
5. In all outcomes, `finally` limits cleanup to the nonce-named two test user IDs/shops and checks no orphan drafts. **Inspect logs for all cleanup checks**. If cleanup fails, escalate immediately and do not run again until the exact orphan identity is reconciled; never delete unrelated accounts.
6. Record exact run ID, overall conclusion, OWNER/VIEWER/EDITOR and denial markers, exact cleanup evidence, and any Azure #249 preflight failure in `docs/PROJECT_STATE.md`, `docs/WORK_LOG.md`, and `ai-agents/FEATURE2_HANDOFF.md`. No positive hosted acceptance claim based on unit tests or public SPA 200.

## Explicit limitations

This mode is HTTP-client acceptance (not Playwright on a physically signed-in mobile/browser), uses *invalid* bearer denial rather than waiting for expiry of a genuinely signed JWT, and does not demonstrate completed licensed-media content-draft persistence. Those separate tasks remain open. If the ROOT operator is not present or approval not granted, **do not manually create users with secret keys, use test-only role bypasses, or mark the run passed.**

**Cost:** existing DEV Supabase + Azure Functions; no additional always-on service, GPU or paid model request. The protected workflow alone holds the DEV service key; it must never appear in a browser, CI artifact or logs.
