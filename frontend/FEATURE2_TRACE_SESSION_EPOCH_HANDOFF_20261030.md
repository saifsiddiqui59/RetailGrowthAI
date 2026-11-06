# Feature2 F2-12 / F2-32 — private trace session-epoch fencing (2026-10-30)

**Source IN PROGRESS, not accepted integrated DONE.** One scoped UI batch against existing unified draft #551.

The optional Feature2 trace panel previously cleared old results only in a post-render effect, and its asynchronous stale request catch/finally could modify newer session UI state. Its scope key was a colon-delimited string that excluded the authenticated private reader callback identity. Now a stable per-context object identity (shop, campaign, workflow, input SHA, enabled flag, and callback) tags the displayed result, error, and busy state on every render; old scope state is immediately hidden, even before effects. Async resolutions, denials, and finally cleanup are ignored when the current scope has changed. The existing backend remains the only authorized HMAC/JWT/RLS reader; the browser validates a bounded projection and **does not certify actual model execution or human/media approvals**.

Added pure negative tests for changed tenant, workflow, source digest, provider callback and role disable. Included the actual child trace JSX in the F2 Vite/esbuild component compile test instead of only checking the parent VoiceoverSelector JSX. This does NOT replace an actual mounted React/browser E2E; coordinator must create a distinct callback on signed session replacement and verify real account isolation after DEV Auth provisioning.

Requirements: coordinator original task F2-12/F2-32 integration, merge with latest main and sibling Feature2 PRs, protected Azure Functions ZIP gate #650, separate Azure DEV 503 issue #249, authenticated private trace HMAC/store and fresh 4/4 postmerge main CI. No paid AI/GPU, hosted writes, PROD, WineShopPOS or sample outputs.
