# Feature #2 F2-03 — Unicode prompt trust-boundary hardening (2026-10-30)

**Status:** IN PROGRESS (source-only, not integrated DONE). Original centralized task ID: `F2-03` of 38. This branch is stacked on existing F2-03 post-CAS fix PR #742, which itself is stacked on unified draft PR #551. Do not merge independently into main or duplicate the prior post-CAS fix.

## Source changes
- Reject invisible/bidi/format, private-use, unassigned and Unicode line-separator controls from original retailer prompts and from mocked injected provider responses.
- Keep legitimate Hindi/Marathi Devanagari virama + ZWJ/ZWNJ + letter conjunct sequences; do not strip or normalize the original request.
- Exclude authorized retailer profile fields containing unsafe Unicode controls from generated prompt context rather than silently treating them as verified facts.
- Extend synthetic-only tests for hidden-control original requests, provider output, signed draft CAS, and valid Indic conjuncts. No live AI, GPU, paid inference, hosted SQL, approval, deployment, PROD, or WineShopPOS edits.

## Verification and integration gates
- Targeted: `uv run --project ai-agents pytest -q tests/ai/test_prompt_improver.py` (run in the repository's supported CI environment, adjusting PYTHONPATH according to existing workflow).
- Exact-head four-job PR CI required; do not mark tests passed until actual run evidence is inspected.
- Coordinator reviews the stack (#551 → #742 → this PR), integrates source to main, verifies fresh 4/4 main CI and records evidence in `coordination/task_progress.json`. No worker-side edit to shared/canonical docs.
- **Dependency:** `F2-CREATIVE-SOURCE`, coordinator; required output: accepted Creative Director runtime and review contracts on main, fresh 4/4 CI; acceptance: current JWT/RLS editor and draft CAS actually enforce tenant scope, signed reviewer decision and review-only rights at commit time.
- **Additional release gate:** `ISSUE-650`, coordinator; required output: Azure Functions package within protected 120-entry ZIP constraint, exact-head import closure tests passing.
- Real signed editor JWT/RLS, durable hosted proposal storage and actual human review remain unverified. Mocked tests are not production approvals.

## Task evidence
GitHub PR and exact commit SHA are the source of truth. This handoff does **not** assert integrated completion or new successful CI until independently checked.
