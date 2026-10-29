# Feature #3: OpenVTO MIT synthetic demo inputs for Features #4 and #5

**Status:** Pinned **real external upstream Git blob identities**, network download not yet demonstrated in the hosted DEV customer workspace. These are unmodified upstream synthetic image *sources*, not a VTON inference result. Owners of Features #4 and #5 can download them **now**, without waiting for FLUX, virtual try-on, image licensing of customer garments, model review, GPU or Feature #3 deployment.

Source: [Prompt-Haus/OpenVTO](https://github.com/Prompt-Haus/OpenVTO), commit `10140178cdb198ff17ad7b226c432bd63d732fc2`. The exact pinned upstream README section **Demo Assets License** says avatar, clothing and people media in `openvto/assets` are team-generated fictional images available for testing/development/demonstration under [MIT](https://github.com/Prompt-Haus/OpenVTO/blob/10140178cdb198ff17ad7b226c432bd63d732fc2/LICENSE). Preserve its copyright notice/attribution when redistributed. Review provider and customer release separately. The files below are MIT demo input, **not approved commercial images or a verified retailer-owned clothing SKU**.

| File generated locally | Exact upstream path | Git blob SHA1 |
| --- | --- | --- |
| `synthetic_avatar.png` | `packages/sdk/openvto/assets/avatars/1.png` | `fc88e5d07282009a14b0bd58fbdd58bc2f89ace0` |
| `synthetic_garment_front.jpg` | `packages/sdk/openvto/assets/clothes/shirts/1_front.jpg` | `878fde8857f58862723f85d7f8bd723c65a8e498` |
| `synthetic_model_pose.jpg` | `packages/sdk/openvto/assets/people/1_posture.jpg` | `72a86a60280976ce5c73db9525d9648b54d1126a` |

## One command — stable shared input paths

From repository root (with existing Pillow installed):

```bash
python poster-engine/feature3_demo_inputs.py --output test-artifacts/feature3-openvto
```

The downloader requests **only those three files** at the exact pinned commit and fails closed on redirect, changed Git blob SHA1, size, invalid image format, untrusted path or network failure. It also calculates and records SHA256 of downloaded bytes and writes `manifest.json` only after verifying every image.

- **Feature #4:** Use `test-artifacts/feature3-openvto/synthetic_avatar.png` for a still/first-frame compositing test, `synthetic_garment_front.jpg` as product still, and `synthetic_model_pose.jpg` for a model reference. All can be supplied to existing FFmpeg editor tests. This is not an approved final marketing Reel.
- **Feature #5:** Use `synthetic_avatar.png` as a non-paid image-to-video **test input** and the garment JPG as a reference for API mapping and first-frame SHA/rights checks. **Do not claim the avatar is wearing the garment**: only a real VTON inference and review can establish that. Feature #5 must still authorize a real tenant-owned source, hold its durable lease, enforce cost reservation, and re-read private SHA before any billable provider call.
- **Feature #2 and #7:** Can use the same garment JPG and avatar PNG for offline storyboard/editor scaffolding; media remains an unapproved demo until separately checked.

The generated `manifest.json` has `feature4` and `feature5` read-only entries. Both explicitly remain `publish_approved=false` and `provider_call_permitted=false`. The online fetch is **opt-in**, not run automatically by offline CI. CI tests use Pillow-generated fake images only to test downloader logic. **No hosted storage, real input-byte download, signed-user import, paid inference, publishing or WineShopPOS operations are implied by this document.**

## Optional GitHub Actions downloadable input ZIP

Run workflow `Feature3 pinned OpenVTO real demo source pack` on branch `feat/feature3-real-demo-input-pack-20261029` or use its branch push run, then download short-lived artifact `feature3-openvto-mit-demo-inputs` with original bytes, `manifest.json` and upstream MIT LICENSE. **CI source download success must be separately inspected; workflow trigger alone is not source acceptance.**

## 2026-10-29 ACTUAL original-byte download succeeded (supersedes initial source-only wording)
- GitHub Actions [#40829987383](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40829987383) completed SUCCESS running the pinned downloader on a GitHub-hosted Ubuntu worker. It verified upstream three raw images against exact Git blob SHA1, length and Pillow format, then pinned upstream `LICENSE` Git blob `d246e4160c1d8c59bc9e99a90b095ec42ee5cec5`, and verified the resulting manifest's explicit no-GPU/no-publish gates.
- The bundle is available as Actions artifact **`feature3-openvto-mit-inputs`** (GitHub artifact ID `12877664995`, 1,339,123 bytes ZIP, expires 2026-11-28 UTC); users with repository Actions access can download directly from that run. ZIP contains three verified media files, `manifest.json` and `LICENSE-openvto.txt`. This is now actual externally downloaded upstream media evidence, not only mocked Pillow downloader tests.
- OpenVTO synthetic source avatar is not shown wearing the separately supplied shirt; Feature5 must not call it a VTON sample, and Feature4 must not publish an advertisement alleging garment fit. Any paid or customer-approved use remains blocked pending separately verified rights and a new auth/lease/approval check. The permanent pinned downloader can re-create the bundle once artifact retention lapses.


## Additional Feature4/7 playable Full-HD footage (2026-10-29)
- A second zero-GPU actual GitHub Actions workflow [#40831572603](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40831572603) generated a **9.0s 1080x1920 portrait H264/AAC MP4** from the real pinned MIT garment/portrait source stills, with independent ffprobe verification. Download `feature3-openvto-editor-input-mp4` (artifact #12879355229, expires 2026-11-28). It contains original stills, original MIT notice, manifest and `feature4-editor-input.mp4` plus `technical_footage_manifest.json`. Feature4 and Feature7 can use the video for their timeline/audio/footage-editing tests immediately; Feature5 should use the source avatar PNG for image-to-video tests. Not a virtual try-on or professional customer reel; no endorsement or actual fit is implied.
