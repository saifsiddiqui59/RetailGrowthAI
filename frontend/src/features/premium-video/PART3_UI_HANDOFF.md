# Part 3 UI handoff

This isolated frontend component is intentionally not mounted in Part 1 CampaignDashboard until final integration. FFmpeg remains the default. Wan can only appear active when server entitlement, backend support and reviewed feature flag are all true. There is no customer checkout, automatic payment, provider key or provider URL in the frontend. The final coordinator must review shared campaign UI placement and the authenticated premium API contract before mounting it.

Full existing 4-job Part 1 CI and dedicated 2-job Part 3 CI must pass on this PR before integration merge.
