# Feature #3 — Fashion reference asset handoff for #2, #4 and #5 (2026-10-28)

**Status: implemented source-level, GPU OFF, authenticated deployment NOT complete.**
This supplements the existing `model_library_v2`, `model_reference_v2`,
`garment_review_v2`, Feature3 v2 JWT/RLS design API, private media
registration and optional provider. It does not introduce another renderer,
writer, new wallet, database migration or upload surface.

## Ownership and consumer contract

`poster-engine/fashion_reference_v1.py` adds:

- `prepare_fashion_references(...)` resolves a **real, currently approved**
  retailer's garment upload and optional approved model catalog image, and
  optionally one post-inference, six-feature **human reviewed** try-on PNG.
  Caller injects server-side `read_asset`, `authorize_asset`,
  `read_private_bytes`, `read_garment_metadata`, `read_model` and
  `read_review` functions. No browser-supplied metadata or role is trusted.
  Asset ownership, private bucket, immutable tenant-first object path,
  mime, actual decoded dimensions and SHA256 of **private image bytes**,
  license evidence, current rights revision and approval are checked.
- `resolve_first_frame(expected_manifest, current_readers, verify_worker_job)` is a PRIVATE
  Feature5 worker-only operation. It repeats the full source/model/product/
  review check, demands an identical reference fingerprint and makes one
  last hash-verified image read. It returns **in-process `image_bytes`**
  for image-to-video *after* an independently verified, currently leased
  durable private worker job (`verify_worker_job`) checks shop, source IDs,
  exact reference fingerprint, subscription and approved cost cap. It returns NO Blob URL, bearer JWT, API key, payable job
  receipt or public source. It does not start GPU or a renderer.
- `plan_virtual_try_on(manifest)` prepares an **unbilled, blocked** pair
  of garment/model IDs and category for licensed future provider
  integration. It does **not** disguise a composition, mask or mock image
  as genuine virtual try-on. `FASHN_VTON_15` remains disabled because
  the associated human parser commercial licensing has not been cleared.

**Reference manifest** `retailgrowth.fashion-reference-bundle.v1`
(made only by the trusted backend) contains shop UUID, request purpose,
garment SKU/type/colour/shape/pattern/neckline/sleeves/length/embroidery,
human-reviewed product revision, source/media IDs, original image
dimensions, MIME, blob SHA256, source (UPLOAD/GENERATED), image license
and attribution, asset approval + current rights revision, model UUID
/ label / pose / adult synthetic status / rights revision / commercial
license (when used), optional verified VTON review state and six approved
features, preservation instructions, fingerprint and unambiguous
`output_approved=false`, `gpu_authorized=false` flags.

There is intentionally **no** `object_path`, signed link, access token,
third-party URI, first-frame image bytes or direct provider activation in
this metadata packet.

| Consumer | Purpose | What to do | Must not do |
| --- | --- | --- | --- |
| Feature #2 Creative Director | `creative_direction` | Request server-approved metadata and reference IDs for shot planning; specify garment identity and camera/background-only movement, ask for first-frame use, never hallucinate approved fabric or discounts | No direct private bytes, browser asset grants, product licensing conclusions or paid video calls |
| Feature #4 Professional Video Studio | `editing` | Carry identical shop/asset ID/SHA/rights revision in scene/edit instructions and arrange approved stills with existing editor; validate sources again at render | Never substitute other-shop bytes, create new renderer, claim that model wears the garment or auto-publish |
| Feature #5 Premium AI Motion | `image_to_video` | After a separately approved/prepaid worker claim, rehydrate manifest via server callbacks and call `resolve_first_frame` to stream exact original PNG/JPG/WebP privately; use scene rules to preserve product | No direct signed/public URLs, unapproved VTON frame, client-supplied mask, duplicate wallet or automatic GPU activation |

**Important distinction:** A model portrait + garment original is **not**
yet an image depicting the model in that garment. In the default
zero-GPU path the first frame is the retailer-owned original garment
image. Only a genuinely inferred, registered, independently licensed,
human-reviewed try-on output may replace it. The reviewer must inspect
actual colour, pattern, neckline, sleeves, length and embroidery.
A human checklist is an approval gate, not mathematical proof a
generative video will preserve the pattern. Final motion output must
also be reviewed against source frames before publishing.

## Kurti test scenario

The new `tests/media/test_feature3_fashion_reference.py` creates
illustrative **Pillow-only, synthetic and NOT production-licensed**
720x1080 images: teal A-line kurti, round neckline, elbow-length
sleeves, gold chest embroidery, SKU `KURTI-TEAL-001`. It injects fake
server-only approval readers solely for unit tests, then checks:

- metadata-only Feature2/4, exact garment first-frame bytes for Feature5;
- same-shop registered private media, decoded dimensions, SHA256, human
  product revision and licensed model pose/attribution;
- a VTON plan that never attempts paid inference, and rejection of
  unverified inference, missing human review or altered embroidery;
- denial for another shop, revoked rights, forged image registration,
  mutated private bytes, missing fields, fake fixture approval and
  stale product/model/try-on revisions.

The fixture does not attest to **any** real kurti uploaded by a retailer.
There is NO approved real garment/model source currently registered in
RetailGrowthAI DEV, so no actual reference imagery can responsibly be
delivered to an image-to-video model yet.

## Release-required integration, not silently assumed

1. **Coordinator/data:** make tenant-owned product metadata + garment-review
   revision authoritative (not just caller JSON) and supply per-asset
   reviewed-use/revocation grants. Current `media_assets` alone has
   user-declared license fields; it does **not** store review approvals,
   SHA256 and decoded dimensions. The injected `read_asset` contract
   requires those facts joined/verified server-side before any live use.
   Any additive SQL/reviewer RPC requires coordinator-owned migration,
   RLS, JWT checks and audit.
2. **Real content:** register actual retailer-approved kurti and a real
   approved synthetic-adult model library image through existing private
   storage; carry original source IDs, immutable hashed bytes, license
   and pose. No revoked synthetic Feature2 account/image can substitute.
3. **VTON quality:** obtain permitted FASHN parser replacement/license
   and separately authorized inference/cost cap. Review generated real
   wearing-model output against original garment colour, seam, embroidery,
   neck, sleeves and hem; reject mismatches. A real completed VTON frame
   must be recorded with its original garment+model lineage and immutable
   reviewer decision.
4. **Other leads:** Feature2 chooses approved reference identities only;
   Feature4 coordinates timeline/preview, keeping final media renderer;
   Feature5 consumes actual bytes only inside an already-authorized
   scale-to-zero worker. Owner/EDITOR, VIEWER read-only, foreign, expired
   session, revoked rights and changed image must be tested end to end
   before user-facing activation.
5. **Gate:** independent full four-job PR CI, merge/main CI, separate DEV
   deployment verification and visual review; no GPU charges or PROD
   until separately approved. Existing Feature3 catalog private path fix
   PR #504 must be reconciled before real model import.

No WineShopPOS modification. This document provides a reviewed integration
proposal without changing the canonical shared `docs/INTERFACES_V1.md`
until the coordinator freezes the cross-feature API surface.

## 2026-10-28 — Real registered-upload UUID interoperability repair

`register_uploaded_image` validates an independently generated private
Storage object key `{shop}/uploads/{object_uuid}.{png|jpg|webp}`, then creates
a separate `media_assets.id` registration UUID. The prior fashion
adapter erroneously required the storage UUID to equal the DB media ID.
`fashion_reference_v1._approved_asset` now verifies the correct existing
upload prefix, a canonical private object UUIDv4, exact registered extension
and current DB row+shop+hash+byte permissions **without equating the two IDs**.
This is still a source-level adapter: production requires authoritative
asset/current-rights review callbacks and original byte hash registration,
not unverified client evidence. New tests deliberately use different file
and database IDs and deny forged paths, mismatched MIME and traversal.
