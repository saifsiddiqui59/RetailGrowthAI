# Feature #3 F3-13 / F3-09 — approved copy and workspace scope hardening

Source-only security/robustness change. No hosted integration or production media acceptance.

## Change
- Fail closed on null, undefined, nonobject and array workspace context without crashing the editor.
- Reject ASCII/C1 controls and Unicode bidirectional overrides/isolates in displayed "APPROVED" headline, CTA, offer text or brand name, preventing misleading control-character rendering in local poster previews.
- Reject non-safe or out-of-range approved-version values; preserve ordinary Hindi/Indic text and existing valid approved content.
- Add deterministic Node tests for malformed contexts, spoofed offers and legitimate Indic copy.

## Evidence / scope
- Original task IDs: F3-13 (cross-tenant/security regressions), F3-09 (studio review-state presentation).
- Branch: `feat/feature3-approved-copy-scope-fence-20261030`.
- Targeted test command: `node --test tests/frontend/feature3-context.test.mjs`.
- No local test was run by the GitHub connector; exact-head four-job PR CI must be inspected before coordinator integration.
- Does not authorize images, models, rights, publication, signed DEV, GPU or payment; server JWT/RLS and current independent source approval remain mandatory.
- Coordinator alone reviews/merges and records `coordination/task_progress.json` evidence. **Neither F3-13 nor F3-09 is DONE** without hosted acceptance and fresh 4/4 postmerge main CI.

## Blockers
- `F3-LICENSED-MEDIA` / Feature #3: genuine original garment/model rights and independent human approval.
- `#471/#325` / coordinator: mounted signed private output route and live current-rights checks.
- `#249` / Azure reliability: observed signed DEV gateway response and 503 resolution.
- `F3-13` hosted negative acceptance / coordinator + Feature #3: real signed owner/editor/VIEWER/foreign/revoked role denials, not fixture-only results.

No GPU, paid inference, hosted SQL, PROD or WineShopPOS change.
