# Feature2 VoiceStudio private registration — direct-to-main safe slice (2026-11-11)

Owner requested faster, parallel, merged source integration. This **two-code-file Feature2-only slice** extracts the existing worker orchestration from combined PR #920 while its protected JWT/SQL RPC changes get independent security review.

- Reuses existing unmodified upstream VoiceStudio API client (#900), original-key voice job review gating and Feature4 WAV padding (#905), private two-object Supabase Storage writer and readback (#909).
- The new `run_verified_private_voice_job` composes those actual source modules and requires a trusted **injected** one-shot SQL claim and authoritative review-registration callback, verifies original/render WAV bytes via private storage readback with SHA256, then obtains only a `NEEDS_REVIEW` receipt. No browser key, private URL, AI/paid model activation or publishing.
- New deterministic Python test exercises real producer and private Storage module with synthetic mock HTTP, foreign-shop denial, model OFF gates, duplicate job denial, tampered readback, partial-object failure, uncertain SQL receipt and role revocation.
- No auth API, root Azure Functions router, SQL schema, migration, production resource or third-party model changed. Full protected four-RPC SQL client, JWT-bound initiation and matching review-only SQL DDL remain in PRs #920/#923/#925 awaiting an independent reviewer. No SQL or hosted voice inference is claimed.

**Task state:** original F2-19/F2-20 IN PROGRESS, source component eligible for ordinary Feature2 merge after exact-head PR 4/4, rechecked current main, and fresh postmerge main 4/4. This does not close the full task. GPU, paid models, PROD and WineShopPOS untouched.
