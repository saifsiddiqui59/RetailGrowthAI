# Feature #3 F3-09/F3-13 — signed provider state visibility

Source-only independent fix to `Feature3SecureDraftWorkspace.jsx`.

## Root cause
`scopedFeature3WorkspaceValue(state, scope, fallback, feature3Api)` requires an exact `provider` match to show private state. Initial and reset states carry `provider: feature3Api`, but the busy and status setter closures omitted `provider`. Consequently status messages and busy flags always fell back to empty/false even for the current signed session, allowing concurrent UI operations and hiding errors.

## Repair
Bind both busy and status setter writes to the exact signed `feature3Api` provider identity. Existing scope/provider guard hides prior session state on first paint. Add deterministic source/selector regression to `tests/frontend/feature3-workspace-scope.test.mjs`.

Original task IDs: F3-09 (studio history/review state), F3-13 (tenant/session negative regressions). This does not create a hosted API or verify real login, output, licensed rights or publication. No GPU, paid inference, SQL, PROD or WineShopPOS. Targeted command: `node --test tests/frontend/feature3-workspace-scope.test.mjs`; local tests unavailable, require exact-head 4/4 PR CI, coordinator merge and fresh main 4/4 before any integration claim.

Blocked acceptance: `#471/#325` signed private PNG route (coordinator), `F3-LICENSED-MEDIA` reviewed originals (Feature3), `#249` hosted Azure gateway (reliability), genuine two-tenant JWT/RLS negative browser verification (coordinator/Feature3). **Neither task is integrated DONE** from this source patch.
