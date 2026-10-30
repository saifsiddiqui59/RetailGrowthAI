# Feature #3 — Import-First AI Fashion Model Library (Cost-First)

## Product decision

Import **existing commercially approved synthetic adult character IMAGE assets**
first, create a low-cost shared fashion model library, and **keep Create New
AI Model** as an OPTIONAL premium/custom feature. Both paths produce the same
`retailgrowth.model-library.v1` asset contract; do not build two libraries.

This is a source/test implementation in `poster-engine/model_library_v2.py`,
not a deployed SaaS import button, Supabase table or scheduled downloader.
NO GPU inference occurs on import.

| Step | Imported existing model | Newly AI-created model |
| --- | --- | --- |
| Ingest | Private staged PNG/JPEG/WebP, independently verified rights | Existing FLUX 4B worker generates a locally staged image when approved |
| Cost | Zero IMAGE-GENERATION GPU calls; storage/traffic still have costs | GPU only when chosen, with cost/accounting approval |
| Identity | One immutable SHA256-based model reference | Same reference contract |
| Review | Human visual/licensing approval | Same review gate |
| Storage | Immutable PRIVATE blob, shop-scoped or vetted platform-wide | Same storage/registry |
| Reuse | Poster template, VTON model/person still, video identity reference | Same reusable consumers |

## Where can we legitimately import pre-created humans?

Promising FIRST seed source: [MakeHuman core](https://www.makehumancommunity.org/about/license.html)
and [MakeHuman upstream LICENSE](https://github.com/makehumancommunity/makehuman/blob/master/LICENSE.md).
Core graphical assets are CC0 and outputs/renderings are not claimed by its
maintainers; third-party community clothes, textures and downloaded assets
**may use DIFFERENT licenses**. Prefer curator-made renders from **core
CC0 assets** for the first batch. Their fashion realism must be reviewed:
a basic 3D render is not automatically a high-end photorealistic fashion model.

A 3D mesh/FBX/GLB import is NOT implemented by this image importer. It
accepts private PNG/JPEG/WebP exports/stills. A later separately reviewed
3D viewer/renderer may ingest 3D meshes if business value warrants it.

Do NOT bulk copy Unsplash/Pexels/social media or a GitHub repository because
the **code** is open source. Explicit licensing of the actual image and
right to curate/re-distribute a shared commercial library is required.
For example Unsplash explicitly restricts building a competing image
library and certain AI-related uses:
https://unsplash.com/license
https://unsplash.com/terms

## Workflow

1. Curator or retailer locally obtains an approved rendered **adult
   synthetic character still**, records source URL, image-specific license,
   evidence digest, any attribution and pose.
2. A trusted backend verifies commercial reuse, rights, available scopes,
   the user/shop's role and whether the platform curator approved global
   redistribution. The browser cannot self-declare itself a curator.
3. `import_model_image` strips image metadata/EXIF, validates dimensions,
   normalizes to PNG, derives deterministic model UUID and exact SHA256 blob
   key, and requests an immutable PRIVATE upload + registry insertion through
   injected, separately authenticated callbacks.
4. The initial library entry is `PENDING_REVIEW`. A separate authorized
   human approval must set `APPROVED` in the database; import is not
   permission to publish. Review data should include pose suitability,
   believable anatomy, clothing fidelity, required attribution and likeness
   clearance for any non-synthetic subject.
5. `checked_model_for_use` must receive the latest server-loaded library
   record and an independent RLS/license/approval callback every time a
   retailer uses it. Shop-private images never resolve for another shop.
   Approved platform models may resolve for multiple tenants.
6. Feed the returned opaque private media reference into the existing
   rights-staged workflow: FASHN-compatible try-on (subject to commercial
   parser clearance), Feature #3 CPU poster, Feature #4 compositor, or
   Feature #5 image-to-video identity/style reference. Do not pass raw Blob
   paths, public URLs or customer tokens directly to browser generators.
7. Cache **approved model + garment + pose + rights version** result to
   prevent duplicate GPU try-on per unchanged creative. A library model
   by itself does NOT magically change outfits or walk in a new video.

## Minimum-cost delivery sequence

**P0, source ready:** offline rights-gated import adapter and negative tests.
**P0, coordinator-owned:** freeze additive catalog schema/RLS (immutable
`model_id`, model image SHA, licence evidence, shop/global scope, review
state, version + attribution); transactional library role/curator authorizer;
private Blob storage callbacks; idempotent unique record and capacity limit;
signed review/preview; revocation/takedown; signed-in OWNER/EDITOR/VIEWER and
cross-tenant E2E.
**P1:** expose UI `Model Library` → `Import Existing` or
`Create New (GPU)`, with unambiguous costs and approval. No new npm
dependency required for initial existing React UI.
**P1:** integrate selected approved model as reference asset in try-on,
Poster Studio and Video Studio, with a role/rights recheck per generation.
**P2:** add gallery images, optional pose bundles/LoRA identities and
controlled, measured new AI model creation. Never silently spend GPU.

## Honest acceptance criteria

- Actual source images curated with demonstrable rights, not mock
  placeholders; license evidence stored, attribution carried.
- Initial catalog of 6–10 **approved adult synthetic model stills** only
  if quality and rights pass, NOT automatically seeded by a download.
- Importing one approved asset has zero generation-model calls, and the
  same model can be safely selected for poster, try-on and video reference.
- New AI creation remains as an **additional option**, feeds exactly the
  same schema and has separate cost caps.
- Actual GPU VTON and I2V footage may require new inference despite
  selecting a saved reference; model library does not fabricate try-on
  results or motion.
- Do not call this cloud-ready until coordinator RLS/Blob/endpoint UI
  and true hosted tenant acceptance tests have passed.

### Engineering entrypoint

`poster-engine/model_library_v2.py`

`tests/media/test_feature3_model_library.py`

The source-only tests use synthetic Pillow images; they do not import
real models from MakeHuman, download datasets, prove CDN terms or perform
GPU work. Canonical docs, shared API/schema and deployments are owned
by coordinator #325; this feature branch must not edit them directly.


### Explicit pre-generated human image candidate — OpenPeople

[Prompt-Haus/OpenPeople](https://github.com/Prompt-Haus/OpenPeople)
contains up to 100 pre-generated synthetic people with studio portraits,
full-body studio postures, casual poses and character sheets. Its README
declares **images CC-BY 4.0**, while the repository's separate software
`LICENSE` is **MIT**. Do not accidentally cite the code MIT license
as the image license. Upstream README also describes the dataset as
testing/development assets and disclaims likeness guarantees, so have
our independent commercial curator confirm desired **SaaS redistribution,
advertising and reference-generation rights**, attribution and any
provider-specific restrictions before populating the public catalog.
Individual faces should be checked for accidental real-person likeness.

Added `openpeople_import_v2.py` to select an already locally staged,
40-character commit-pinned snapshot of:
`openpeople/data/curated/P001..P100/assets/studio_posture.jpg`,
`studio_portrait.jpg`, `amateur_posture.jpg` or
`amateur_selfie.jpg`. It refuses symlinks, forged person IDs,
unlisted paths, missing local files, missing curator verification
and invalid licensed image receipts. No clone/download or cloud API.

`tests/media/test_feature3_openpeople_import.py` performs a real
PRIVATE JPG->PNG normalization and all-three-feature reuse with
synthetic local JPEG fixture only. No upstream binary has yet been
downloaded, shipped in GitHub, added to Azure storage, or approved
as a reusable commercial model.

**Never seed from StyleGAN-Human SHHQ** despite attractive full-body
examples: its dataset agreement explicitly restricts use to
**non-commercial research** and forbids redistribution.
https://github.com/stylegan-human/StyleGAN-Human/blob/main/docs/Dataset.md

Pilot after rights review: selectively stage **2–3 genuine source
images** with their source commit and license evidence, require private
owner/curator approval, then grow to 6–10 accepted shared models.
Only then wire consumer UX and paid try-on. If quality is unsuitable,
retain import functionality and use optional custom FLUX generation.
