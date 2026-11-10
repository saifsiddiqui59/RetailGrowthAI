# Feature #3 → Features #4 and #5: immediately usable synthetic fashion inputs

**Source code and test fixture, 2026-10-29. Not a new RetailGrowthAI VTON render or hosted tenant approval.**

## Get real upstream image bytes (test/demo only)

OpenVTO publishes fictional synthetic people and apparel demonstration assets with an MIT license statement. We pinned **existing actual source Git objects** at commit `10140178cdb198ff17ad7b226c432bd63d732fc2`, with exact expected byte counts and Git blob SHA-1 identities in:

- `tests/fixtures/feature3/openvto_demo_sources_v1.json`.
- `tests/fixtures/feature3/OPENVTO_MIT_LICENSE.txt` — full upstream MIT license and original copyright notice.
- `poster-engine/feature3_demo_inputs_v1.py` — no credentials, downloads ONLY three pinned immutable URLs, refuses redirects, bounds response sizes, compares exact upstream Git blob identities, decodes images with Pillow, derives SHA256, and emits local materialization receipt.
- `.github/workflows/feature3-shared-openvto-demo-inputs-once.yml` — optional source-only workflow generates the artifact `feature3-verified-openvto-model-garment-v1` for 7 days after real successful download. It does **not** contain user images or connect to Azure/Supabase/GPU.

Run on a local clone or a Feature4/Feature5 worker test sandbox:

```bash
python -m pip install Pillow==11.3.0
python poster-engine/feature3_demo_inputs_v1.py --output-dir /tmp/feature3-fashion-demo
```

| Input | Filename | Use |
| --- | --- | --- |
| Fully synthetic full-body person | `model_posture.jpg` | Feature4 approved *demo-only* still composition / Feature5 image-to-video **test input** |
| Synthetic person avatar | `model_avatar.png` | Feature4 optional face/branding reference testing |
| Synthetic shirt product front | `garment_front.jpg` | Feature4 overlays / future VTON garment test |
| Evidence | `verified_manifest.json` | Exact byte SHA256, Git SHA-1, dimensions, source commit, license, flags |
| Rights | `SOURCE_AND_RIGHTS_NOTICE.txt`, `LICENSE.txt` in CI artifact | Attribution and the synthetic-only test/demo boundary |

For a quick test, Feature4 can compose `model_posture.jpg` and `garment_front.jpg` separately in its FFmpeg storyboard; **do not claim the model is wearing the garment**. Feature5 can run **its own permitted local/image-to-video dry run** with `model_posture.jpg`; this input package itself **does not authorize a paid provider call**, reserve billing or auto-publish. It provides source images, not freshly generated Feature3 images.

## Production-grade private input code for BOTH features

For a genuine **signed tenant** and licensed/reviewed model + garment, no fixed public URL or copied personal token is acceptable. The new `poster-engine/feature3_worker_inputs_v1.py` reuses existing model/garment/try-on source approval and immutable SHA, and exposes two **in-process trusted-worker** entry points:

```python
from feature3_worker_inputs_v1 import materialize_feature4_inputs, materialize_feature5_input

# expected_manifest must come from the existing signed fashion-reference
# service, current_readers are real JWT/RLS + private storage readers,
# and verify_* must validate the live tenant job lease (not a mock in PROD).
editor = materialize_feature4_inputs(
    expected_manifest=editing_manifest,
    current_readers=trusted_server_readers,
    verify_render_job=verify_live_ffmpeg_claim,
)
# editor["sources"]["model"]["image_bytes"]
# editor["sources"]["garment"]["image_bytes"]
# editor["sources"]["first_frame"]["image_bytes"]

motion = materialize_feature5_input(
    expected_manifest=motion_manifest,
    current_readers=trusted_server_readers,
    verify_motion_job=verify_live_reserved_motion_claim,
)
# motion["image_bytes"]    # bytes of correct authorized first frame
# motion["provider_call_permitted"] is always False (separate spend gate)
```

The source manifests come from `prepare_fashion_references` with `purpose="editing"` / `purpose="image_to_video"`. The editor and motion worker must independently prove an active durable job claim, current source and model rights, exact original byte hashes, human-review lineage if a try-on is used, and the same tenant before consuming. Never pass binary results to browser APIs, logs, public Storage or untrusted provider; do not treat returned bytes as an approval to bill or publish.

## Status/acceptance limits

1. **Real demo inputs VERIFIED:** exact source fetch, Git blob SHA-1, actual image decode and local SHA256 succeeded on GitHub Actions [#40820810387](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40820810387), with a genuine six-file [downloadable artifact](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40820810387/artifacts/12874751370) (ID 12874751370, ZIP digest `1c4f0544c8192e676f9735e31783f4678e5b17fab1d83e97f9abed9d8a5ae76c`, 1,339,382 compressed bytes, expires 2026-11-05). This **is** a real successful pinned model/garment/portrait download, not a paid model inference or customer release.
2. **Production tenant bridge implemented in source**: real image decoding against isolated synthetic fixtures and mocked private RLS/leases; **not yet mounted in Feature4/Feature5 live workers**. Their leads can use the APIs without waiting on Feature3's real VTON model.
3. **Not provided yet**: genuine new RetailGrowthAI VTON output, actual registered synthetic model for the DEV retailer, real signed OWNER/EDITOR/curator review, verified branded product claims, paid FLUX/Wan inference, deployed editor/provider worker, and hosted HTTP readiness (#249).
4. OpenVTO demo images carry upstream MIT source attribution but **never become customer-owned SKU photography or model-consent proof**. They are demo-only inputs in this project. No WineShopPOS files or resources touched.

**Handoff target:** Features #4 and #5 should adopt the existing pinned demo manifest/test downloader now and later inject their trusted private job/lease readers at the two new worker entry points; no schema migration or provider account is needed for the independent tests.
