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


## Source-image visual-review pilot — 2026-10-26 addition

The source branch now includes `openpeople_pilot_qa_v2.py`. It is a PRIVATE,
zero-GPU, local operator reviewer for **1–3 real JPGs already staged at the
pinned upstream revision**. It consumes the exact unapproved JSON review
packets from the existing Feature #3 UI; the server-side allowlist and
physical JPG Git-blob hash must both match. It refuses altered permission
flags, changed URLs, missing source files, symlinks and duplicate selections.

Example from the repository root, **only after separately staging the
real source JPGs in an operator-owned private checkout**:

```bash
python - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, "poster-engine")
from openpeople_pilot_qa_v2 import build_private_pilot_review

packet = Path("/private/reviews/P009-full-packet.json").read_text()
receipt = build_private_pilot_review(
    [packet],
    dataset_root="/private/approved-upstream-checkout",
    output_dir="/private/reviews/pilot-001",  # MUST NOT preexist
)
print(receipt["status"], receipt["source_asset_count"])
PY
```

Outputs are **local and unapproved**: a 0600-mode
`pilot-contact-sheet-UNAPPROVED.png` with actual pixel crops and warning,
and `pilot-review-UNAPPROVED.json` recording SHA-1 Git blob provenance,
source SHA-256, size, the precise upstream links, and the still-required
human reviews. Their containing directory uses 0700 on POSIX. Neither
file is stored in Git, Azure, Supabase, a shared browser catalog or a
user-facing CDN. The contact sheet makes *visual review possible*, but it
does not autonomously certify photographic realism or determine age,
likeness, apparel suitability or image-provider commercial rights.

Operator decisions remain OUTSIDE and independent of the raw browser
packet and technical reviewer. Successful private review never sets
`approved`, `rights_verified` or `ready_for_cloud_import` true.
The existing `import_openpeople_still` still independently requires
explicit rights callback approval, authenticated scope/curator authorization
and a private immutable blob/registry implementation.

**Verification:** `tests/media/test_feature3_pilot_review.py` uses
synthetic (not OpenPeople) JPG pixels and mocks the staged-reader only in
the positive local contact-sheet test. Its negative cases exercise genuine
untrusted packet validation, missing source, forced denial, immutability
and private output permissions. Real upstream pixels, artistic acceptance,
rights and hosted imports **remain unverified** until an exact approved
source asset is locally supplied and independently reviewed. Zero GPU
generation and zero new Azure infrastructure are used by this code.
