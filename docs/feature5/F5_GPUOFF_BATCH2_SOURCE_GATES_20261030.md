# Feature #5 — Follow-up GPU-OFF hardening inside combined PR #781 (30 Oct 2026)

**One review batch, not four new PRs.** Parent is existing #781 first combined GPU-OFF batch (head before follow-up `53597a2687fee1336977bced1259abb23d0bef7f`). The first batch passed its exact-head four CI jobs in run #41025346427; each new source file here is tested by the **new final head's required four-job CI**, not that historical run.

| Existing F5 task | Changes | Offline acceptance and limitations |
|---|---|---|
| F5-13 | `wan22_native_preflight.check_small_safetensors_header` | Reject bad tensor descriptors/offsets, duplicate/nonfinite/deep header JSON, hardlinked model; new typed negative cases. Optional small-header audit never proves the full Wan 18GB weight hashes, approved OCI SBOM/ABI or legal license |
| F5-14 | `shared_model_mount.check_mounted_files` | Reject intermediate symlink model mount path and hardlinked model file; fake tiny positive, symlink and hardlink tests. This is stat-only, not a real Azure mounted byte stream or proof of read-only mount |
| F5-17 | `wan22_clip_validation.inspect_native_mp4` | Reject fractional/unicode/float frame count, invalid duration type, malformed or recursively nested probe JSON; 121 ASCII frames, native profile and private hash remain enforced. Fake stdout is **not** real video |
| F5-17 | `wan22_frame_screening.screen_motion_frames` | Check exact same original SHA and file identity **after** five CPU FFmpeg sample decodes; reject hardlink, malformed frame or byte replacement; pure mocked raw RGB tests. No human identity/garment fidelity approval |

**Tests during batch:** `python -m unittest discover -s tests/ai -p 'test_feature5_wan22_native_preflight.py'`, `test_feature5_shared_model_mount.py`, `test_feature5_wan22_clip_validation.py`, and `test_feature5_wan22_frame_screening.py`. GitHub existing Python job is required to discover them, together with FFmpeg, Playwright/frontend and disposable Supabase CI. If a runner/test fails, diagnose and fix in the same batch branch; no disabling tests.

**Reusable shared inputs:** F3 original source demo #630 is merged but lacks real worn licensed garment; Feature2 source exporter #551, Part3 Wan 2.2 #125, Feature4 #322 are still draft and their original production acceptance remains external. No guessed model output or approval receipts.

**Status unchanged:** original F5 release ledger 0 DONE / 3 IN PROGRESS / 19 BLOCKED out of 22. Only coordinator can integrate #781 into #465, reconcile historical siblings #685/#688/#691/#694/#698/#702, promote parent to main, validate fresh main 4/4 and mark any development task DONE. Do not run GPU or paid AI, cloud/PROD migrations, rights automation, user-facing media previews or WineShopPOS.
