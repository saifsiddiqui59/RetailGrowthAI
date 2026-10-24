# Super Admin subscription watch handoff — source-only

- Feature branch `feat/p1-superadmin-subscription-watch` based on `feat/part1-completion`. Adds `SubscriptionHealthPanel.jsx`, pure helper and CSS, wired into existing `PlatformAdmin.jsx` without touching subscription RPC or security grants.
- Tracks **only the loaded directory page** (up to 25 shops), counts due in seven days, expired, suspended, and unknown subscription dates. Client-side filters/search and existing audited `Manage plan` action; no payment charges, renewals, billing emails or platform-wide expiry coverage are implied.
- Requires Part 1 lead to merge after 4/4 CI, run independent integration/main CI and deploy through separately authorized DEV-only frontend release. Existing trial, shop RLS and subscription ledger unchanged.
