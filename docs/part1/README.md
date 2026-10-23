# Part 1 completion — isolated source integration

Baseline: `main` `80f6bdac4c2c54ca1b2836bf2297e849e296516e` (four successful CI jobs, run 40026278799). Integration branch: `feat/part1-completion`. Only the final Coordinator may merge this branch to `main`.

This sprint adds Creative Studio to the existing dashboard. Existing campaign, Auth, approval, trial/quota and FFmpeg functionality is reused. No deployment, hosted database write, real email delivery, paid provider call or charging is authorized by a source merge.

| Workstream | Task branch | Exclusive implementation and evidence |
| --- | --- | --- |
| A Poster engine | `feat/p1-poster-engine` | `poster-engine/**`, `tests/media/test_poster_engine.py`, `POSTER_ENGINE.md` |
| B Creative Studio | `feat/p1-creative-studio-ui` | `frontend/src/features/creative/**`, minimal campaign child mount, new creative unit/browser tests, `CREATIVE_STUDIO_UI.md` |
| C Private poster backend | `feat/p1-poster-storage` | new `poster_*.py`, additive poster migrations and API/SQL tests, `POSTER_BACKEND.md` |
| D Notification emails | `feat/p1-email-notifications` | new `notification_*.py`, additive notification migrations and tests, `EMAIL_NOTIFICATIONS.md` |
| E Subscription readiness | `feat/p1-subscription-readiness` | isolated lifecycle/budget policy and tests, `SUBSCRIPTION_READINESS.md` |
| F Diagnostics and QA | `feat/p1-performance-hardening` | isolated request diagnostics, role regressions and tests, `PERFORMANCE_QA.md` |
| Part 1 lead | `feat/p1-completion-wiring` | CI discovery, root integration/wiring, dependency/package configuration, cross-component QA and final handoff |

All task PRs target `feat/part1-completion`. The Part 1 lead reviews and merges internal PRs after the actual four Actions jobs pass. Part 2/3 branches and the live DEV operator's work are untouched. Shared canonical documents and public v1 contracts remain unchanged; proposed additive contracts and rollout notes are recorded here for final Coordinator reconciliation.

## Compatibility requirements

- Keep existing `instagram.banner_asset_id` semantics and canonical campaign v1 shape.
- Poster drafts/jobs are additive; do not widen shared publishing, premium, outbox or subscription-ledger constraints.
- Recheck active tenant membership, asset lineage and rights on request, worker execution, attachment and signed download.
- Default-off server features require a reviewed migration, approved deployment and controlled verification before activation.
- Confirmation/recovery templates and in-app approval already exist. SMTP and controlled inbox delivery remain external gates; never reuse WineShopPOS secrets.
- Trial/atomic quota enforcement remains authoritative. No gateway, real charging or self-service paid upgrade is enabled.

## Verification

The existing four non-deploy CI jobs remain mandatory. They discover the new Python/API/reliability tests, creative frontend/Playwright tests, poster media tests and disposable poster/notification SQL denial tests. A green job is source evidence only. Exact task PR, merge and integration-head evidence will be recorded in `FINAL_HANDOFF.md`.
