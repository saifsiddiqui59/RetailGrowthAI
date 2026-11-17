# Feature2 metadata-only YouTube music source handoff — 2026-11-17

This reuses **two unchanged original Git blobs** from both F2 parent #551 (`d80d6b50705323290c4b214bf2f006eacef1ef33`) and stacked keeper #848 (`a35a1f171819564bfb3ed00806e4a87545a8a043`).

- `src/ai_agents/feature2_live_music.py` original Git blob `321e06a67330498002f22fb19fd188d033c17378`
- `tests/test_feature2_live_music.py` original Git blob `d1127e62d4d31a029ae77c56e8c79877a11dddb6`
- Reuses the existing merged `feature2_music_recommender.py`; no override of newer data/ranking/security source.
- Official YouTube videos.list music-category popularity results, region IN, are *not* Instagram trending audio evidence. This API metadata is source reference only, never a copyrighted soundtrack, streaming playback, licensed input, video/audio download or commercial grant.
- `RETAIL_FEATURE2_MUSIC_YT_ENABLED` defaults OFF, server API key only, exact HTTPS endpoint, bounded result size, strict untrusted text/video ID checks, no redirects, current signed tenant-role lookup before and after provider observation, and `can_use_audio=false`.
- All tests inject fake network responses and deny forged hosts, stale/revoked membership and non-music content. No external API, paid provider, licensed media, voice model or rendering is run.
- Source-only acceptance requires four exact-head PR CI jobs and four fresh-main CI jobs; original F2 hosted/rights/editor and F4/7 media handoff remain unfinished. No GPU/DEV cloud/SQL/PROD/WineShopPOS changes.
