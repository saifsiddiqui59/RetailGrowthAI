# Feature #3 — Reduced current delivery scope (owner decision, 2026-10-26)

## Deferred from THIS development sprint

1. Visual inspection of genuine upstream Indian-themed/OpenPeople source images.
2. Independently investigating/verifying commercial rights of those actual upstream images.
3. Hosted DEV deployment and live end-to-end browser acceptance tests.

**Important boundary:** Defer these activities, not the legal or technical
restrictions. No third-party model is deemed commercially licensed by
omission. External model assets stay PENDING_REVIEW and unavailable in
customer posters, try-on, videos, shared catalog or production until
applicable rights are established. Existing rights callbacks, access
checks, approval/revocation and image-integrity rules are unchanged.
No real human still is imported to cloud, and hosted readiness cannot
be claimed from offline CI.

## Current deliverables completed in Feature #3-owned code

- A saved-model UI mode in `Feature3StudioPanel.jsx`. It uses an image
  layer from a **currently approved model** only when the authenticated
  host separately supplies a registered, already-loaded **private** image
  in `authenticatedModelImageMap`.
- `feature3-approved-models.mjs` filters model rows for shop ownership,
  approved status, supported use, existing image assets and attribution.
  The filter is defensive UI only; it is NEVER proof of server rights.
- Mounted `PosterStudio.jsx` accepts additive optional host props
  `approvedModels` and `authenticatedModelImageMap`; defaults are empty.
  Existing v1 campaign draft/save/queue/private download still works
  without Feature #3 model catalog integration. The new mode uses current
  CPU v2 local-draft output; it does not call GPU models or falsely
  describe a source still as an actual dressed virtual try-on.
- `model_catalog_projection_v2.py` prepares a minimal server-authored
  model-picker DTO only after existing `checked_model_for_use` rights
  verification and a separate registered-private-media callback bound to
  the requesting shop. No signed CDN URL, storage path or token in DTO.
- `model_reference_v2.py` derives a reusable private reference for
  poster/try-on/video with an AUTHORITATIVE revision from a current
  tenant/rights callback. Key fingerprints include shop, model image
  digest, rights revision, usage, pose, optional garment digest and
  render profile; changing a rights revision invalidates cached results.
  Cache reuse also needs the immutable output reauthorized separately.
  The receipt does **not** start a GPU job, assert garment photo is
  authorized, create a moving video, or approve image-generation costs.
- Added source-only Node/Python positive and negative tests for these
  adapters. They use synthetic fixtures and/or mocked authoritative
  callbacks, NOT hosted identities, genuine human models or paid GPU.

## Still pending, even with reduced scope

**Coordinator-owned P0:** freeze additive catalog DB/RLS and signed private
image API; provide authenticated `approvedModels` and authorized decoded
`authenticatedModelImageMap` to the existing mounted PosterStudio;
implement real rights-rechecking poster save/renderer paths; review
usage/quotas, model approval/revocation, and immutable private outputs.
No feature branch may silently change Supabase migrations, shared HTTP
contracts, frontend App root or other feature branches.

**GPU optional/P1:** retain Create New AI Model via FLUX.2 Klein 4B
approved checkpoint, account quotas, real on-demand GPU and appropriate
license/cost/region gates. Retain FASHN adapter behind commercially
permitted parser/license and actual product-fidelity gates. Feature #4/#5
leads own their motion/composition engines; this branch only offers
private reference receipts, not motion/inference itself.

**CI:** all new code must pass the four branch/PR GitHub checks on the
new exact head. Do not conflate this with production/hosted E2E.

**Cost:** no new Azure instance, no paid inference and no new dependency
needed for this source integration. Private objects and any future inference
will have normal storage/compute costs when intentionally activated.
