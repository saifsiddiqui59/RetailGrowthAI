# RetailGrowthAI clothing campaign — reproducible engine sample

This deliberately uses the **existing RetailGrowthAI seven-day clothing fixture** (Day 1) and runs the **unmodified repository engines**, not ChatGPT image/video generation or a claimed hosted customer run.

- Generator: `demo/clothing/generate.py` draws original synthetic clothing illustrations and original procedural demonstration audio, emits rights-evidence-stamped staging manifest, and copies LinkedIn/Instagram content from the fixture.
- Genuine engine commands: `poster-engine/render.py` renders a 1080×1350 poster; `video-engine/render.py` renders the 30-second 540×960 MP4. No customer asset, WineShopPOS secret, external stock footage, SMTP, Supabase mutation or paid provider.
- Verification: `ffprobe` confirms H.264 video and AAC audio, 30-second duration; Pillow confirms PNG dimensions. GitHub Actions uploads all outputs as one user-downloadable artifact.
- GitHub Actions [successful run #40081154973](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40081154973), artifact [#12555496142](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40081154973/artifacts/12555496142) (`RetailGrowthAI-Clothing-Post-Poster-Video-Demo`, 14-day retention). Results are synthetic concept art, not licensed product photography or a production-ready creative.
- This does **not** verify Supabase user login/approval, signed private remote download, Azure Functions poster render completion, live Foundry-generated copy or any published social content. Independent hosted canary [#40079151954](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40079151954) previously confirmed real remote campaign/draft/poster-save but timed out on poster render POST; no completed cloud video claim.

To repeat, push a change under `demo/clothing/**` to the test branch or manually dispatch the workflow from a reviewed branch. Prefer a real licensed photo and authorized DEV tenant only for separately approved hosted tests.
