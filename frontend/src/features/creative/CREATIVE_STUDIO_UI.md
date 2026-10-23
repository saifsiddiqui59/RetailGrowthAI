# RetailGrowthAI Part 1 — Creative Studio frontend handoff

## Implemented source (not yet released)

- Existing /campaigns workspace now includes PosterStudio after the saved-day Reel area. Original Auth, onboarding approval, campaign editing, render, media upload and subscriptions are preserved.
- Actual live browser Canvas poster preview and PNG export, based on selected campaign day's topic and Reel CTA.
- Three design layouts: editorial, bold, minimal; 1080×1080 square and 1080×1350 portrait, business brand, background/accent colors, optional human-approved offer, and local merchant photo.
- PNG export is disabled until a photo is selected and merchant confirms commercial rights. JPG/PNG/WebP up to 25 MiB; 8192 pixels per side and 24 megapixels.
- Responsive mobile and desktop. Image stays in browser: PNG is local, not a stored authenticated media asset. Placeholder cannot be downloaded without a product photo.
- No paid image generation, external stock media, social publisher, Wan API, SMTP or WineShopPOS integration.

## Tests and next gate

- Run: node --test tests/frontend/poster-canvas.test.mjs. Covers all six layouts, real campaign text and opt-in offers, placeholder, input validation and crop safety.
- Existing four GitHub CI checks are mandatory on the PR and integration head.
- Backend Pillow poster generator in poster-engine/render.py is separately runnable; browser preview and Pillow output may differ in typography.
- **Still needed for production SaaS**: secured poster API/job and draft persistence, private asset registration, authorized photo/rights checks on all stages, signed downloads, campaign banner attachment, trial/quotas, final E2E and the owner-approved existing DEV release.
- No live browser/deployment claim until final Part 1 integration is approved, merged to main and separately released.
