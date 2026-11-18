# Feature #4 private HyperFrames adapter

Candidate runtime adapter (NOT Azure-deployed). Backend authorizes tenant/media and compiles reviewed templates in video-engine/professional.py. No user HTML, JS or URLs.

Install in isolated no-egress container with Node >=22, Chrome and FFmpeg: npm install --ignore-scripts, then node render.mjs /trusted/compiled-project /trusted/output.mp4.

@hyperframes/producer pinned to 0.8.185. Upstream repository is Apache-2.0; review npm package and transitive dependencies during image promotion. Do not use its public HTTP/hosted rendering modes. Worker needs 780s hard timeout, quota/concurrency/memory/scratch cleanup. Keep FFmpeg fallback active. Actual Chrome MP4, animation/audio, visual QA and cloud costs are NOT yet proven.
