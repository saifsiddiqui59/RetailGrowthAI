# Feature #5 isolated decisions

- Primary research/adapter candidate: Tencent **HunyuanVideo 1.5**, local official CLI with optional future Diffusers backend; never dynamically fetch unreviewed weights.
- Do not activate Tencent under the community license without commercial/legal and territory review; hosted Indian SaaS does **not** automatically imply unrestricted worldwide access.
- Keep previously implemented Alibaba Wan on Part3 integration branch as an alternative provider behind the coordinator's contract. No second live paid provider.
- 480p, 5-second, 24-fps bounded output profile is a conservative **proposed** profile; not asserted verified by actual inference. Dimensions/probe acceptance require real pinned-model test.
- Premium disabled at three gates: worker flag, license approval, GPU budget approval. Existing approval + quota reservation required in DB before claim. No browser/provider key exposure, no public inference endpoint, no LangGraph or new DB schema.
- Feature4 alone handles reliable offer text, brand logo, music, transitions and final export. Feature5 preserves original assets and indicates human quality review required.

## 2026-10-26 safety/interop addendum
- Tencent official CLI uses `--image_path` *only* for I2V; text mode must omit the parameter. `--video_length 121` at 24 fps targets five seconds, but exact output requires real inference validation.
- Default BF16 runner requires `torch.cuda.is_bf16_supported()`, at least 14 GiB of GPU memory, and a pinned local install. Do not assume the Central India T4 is sufficient merely because it offers 16 GB nominal VRAM; no silent fall back to FP32 (substantially different cost/memory).
- Treat unknown/late private Storage upload acknowledgments and completion fencing as `UNKNOWN`, never as refundable FAILED or a reason to repeat GPU inference.
- Exact existing private object convention `{shop}/renders/{job}/{lease}.mp4` in `retailgrowth-media`; invalid bucket, path, lease or private flag are not success. Never create a duplicate public media bucket.
- No new Azure Functions ingestion path, payment ledger, or final renderer: Part3 and coordinating Feature4 own those integrations.
