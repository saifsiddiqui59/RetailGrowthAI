# F2 + F3 + F4/F5 REAL original-demo byte bridge (2026-10-29)

Feature3 reciprocal handoff sent to issues #325 and #472 after verified F2 PR #551 input was sent to F4 PR #322 and F5 PR #465.

Use the existing Feature3 merged pinned OpenVTO MIT synthetic demo source, not new VTON or commercial stock. Feature3 actual CI original download, SHA/decoding and artifact: https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40820810387 . The model pose, avatar and garment are separate demo assets. Do NOT assert the model is wearing this garment.

F2 adds ai-agents/creative-director/feature3-demo-interoperability.js. It reads the actual F3 verified_manifest.json produced by poster-engine/feature3_demo_inputs_v1.py, RE-READS all three local original bytes with exact upstream Git SHA1 pins and SHA256 receipts, refuses symlinks/tampering/non-demo authorizations, and combines those original-byte receipts with actual pinned MIT F2 15/30/60s creative+motion scene packets.

Usage from a main/Feature2-integrated checkout:
1. python -m pip install Pillow==11.3.0
2. python poster-engine/feature3_demo_inputs_v1.py --output-dir /tmp/rgai-f3-demo
3. node ai-agents/creative-director/feature3-demo-interoperability.js 30 /tmp/rgai-f3-demo > /tmp/rgai-f2-f3-f4-f5.json

This bridge does not alter Feature4/5 production APIs. feature4.timeline holds 30s frame/voice/storyboard editorial source; feature5.clip_requests retains FULL Wan motion prompts, native 704x1280 frames=121, but paid provider, GPU and private first-frame IDs remain denied. F4 targets 1080x1920, not native Wan FullHD. No human voice or commercial music is attached. Upstream synthetic original photos are demo-only, not customer SKU/model approval, genuine try-on, private storage, commercial license regrant, or actual retailer publishing.

Automated negative tests run without external download and do not fabricate a live positive: the original F3 source positive was verified in GH CI, while F2+F3 combined original-byte execution still needs an integrated checkout with the actual downloaded demo directory. No paid AI/GPU, hosted DEV mutations, PROD, or WineShopPOS.

Production readers remain solely poster-engine/feature3_consumer_packets_v1.py and poster-engine/feature3_worker_inputs_v1.py with current same-tenant JWT/RLS/media/rights/lease checks. Coordinator owns canonical docs and main merge.