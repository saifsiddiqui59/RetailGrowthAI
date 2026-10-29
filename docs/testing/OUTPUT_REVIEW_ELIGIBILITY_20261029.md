# Testing Chat — do not rate a merely acknowledged job

## Correctness rule
A browser `PASS` from an authenticated `POST /api/campaigns` or
`POST .../renders` proves at most that the server acknowledged a **job**.
It is not proof that a usable campaign, MP4, poster or motion output exists.
Previously Testing Chat could enable a human output-quality review after an
ACK-only PASS when no final result was read back. The resulting 1/5 rating
would misidentify a delivery/reliability problem as bad creative quality.
The actionable diagnostic now calls these receipt sets `AWAITING_OUTPUT`:
no verified creative output yet, **not** a quality failure, technical
failure or permission to replay a potentially committed POST.

## Source implementation
`trace-output-evidence.mjs` exposes strict deterministic checks:
- F2: `prompt-improvement PASS` with a substantial deterministic returned
  improved prompt, or `campaign-planning PASS` with seven validated days
  and matching canonical campaign/day UUID references.
- F4: `ffmpeg-result PASS` with `status=SUCCEEDED`, canonical render
  job UUID and private output asset UUID. Queue submission alone does not
  enable audio, caption or video-quality ratings.
- F3/F5/F7: no supported real output-completion receipt in this Testing Chat
  path yet, so no rating can be attached until a reviewed, real integration
  provides its own output validation.

This is *browser-observed* evidence from already-authorized API replies,
not independent worker attestation. The existing private worker-span RPC
remains separate. The human-review form, quality aggregates and regression
priorities now reject reviews without a previous completed output event in
the same feature/run. Legacy entries with a score on an ACK-only run remain
stored as user-written history but cannot influence output quality
statistics. Failed or UNKNOWN jobs continue to require status reconciliation,
not automatic POST retry.

## Tests and deployment boundary
Node fixtures cover accepted-P0/no-result, malformed IDs, incomplete seven
days, and prohibited fake F3/F5/F7 ratings. Mocked Chromium confirms
unrateable queued-only F4 and rateable actual completed F4 output.
No database schema/grants, provider cost, worker queue, publishing, API
mutation or Azure SKU change; four exact-head CI jobs and postmerge main
remain required. Real DEV retains independently reviewed migration and
hosted signed role-denial gates. Do not touch PROD or WineShopPOS.
