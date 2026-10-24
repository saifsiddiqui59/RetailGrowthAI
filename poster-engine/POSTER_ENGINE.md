# Part 1 — secure offline promotional poster engine

This is an actual PNG renderer, not a hosted preview or an image generated in this chat. Source-only deliverable in Part 1; it is **not** connected to RetailGrowthAI DEV, asset storage, or Part 2 publishing yet.

## Presets and source

- `editorial`, `bold`, `minimal` templates, at `square` (1080×1080) and `portrait` (1080×1350).
- Builds headline from the selected v1 campaign day `topic` and CTA from that day's Reel CTA; uses an existing authorized storyboard image. Brand name, colors and an optional authorized logo are configurable.
- Discounts and offers are **not invented**: caller must pass explicitly approved offer copy.
- Re-encodes private approved source images to PNG, stripping source metadata; no network download or external image generation.

## Example

```bash
python poster-engine/render.py \
  --campaign frontend/src/features/campaigns/fixtures/sample-campaign.json \
  --manifest /tmp/authorized-manifest.json \
  --asset-root /tmp/private-tenant-staged-assets \
  --day 1 --business 'Clothing Studio' \
  --template editorial --size portrait --output /tmp/preview.png
```

Operator or authenticated backend must stage licensed media and create manifest for this campaign/shop. No fixture media IDs are assumed to refer to genuine rights-approved files. Human-approved offer copy may be passed with `--offer`.

## Security, operations and next integration

1. Caller MUST authorize JWT, current shop membership, campaign/day ownership, media rights and staged IDs via the existing Supabase-backed service **before** invoking the renderer. The engine also checks shop IDs, allowed campaign-day images, rights evidence, relative-path confinement, supported still-image codecs, 25-MiB source cap and 24-MP cap. These checks are defense in depth, not proof of asset ownership.
2. Reject noncommercial/synthetic licenses by default; `allow_test_media=True` is a unit-test-only library override and is not exposed by the CLI. Never enable it in hosted code. No arbitrary customer URL fetch or PDF/SVG processing.
3. Pillow (currently pinned in Part 1 API requirements) and DejaVu Sans font are runtime prerequisites. Benchmark memory and cost before deploying any cloud worker. The engine emits local PNG only; it does not register/attach, store, email, publish or modify a campaign.
4. Part 1 storage/backend workstream will implement durable draft/version records, private object upload, signed download, and fresh tenant checks on asset selection. The only shared v1 campaign slot is existing `instagram.banner_asset_id`; it must be updated through a secure backend, not by trusting browser input. Part 2/3 interfaces remain unchanged.
5. Part 1 UI workstream will supply template and brand controls, actual preview/edit/selection and saved approved draft. No cloud deployment, SMTP or AI provider spending is authorized by this source PR.

## Tests

`python -m unittest discover -s tests/media -p test_poster_engine.py -v` (Pillow required). Includes six visual output combinations plus tenant, commercial-license, traversal, malformed-image, unauthorized logo, synthetic-media and draft-state negative cases. CI discovery is provided by the Part 1 wiring PR. Test inputs are generated locally and do not imply live hosting or commercial image rights.
