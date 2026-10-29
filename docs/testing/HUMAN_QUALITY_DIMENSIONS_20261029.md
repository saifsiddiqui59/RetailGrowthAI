# Testing Chat — human quality dimensions (independent source extension)

## Intent
A single 1–5 score cannot identify whether an output failed at copy accuracy, garment identity, text legibility, Reel pacing, subtitles, audio mixing or motion continuity. This source-level taxonomy provides stable **human review aspects** for each feature that can produce a real output.

`quality-rubrics.mjs` defines feature-specific dimensions and precise manual checks for F2 (copy/offer/brand/storyboard), F3 (garment/model/typography), F4 (pacing/captions/audio), F5 (motion continuity/artifacts) and F7 (cuts/subtitles/sync). F1 tenant membership is an authorization check, not a creative quality review.

These categories are not algorithmic quality judgments, paid model inference, or claims that F3/F5/F7 were invoked. Existing browser QA remains separate from protected service-written worker observations. A dimension should only be submitted for a feature that has an actual observed PASS output, and it should be stored as an allowlisted `details.dimension` alongside `details.score` and optional reviewer note; current append-only trace `details jsonb` needs no SQL column change. Historical reviews without a dimension remain the `overall` category.

## Next integration boundary
- Add dimension selectors to the existing Testing Chat human-quality form after the source triage branch is merged; reject unsupported feature/dimension combinations in client and output recommendations, not just display them.
- Compare 1–5 scores only for matching dimensions across baseline runs; a 2/5 *audio* rating cannot be interpreted as a regression from a 4/5 *caption* rating.
- Distinguish human review from technical success and backend job outcome, never render fake ratings for explicitly NOT_RUN features.
- Run Node/Chromium regression tests, required four PR jobs, independent main checks and separately reviewed DEV rollout. This branch has no runtime inference, SQL changes, backend credentials, paid API calls, publishing, PROD or WineShopPOS modification.
