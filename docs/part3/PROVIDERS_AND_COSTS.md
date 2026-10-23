# Part 3 — Wan vendor research and cost baseline (2026-10-23)

Verified with official Alibaba Cloud documentation. This is **research**, not approval to consume any paid provider API. Vendor plans/prices may change, including promotional prices and taxes.

## Available official Alibaba Model Studio models
- `wan2.7-t2v-2026-06-12`: text-to-video, 720P/1080P, 2–15 seconds, 30 fps MP4 (International/Singapore).
- `wan2.7-i2v-2026-04-25`: first-frame / first-and-last-frame / video continuation, 720P/1080P, 2–15 seconds, 30 fps MP4. Source media must be licensed; for first-frame video its aspect ratio follows the source image, not a `ratio` parameter.
- `wan3.0-video-prime`: newer 480P/720P/1080P multi-modal video up to 30 seconds. Pricing is higher; not implemented by the initial narrow 2.7 adapter.
- `wan2.6-t2v`, `wan2.6-i2v`: legacy separately versioned endpoints; do not send new 2.7 payload to legacy format.

## Official reference prices (Singapore, USD)
| Model | 720P / second | 1080P / second | Notes |
|---|---:|---:|---|
| Alibaba Wan 2.7 T2V | $0.10 | $0.15 | 2–15s |
| Alibaba Wan 2.7 I2V | $0.10 | $0.15 | 2–15s |
| Alibaba Wan 3.0 Video Prime | $0.14 | $0.28 | up to 30s |
| fal.ai Wan 2.6 I2V (third-party) | $0.10 | $0.15 | 5/10/15s; alternative provider only |

At an *indicative* **₹94.94/USD** on 2026-10-23, Wan 2.7 for 5s 720P ≈ **₹47.47**, 10s 720P ≈ **₹94.94**, 15s 1080P ≈ **₹213.62**. A 30s campaign Reel requires composition of clips, e.g. two 15s 720P Wan 2.7 clips = $3.00 ≈ **₹284.82**, while two 15s at 1080P = $4.50 ≈ **₹427.23**. These exclude GST, foreign exchange spread, failed/retried tasks, premium FFmpeg assembly, hosting/storage/network and platform margin. Do not present them as a customer price or quote without real-time approved provider cost.

## API and region
- Use *workspace-specific Singapore* HTTPS `https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com` with same-region API key. Region/model/key must match.
- Call `POST /api/v1/services/aigc/video-generation/video-synthesis` with `X-DashScope-Async: enable`; poll `GET /api/v1/tasks/{task_id}` at bounded intervals (vendor suggests ~15 seconds).
- Model creation usually takes 1–5 minutes. Task IDs and result video URLs are valid for **24 hours**, not a permanent customer media link. Never return provider URL directly to the browser; backend must privately import, verify codecs/bytes and save in existing private media storage.
- WAN 2.7 T2V has explicit `ratio`; I2V uses first-frame aspect ratio. Watermark choice and AI disclosure must comply with platform/local policy.

## Rights and provider approval
- Alibaba Cloud paid Model Studio product terms say the provider does **not** claim IP ownership in output, but customer input/output use is subject to rules/laws, rights of third parties and output may lack exclusivity.
- **Model Studio console *trial interactions* are explicitly restricted to evaluation and not commercial publication.** Never treat free console trial renders as licensed marketing assets.
- Verify paid workspace entitlement, commercial terms and permitted data regions. Customer must own/authorize input photo, likeness/logo/music and consent to cross-provider transfer. Moderation can reject copyrighted/unsafe content. No automatic posting: human review.
- Alternative fal.ai API has separate terms, media handling, pricing, model versions and credentials; provider substitution requires independent review and cannot silently inherit Alibaba approval.

Sources:
- https://www.alibabacloud.com/help/en/model-studio/video-generate-edit-model
- https://www.alibabacloud.com/help/en/model-studio/text-to-video-api-reference
- https://www.alibabacloud.com/help/en/model-studio/image-to-video-general-api-reference
- https://www.alibabacloud.com/help/en/model-studio/model-pricing
- https://www.alibabacloud.com/help/en/model-studio/wan3-0-video-prime
- https://www.alibabacloud.com/help/en/legal/latest/alibaba-cloud-international-website-product-terms-of-service-v-3-8-0
- https://help.aliyun.com/en/model-studio/bailian-service-notes
- https://fal.ai/models/wan/v2.6/image-to-video/api
- https://indiagraphs.com/data/usd-inr-exchange-rate/average-usd-inr-rate-per-usd
