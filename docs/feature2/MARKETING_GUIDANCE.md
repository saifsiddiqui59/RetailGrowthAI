# Feature 2 editorial approach — source workstream AI-B (#402)

**Design choice:** Use reviewed marketing principles as inspiration for a small,
auditable first-party editorial guidance layer, not as a third-party executable
agent in our multi-tenant runtime.

Reference project: https://github.com/coreyhaines31/marketingskills
Source inspected 2026-10-26:
- `skills/copywriting/SKILL.md`
- `skills/content-strategy/SKILL.md`
- `skills/copy-editing/SKILL.md`

The upstream project is MIT-licensed (Copyright © 2025 Corey Haines).
Upstream license: https://github.com/coreyhaines31/marketingskills/blob/main/LICENSE

No upstream code or substantial text is copied into our module. Our own
`marketing_guidance.py` is a concise independent implementation inspired by
general public marketing principles: know the audience and objective, give
each day one useful idea, avoid tired generic copy, vary hooks, give appropriate
platform-specific creative direction, and edit for clarity/voice/trust.

**Inputs:** only the authenticated, signed caller's `RetailerProfile`,
original retailer request and explicitly selected channels. No front-end
submitted business/tenant identifiers, third-party skill downloads or
unverified facts. No subscription, secrets, customer profiles, or private media
are transmitted by the guidance itself.

**Outputs:** one short editorial brief and optional deterministic advisory
scorecard for day count, repeated topics/hooks, missing copy, restricted claims
and maximum lengths. All content is DRAFT and human approved; a score is not
legal sign-off, source-backed Google Trends evidence, automatic post approval,
or proof that an LLM was called.

**Integration dependency:** AI-C (#403) must wire this guidance into the
approved actual model path alongside AI-A (#401), preserving billing reservations,
JWT/RLS, safe media use, a strict output schema and canonical campaign v1.
Source completion/green unit tests alone do NOT mean real model inference
has executed. No Azure/GPU/Figma/Supabase spending or schema writes in this
workstream.
