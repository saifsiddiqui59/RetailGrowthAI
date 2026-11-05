# Feature3 F3-09 — owned private media lookup, 2026-11-05

- Source-only draft restore and save integrity: `Feature3SecureDraftWorkspace` now uses the same `feature3DraftMediaReady` permission hint for both flows. It accepts only an own-property entry in the current host's private image map, with loaded natural image dimensions. Inherited `constructor`, `toString`, `__proto__`, and arbitrary prototype media entries cannot masquerade as a registered image.
- Automated Node regression covers valid own-image input, inherited metadata, corrupted dimensions and direct component source use. The backend JWT/RLS and immutable media rights continue to be authoritative. No hosted signed user or commercial media testing is asserted.
- Original work packages: F3-09 and F3-13; this is a distinct source gap, not a new original task ID or a new full package DONE.
- Current `main` baseline: `837943de3507c3021b16b4f54e2044f2e9418266`, after DEV-source acceptance PR #875. CI and review to be verified on final head.
- Shared root route, authentic DEV/PROD, paid GPU, hosted SQL and WineShopPOS were not modified. No new feature flag enabled.
