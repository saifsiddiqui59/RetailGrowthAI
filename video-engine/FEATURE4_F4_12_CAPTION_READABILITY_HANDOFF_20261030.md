# F4-12 — Offline caption readability flags (source-only)

Feature #4 draft branch `feat/feature4-caption-readability-receipt-20261030-run3` stacked on draft #322 at `e32a8da61a6272666d757b6c51b0ec2576d7602f`.

A private SRT/VTT sidecar export now includes **conservative, non-authoritative** mobile subtitle warnings: a token exceeding 36 characters, more than two heuristic 36-character lines, or more than 20 characters per second. It never edits Feature #2-approved wording/timing, refuses invalid/unapproved cues, and never asserts visual acceptance or actual encoded subtitle legibility. Only numeric cue indexes and warning codes enter the report; approved caption text remains in private sidecars. No public response contract or shared file changed.

Run `python -m unittest discover -s tests/media -p 'test_feature4_caption_readability.py'` with the existing repo Python environment. This is CPU-only metadata QA, not a real rendered video test, accessibility audit, human visual review, speech alignment or commercial release. A native revised 60s render and actual decoded legibility remain F4-12 acceptance blockers. Exact-head GitHub CI and coordinator review are required before integration. GPU, paid inference, Azure, PROD, WineShopPOS and user samples remain untouched.
