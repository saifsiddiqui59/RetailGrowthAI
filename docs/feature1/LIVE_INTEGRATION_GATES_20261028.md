# Feature #1 — live integration and release gates (2026-10-28)

## Scope and evidence

**Owned React UI, source security and offline-mocked acceptance are complete. Live product acceptance is not complete.** No independently-owned Feature #1 code rebuild is necessary without a newly reproduced defect or an approved upstream live API contract.

- Last Feature #1 code change: [PR #557](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/557), merged as `16992ae4200f56a93a7ce90fe590510f7cc70a85`. Its [exact-head PR run #40730871241](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40730871241) passed 4/4. Independently inspected [post-merge main run #40731459701](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40731459701): frontend, Python, FFmpeg and isolated Supabase jobs each completed SUCCESS. **This does not certify later main commits or a hosted release.**
- Existing [offline acceptance matrix](OFFLINE_ACCEPTANCE_20261028.md) tracks P1-01 through P2-02, including three distinct **fictional**, opt-in retailer samples, 320px Playwright, 100+1 microsecond-safe JWT/RLS media history and revocation-on-refetch private original UPLOAD preview.
- Existing `frontend/src/App.jsx` mounts dedicated `RecentCampaignCalendar`, `MediaLibrary` and `RetailerInbox` routes; `WorkspacePage` remains only the non-live social/publishing guide and fictional preview on the active routes. No fake live provider accounts or receipts are displayed.
- Tracking: [Feature #1 external contract issue #489](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/489). This issue's original inbox source-contract blocker is superseded by merged #510; hosted release remains pending.

## Remaining work, strictly separated by owner

| Gate | Authoritative dependency | Do not claim before acceptance |
| --- | --- | --- |
| P1-02 connected social accounts | Part 2 lead and coordinator approve/version authenticated current-shop OAuth identity/status/scopes/consent/revoke read + action contracts; freeze shared interface, explicit release authorization | No real connected channel, token access or enabled connect/disconnect UI |
| P1-03 publishing history | Part 2 and coordinator provide source-approved JWT/RLS, bounded per-shop schedule, approved version, UTC and IANA timezone, verified provider receipt, retry/failure/audit paging | Draft calendar is not a sent post; sample receipt is not a provider confirmation |
| P1-04 retailer inbox **hosted activation** | Database coordinator reviews full chronological migration chain including `20261028173000_feature1_retailer_inbox.sql`; separately authorized DEV apply and frontend release | Source SQL/React tests are green, but the hosted inbox migration and signed-in behavior are not verified |
| P2-02 STOCK/GENERATED private previews | Trusted per-image commercial rights, same-shop private object read and revocation contract; approved media provenance | Metadata or user-declared license alone does not authorize byte previews |
| Overall live readiness | Explicit signed-in OWNER/EDITOR/VIEWER/revoked/ROOT acceptance in an approved DEV test environment, current real media permissions, original Azure #249 HTTP reliability | No production-ready or 4/4 **hosted** E2E claim |

## Safe execution sequence once the responsible owner explicitly clears a gate

1. **Freeze the actual shared contract:** coordinator reviews Part 2 versioned fields and authenticated endpoints; retain current Feature #1 fail-closed default, including disabled provider write controls. Feature #1 never invents its own OAuth API or stores provider tokens in the browser.
2. **Build a mock contract test first:** use the already passing separate-shop fictional fixtures, then add actual response-shape, shop/JWT/role/expiry/duplicate/unrecognized-field/secret-leak denials. Test revoked membership, unauthorized write attempts, timezone changes, forged receipts and cancellation. Never transform fixture receipts into live examples.
3. **Database rollout requires separate authorization:** read-only confirm existing RetailGrowthAI DEV migration history, exact pending review order, grants and rollback procedure before applying anything. Do not apply migration from this document. Inspect actual signed JWT OWNER/EDITOR/VIEWER/revoked access against a controlled RetailGrowthAI-only disposable test shop after approval. ROOT notifications remain separate.
4. **Release only after explicit approval:** first verify all four CI jobs on the exact reviewed head and independently on merged main. For a separately authorized DEV frontend release, use the existing tagged Free SWA and public-only environment variables; never provision extra paid services or use WineShopPOS.
5. **Acceptance:** test a real consented provider identity/receipt only when Part 2 transport and real tenant authorization have separately passed. Verify current-shop switching, login/signout, mobile 320px and desktop UX, inbox read state, old Blob URL revocation and failure/unavailable states. Record actual deployment SHA and signed-in evidence; do not infer success from static-page HTTP smoke.

## No-wait Feature #1 status

The owner-directed no-wait offline work has been exercised and merged. All further genuine **live** gates depend on authorized Part 2 contract, hosted DB deployment, external license authority or actual signed-in acceptance. Repeating fictional fixtures or enabling default-off integrations does not resolve them. No GPU, provider API call, paid resource, Supabase hosted SQL, Azure deployment, PROD or WineShopPOS write is performed by this audit.
