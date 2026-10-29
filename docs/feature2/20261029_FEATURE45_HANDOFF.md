# Feature2 to Feature4/5 immediately reusable offline inputs (2026-10-29)

Source: RetailGrowthAI original Feature2 draft PR #551. These files are machine-test fixtures, not a new production HTTP API.

## Reuse the existing working MIT Creative Director

Run these from repository root (Node required), no remote calls, keys or model inference:

    node ai-agents/creative-director/export-feature4-feature5-fixture.js 15 > /tmp/f2-15.json
    node ai-agents/creative-director/export-feature4-feature5-fixture.js 30 > /tmp/f2-30.json
    node ai-agents/creative-director/export-feature4-feature5-fixture.js 60 > /tmp/f2-60.json

The exporter invokes the real local pinned MIT Kuble-Lab engine and its existing exhaustive garment/shot compiler, not an assistant-invented duplicate. JSON has 3/6/12 contiguous five-second timeline events, original unmodified detailed motion_direction_v1 for each shot, five garment identity locks, camera movements, SHA256, original text voiceover/dialogue, and explicit non-approved outputs.

Feature4: feature4.timeline is shot-precise and targets a final 1080x1920 H264/AAC portrait Reel; Feature4 must still verify registered media and retain its own approved rg_video_v2 request and render gate. Feature5: feature5.clip_requests[*].original_direction is the full native 5-second Wan-relevant source. Its actual TI2V-5B output profile is 704x1280/24fps/121 frames, not 1080p. Final resizing/composition belongs to Feature4.

## Generate real image bytes for immediate local decoder tests

    python ai-agents/test-fixtures/clothing-shop-pexels/generate-synthetic-matte.py --output-dir /tmp/rgai-feature45-test

This creates feature2-synthetic-first-frame.png (1080x1920) and source-provenance.json (actual deterministic SHA256). It uses ONLY Python standard library. It is an original stylized kurti silhouette: not a human/model, not a genuine garment product, not a licensed Pexels asset. It can be used to smoke-test Feature5 CPU first-frame loading and Feature4 CPU compositor but never permits a GPU provider, a publish action, shop storage registration or merchandising claims. FFmpeg can create a short H264 test clip from the image for technical editor testing.

## Rights and audio responsibility

Feature2 supplies narration/dialogue text, music discovery candidates and licensing warnings. It supplies NO licensed music/audio bytes or verified voiceover. Feature4 needs licensed voice/music, handles narration timing, mixing, ducking and final render. The four existing Pexels clothing source URLs remain discovery-only. Feature3's already-merged poster-engine/feature3_consumer_packets_v1.py is the authoritative current tenant signed approved-garment/model/first-frame source. Real fashion/product/ad content must be promoted through that existing reader, not these fixture markers.

All synthetic offer/approval markers in existing director test inputs are NOT merchant approval. Every exported package keeps can_publish=false, no licensed private media IDs, GPU off and zero billable calls. Actual Pexels import, human apparel/model and commercial rights review, Feature4/5 authenticated integration and Azure #249 503 reliability remain distinct gates.

Repeatable CI: ai-agents/tests/test_feature2_cross_feature_export.py, ai-agents/tests/test_feature2_synthetic_matte.py and the original director upstream tests.

Coordinator: never double-merge #551 with overlapping Feature2 draft PRs. Share these source paths with Feature4 PR #322 and Feature5 PR #465 for immediate independent adoption.
## Actual 5-second FFmpeg/H264 media source

The checked-in local technical render tool produces ORIGINAL real video bytes (not a feature mock), 1080x1920 at 24 fps with H264/AAC silent audio, plus first-frame PNG, original SHA and a rendered-video receipt:

    python ai-agents/test-fixtures/clothing-shop-pexels/render-offline-reference.py --output-dir /tmp/rgai-feature45-test --render

With no --render flag this tool is a zero-write plan. It validates the final 5-second MP4 using ffprobe, does not upload to private Storage, and cannot create an approved garment/media grant. The actual offline tech render was executed locally and ffprobe returned H264, AAC, 1080x1920, 24 fps and exactly 5.000 seconds. It is a static experimental visual matte, NOT a professional commercial video. Consumer lead should use the emitted original video as test data only, not as Wan-generated or fashion-original stock.

An independent technical sample ZIP was prepared for the owner with generated PNG, MP4, SHA receipts and README. It is not put in GitHub due to generated binary file/repo size and no approval to distribute actual user media.

## Original music input for Feature4 local audio-mix acceptance

Generate original procedure-synthesized mono 48kHz PCM16 WAV beds, without any commercial song, downloads, samples, Azure Speech, Pexels, YouTube or cost:

    python ai-agents/test-fixtures/clothing-shop-pexels/generate-original-test-audio.py --output-dir /tmp/rgai-feature45-test --seconds 30

The builder writes feature2-original-test-bed-30s.wav plus original-audio-provenance.json with SHA256 and duration. Supported 5/15/30/60 seconds. This enables Feature4 to test its existing FFMpeg/HyperFrames audio mix, beat analysis and sound ducking against ORIGINAL local PCM bytes, while the Feature2 packet provides the text script and cue timing. This recording has NO narrated human speech, NO checked commercial music grant, NO tenant-private registered music ID, and NO verified viral rights; it must not be presented as publishable music or an approved campaign soundtrack.
