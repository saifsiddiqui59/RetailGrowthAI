# Feature #3 verified byte-level demo handoff to Features 2/4/5/7 (2026-10-29)

## What is actually available

Source code: `poster-engine/feature3_demo_consumer_bytes.py`.
Test code: `tests/media/test_feature3_demo_consumer_bytes.py`.
Upstream originals: `poster-engine/feature3_demo_inputs.py` pinned to
`Prompt-Haus/OpenVTO@10140178cdb198ff17ad7b226c432bd63d732fc2`
with MIT demo assets. Previous *real external* GitHub Action #40829987383
downloaded/decoded all three images, checked the authoritative Git objects,
and saved original SHA-256 receipts in the artifact's `manifest.json`.
Action #40831572603 used those genuine originals to encode/ffprobe a
9s 1080x1920 H264/AAC **technical** MP4, not VTON or customer content.
Do not relabel the already completed work as an output of this source PR.

| Local file under `test-artifacts/feature3-openvto` | Immutable upstream Git blob SHA1 | Role |
| --- | --- | --- |
| `synthetic_avatar.png` | `fc88e5d07282009a14b0bd58fbdd58bc2f89ace0` | Fictional avatar / F4-F7 first frame / F5 I2V frame |
| `synthetic_garment_front.jpg` | `878fde8857f58862723f85d7f8bd723c65a8e498` | Separately photographed product still |
| `synthetic_model_pose.jpg` | `72a86a60280976ce5c73db9525d9648b54d1126a` | Separate pose reference |

## Independently observed exact SHA-256 in actual Actions artifact

Downloaded the original `feature3-openvto-mit-inputs` ZIP (Actions #40829987383,
artifact ID `12877664995`) and recomputed each binary's SHA-256 **and** Git
blob SHA-1 from the ZIP contents, then compared to its manifest:

| Filename | Actual SHA-256 | Manifest and original Git blob |
| --- | --- | --- |
| `synthetic_avatar.png` | `5f04a36a4511c841f17099dab0e934b1fde3a0a8a2f7f62f0ff01d71a2bd86a4` | Both matched |
| `synthetic_garment_front.jpg` | `03ae4afc28c08a928547d56040f7099a06d2d2dbbb900440f7d33be602731b13` | Both matched |
| `synthetic_model_pose.jpg` | `191830a241911e6186c4103e72769918353f4d21bb64c6cf7cafca4217341b39` | Both matched |

MIT license file was also present. This is inspection of the **existing**
artifact, not a new live server release or customer-source rights approval.

## Commands and executable consumer packet

```bash
python poster-engine/feature3_demo_inputs.py --output test-artifacts/feature3-openvto
python -m unittest discover -s tests/media -p 'test_feature3_demo_consumer_bytes.py'
python poster-engine/feature3_demo_footage.py --inputs test-artifacts/feature3-openvto --output test-artifacts/feature3-openvto/feature4-editor-input.mp4
```

```python
import sys
sys.path.insert(0, "poster-engine")
from feature3_demo_consumer_bytes import load_demo_consumer_bytes

folder = "test-artifacts/feature3-openvto"
# F2 creative director: raw product/model/pose refs plus verifiable provenance.
f2 = load_demo_consumer_bytes(folder, "F2")
garment = f2["assets"]["product_still"]["image_bytes"]
# F4 FFmpeg: a real separately framed image, NOT a model wearing the shirt.
f4 = load_demo_consumer_bytes(folder, "F4")
frame = f4["assets"]["timeline_first_frame"]["image_bytes"]
# F5 first frame: offline only. No provider calls permitted.
f5 = load_demo_consumer_bytes(folder, "F5")
first_frame = f5["assets"]["image_to_video_first_frame"]["image_bytes"]
# F7 editing: actual image-byte assets ready for editor timeline ingest.
f7 = load_demo_consumer_bytes(folder, "F7")
editor_still = f7["assets"]["editor_product_still"]["image_bytes"]
assert not any(p["provider_call_permitted"] or p["publish_approved"]
               for p in (f2, f4, f5, f7))
```

Returned schema: `retailgrowth.feature3-demo-consumer-bytes.v1`.
Each role entry has `filename`, exact pinned `source_path`, original
`source_git_blob_sha1`, recomputed `sha256`, `mime_type`, `bytes`
and actual in-process `image_bytes`. All three source files must pass
the existing whole-pack checker, and then every consumer independently
revalidates original Git blob identity, Pillow decode, exact length and
actual SHA-256 **after** final read. These are local offline bytes; never
serialize to an HTTP response and never send user JWT/keys or signed URLs.

Packet `customer_approved`, `publish_approved`,
`provider_call_permitted`, `paid_inference_authorized`,
`actual_vton_inference_performed`, and
`model_wears_product_garment` are all strictly `false`.
`requires_live_tenant_rights_and_worker_lease=true` is mandatory
before converting this example into trusted, tenant-owned runtime media.

## Acceptance boundary

Tests use real Pillow-generated synthetic binary image inputs with a
local injected downloader, not a second live OpenVTO network retrieval.
Actual external original-byte verification remains backed by Action
#40829987383 and artifact `feature3-openvto-mit-inputs` ID
`12877664995`, and real FFmpeg output by Action #40831572603
artifact `feature3-openvto-editor-input-mp4` ID `12879355229`.
Source PR CI must be checked on its exact head before merge; no claim
of live customer Storage, licensed garment rights, VTON inference,
human garment quality, GPU enabled, Azure #249 fix, or production
publication results from these tests.

For live F4/F5 trusted worker inputs, **do not use the demo bridge**:
use existing `feature3_worker_input_handoff.py` with fresh actual
backend shop/media grants and current job lease. F2/F7 likewise require
current authenticated tenant rights before any real customer operation.
