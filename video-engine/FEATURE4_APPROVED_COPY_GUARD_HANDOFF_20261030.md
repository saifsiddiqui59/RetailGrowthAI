# Feature #4 F4-13 — exact-match reviewed copy guard (2026-10-30)

Scope: source-only fix in the trusted `rg_video_v2` → `creative_reel_v1` compiler. The coordinator remains responsible for actual authenticated immutable approval snapshots, JWT/RLS, private media grants, and integration.

## Root cause and change
`approved_text` was assumed to be a list. If an upstream malformed trusted snapshot provided a string, Python substring membership could accidentally accept a shorter unreviewed headline. The compiler now rejects any non-list, empty list, or list containing non-string/empty entries before checking exact approved headlines/offers. A non-dictionary `script` fails with `CreativeContractError` instead of an uncaught attribute error.

## QA and release state
- New deterministic regression cases: string, tuple, mapping, empty list, invalid members, non-mapping script, and a partial headline; existing valid structured list must remain accepted.
- No external media, AI/GPU calls, deployment, database changes, or customer samples.
- Targeted local test: **not executed in this GitHub-only worker environment**. Exact-head GitHub CI must be inspected; do not infer a pass from the code review.
- Task F4-13: **source patch proposed; NOT integrated DONE** until coordinator accepts the PR, merges the parent chain, and verifies fresh main 4/4.
- Dependencies/acceptance: F4-23 coordinator must reconcile PR #322 and this stacked PR; F4-24 coordinator must prove JWT/RLS-approved snapshot in DEV. Actual licensed retailer media and human release approval remain separate.
