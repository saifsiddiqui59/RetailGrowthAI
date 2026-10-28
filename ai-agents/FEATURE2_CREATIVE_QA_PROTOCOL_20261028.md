# Feature2 P1 Creative Quality Benchmark Protocol — independent, zero-cost

The new `ai_agents.feature2_creative_quality` operates on any structurally versioned `creative_direction_v1` + `motion_direction_v1` bundle. It **does not** call Azure, Feature5, media storage or a cloud service, and does NOT claim its field coverage score demonstrates great writing.

- Six weighted criteria: hook/story 20, shot cinematography 20, motion executability 20, brand/garment provenance 15, commercial review 15, audio/editor readiness 10.
- `review(bundle)` yields explicit failed criteria, a *structural coverage* score, and permanent `actual_ai_generated=False`, `human_creative_approved=False`, `can_publish=False` and `can_dispatch_paid_motion=False`.
- `blind_human_comparison` refuses a winner without both anonymous candidate plans and 2 independently identified reviewers per candidate with a complete 0–5 6-category rubric. Scores are receipts of **user-supplied human evaluations only** and may not trigger publishing/inference.
- Tests use explicit SYNTHETIC 15/30/60s Diwali fixtures, validate timeline gaps, incomplete reference rights/approval, audio contradiction and blind-review participant independence. Not a claim that any real GPT or Wan output was evaluated.
- The previous genuine Azure GPT-4.1-mini seven-day artifact is the baseline to beat, but it only contains three 10-second text direction lines per day. **Before calling the director professional-quality:** obtain one approved authentic new model plan via existing prepaid AI controls, real original garment refs, human blinded review and visual inspection of rendered footage; separately observe Feature4 editor capability and Feature5 provider constraints.
- Designed as an **independent PR from main** so it does not need draft PR #514 to run. Feature2/Coordinator can later use this rubric to compare actual model plans without duplicating creative direction in Feature4.
