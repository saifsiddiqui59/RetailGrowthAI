# Feature #3 — Indian OpenPeople import-first pilot

**Scope:** review eight already-generated fictional Indian/South Asian-themed character stills and keep the separate optional Create New AI Model feature. No GPU is required for source review, importing or static poster composition.

## Verified upstream source

Repository: https://github.com/Prompt-Haus/OpenPeople

Exact pinned commit: **231f73aa43b32a38001759944baa01d7d154ce26**

The repo's README labels **image assets CC BY 4.0** and **code MIT**. It also describes the people as testing/development images, not guaranteed free of resemblance to real individuals. Rights to use the images in a redistributed commercial SaaS fashion library must be checked independently. A dataset's "Indian %" is an invented synthetic generation profile, not verified heritage or nationality.

Candidate IDs with both full-body and portrait files confirmed at this exact tree: **P009, P006, P079, P033, P054, P059, P025, P016**. Five are labeled female-presenting and three male-presenting in the source character profiles. Individual upstream metadata and exact Git object hashes are pinned in the browser and server source.

Sample source:
https://github.com/Prompt-Haus/OpenPeople/blob/231f73aa43b32a38001759944baa01d7d154ce26/openpeople/data/curated/P009/assets/studio_posture.jpg

## Implemented feature-owned components

- **Browser:** Feature3StudioPanel mounts an optional **Explore existing AI fashion models (no GPU)** panel. The user filters synthetic profile labels, chooses full-body/portrait, views the exact pinned GitHub source and downloads a review packet locally. It does not fetch/model-import any image or declare commercial rights.
- **Source metadata:** feature3-indian-model-review.mjs hardcodes the eight actual upstream identities and the Git blob hashes of their full-body, portrait and metadata files. Every generated review packet states approval, commercial rights, server save and publishing are FALSE.
- **Server review:** openpeople_indian_review_v2.py rechecks every review-packet field against an independent immutable catalog, refuses forged approval/changed hash or URL, and yields a pinned selection.
- **Private importer:** openpeople_import_v2.py now verifies the actual staged JPG has the exact Git object SHA before the already-present trusted license, shop, curator, private PNG upload and pending-review callbacks. The browser cannot set legal permissions.
- **Test suite:** frontend source/packet tests; media tests check 16 JS/Python packet pairs, forged permissions, missing source and substituted JPG bytes.

## Curator operational flow

1. In the poster Studio, open the existing AI model section. Choose e.g. P009 full body, inspect the immutable upstream image, and download its **unapproved** curator packet.
2. Independent operator validates actual image/license provenance, third-party model-provider terms, SaaS redistribution and advertising rights, attribution, synthetic-face likeness and garment quality. Never accept a browser boolean as evidence.
3. Operator separately stages the **exact pinned upstream JPG** in a private checkout preserving its original directory layout. No automatic image download is built in.
4. Authenticated server parses the packet using parse_review_packet_file, then calls import_openpeople_still only after independent reviewer/role approval and with existing server-owned storage/rights callbacks. Byte integrity must match pinned Git blob SHA.
5. Store result as PENDING_REVIEW in immutable private Blob. After separate authorized approval, the existing model record can be reused for poster imagery, garment try-on person references or video reference frames, with a fresh source-rights check each time.
6. Preserve GPU-priced Create New Model as optional. Existing CPU poster composition does not require GPU, while actual virtual try-on or moving-video inference does.

## Not yet delivered

No actual third-party source JPGs have been staged/imported into RetailGrowthAI DEV. No hosted model-library Supabase/RLS catalog, public/shared-asset release, signed upload or customer workflow exists yet. No commercial rights clearance, genuine VTON, real FLUX GPU inference or hosted E2E has been proven. These require coordinator-owned contracts, migration, secure endpoints, customer approval and review evidence (issue #325).

Only coordinator merges feature PR #321, updates canonical PROJECT_STATE/NEXT_TASK/DECISIONS/WORK_LOG and performs protected DEV integration. No WineShopPOS/PROD changes or paid GPU deployment.
