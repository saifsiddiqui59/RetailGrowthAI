# Feature #5 motion adapter — disabled source-only

`MotionSpec` and `AssetGrant` are authenticated **server-authoritative** contracts. Run only behind the existing Part3 approved subscription reservation / source-media RLS / ledger / outbox / lease fences. Incoming queue messages contain just the canonical job UUID. This module does not create a queue, cloud API or Supabase schema and does not modify Part3.

`HunyuanLocalRunner` is a no-download optional local official 1.5 `generate.py` adapter; requires explicitly configured preinstalled model checkout + weights + licensed GPU, `enabled=True`, `license_approved=True`, and `gpu_budget_approved=True`. Default off. A pinned model/runtime is still required before execution. No user-facing endpoint or keys here.

`MotionWorker` expects injected existing `JobStore` and `TenantMedia` adapters. The downstream collaborator MUST supply transactional atomic claim/finish/failed fencing with existing credit accounting. Generated clip is checked with local-only ffprobe and private output upload; a human must compare garment with source and approve before publishing. Feature4 remains responsible for promotions, logos, music and final Reel assembly.

Tests: `python -m pytest tests/ai/test_feature5_motion.py`. All tests are CPU-only/mocked. They do not generate real AI video.

No production use until the gates in `docs/feature5/NEXT_TASK.md` are closed.

## Security contract (2026-10-26)
- The offline Tencent CLI must omit `--image_path` for T2V; image/poster mode supplies only a decoded, bounded file inside a private job directory. Zero unapproved network model fetching.
- BF16-capable CUDA hardware and a reviewed 14 GiB minimum are required before launching; a Central India T4 alone is not verified suitable.
- `TenantMedia.upload_private` must return a verified exact, private receipt with `shop_id`, `job_id`, `attempt_token`, `bucket=retailgrowth-media`, `path={shop_id}/renders/{job_id}/{attempt_token}.mp4`, `private=True`. Receipt ambiguity remains UNKNOWN; the injected existing DB store must reconcile it without paid retry.
- Scratch image/video files are deleted after processing. Use encrypted/ephemeral private worker disks; do not log local source content, prompts, provider credentials or private URLs.
- All CLI subprocess and GPU readiness tests remain simulated. No real garment, face, movement or temporal quality has passed acceptance.
