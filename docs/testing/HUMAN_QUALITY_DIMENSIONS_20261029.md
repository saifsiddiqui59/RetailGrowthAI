# Testing Chat — human quality dimensions (independent source extension)

## Intent
A single 1–5 score cannot identify whether an output failed at copy accuracy, garment identity, text legibility, Reel pacing, subtitles, audio mixing or motion continuity. This source-level taxonomy provides stable **human review aspects** for each feature that can produce a real output.

`quality-rubrics.mjs` defines feature-specific dimensions and precise manual checks for F2 (copy/offer/brand/storyboard), F3 (garment/model/typography), F4 (pacing/captions/audio), F5 (motion continuity/artifacts) and F7 (cuts/subtitles/sync). F1 tenant membership is an authorization check, not a creative quality review.

These categories are not algorithmic quality judgments, paid model inference, or claims that F3/F5/F7 were invoked. Existing browser QA remains separate from protected service-written worker observations. A dimension should only be submitted for a feature that has an actual observed PASS output, and it should be stored as an allowlisted `details.dimension` alongside `details.score` and optional reviewer note; current append-only trace `details jsonb` needs no SQL column change. Historical reviews without a dimension remain the `overall` category.

## Added UI and comparison implementation
- Existing Testing Chat now presents a `Quality aspect` selector only in its human-review form. Client refuses a rating for a feature without observed output, and refuses invalid feature/aspect pairs. A legacy score without a dimension is treated as `overall` for compatibility.
- The saved event contains only `{score,dimension,note}`; no DB schema change. Human-review cards show the specific aspect and the reviewer score. The triage recommendations suggest the concrete quality check for a rated 1–2/5 aspect, keeping output execution status unchanged.
- `trace-quality-analysis.mjs` aggregates human ratings only after an observed PASS and compares only the same feature + same aspect; a 2/5 *audio* rating is not a regression from a 4/5 *caption* rating. Legacy aggregate means covering multiple aspects are clearly labeled mixed/not directly comparable.
- Node tests verify invalid/forged/unrun reviews, aspect mismatch and like-for-like comparison. Mocked Chromium exercises saving an F4 audio score and immediately displaying its specific next check. Four PR CI jobs, independent main checks and separately reviewed DEV rollout are required. This source change makes no runtime inference, SQL change, backend credential use, paid API call, publishing, PROD or WineShopPOS modification.
