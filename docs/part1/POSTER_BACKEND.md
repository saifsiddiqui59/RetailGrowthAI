# Part 1 — private poster draft persistence (source only)

Migration: supabase/migrations/20261024113000_p1_poster_drafts.sql
Disposable negative tests: tests/security/poster_draft_negative.sql

## Added
- New tenant-bound public.poster_drafts table with composite shop+campaign, day, source/logo and output asset foreign keys. Each poster is a versionable draft, not a published post.
- SELECT-only RLS for active shop OWNER, EDITOR and VIEWER; no browser direct INSERT/PATCH/DELETE, readiness or output-asset mutation.
- Authenticated, SECURITY DEFINER create_poster_draft RPC rechecks JWT auth.role and current owner/editor membership, draft campaign/day lineage, storyboard-listed image, same-tenant registered media, commercial license and evidence, optional same-tenant logo and valid template/dimensions/brand/color/offer bounds.
- Atomic per-shop subscription row lock; allowed only on active trial/subscription. SHA-256 idempotency avoids duplicate drafts for the same user/inputs. Bound to at most 21 drafts per campaign; existing render and campaign quotas unchanged.
- No generated outputs, queue jobs, payment, SMTP, migration deployment or public share URLs are created by this change.

## Not enabled yet
- The web Canvas preview currently stays in the browser until a backend API is connected. This metadata RPC is not wired into the frontend or HTTP gateway.
- Future migration must add poster render_jobs, worker leases, durable outbox and failure recovery consistent with the existing FFmpeg worker; must not alter Part 2 publishing or Part 3 premium ledger.
- Future service must stage private registered assets, recheck active tenant and rights at render and download, call poster-engine, upload private PNG with immutable server-owned key, register generated media and attach existing instagram.banner_asset_id only after authenticated user selection, with full RLS tests.
- Proposed SQL must be reviewed and separately authorized before applying to dedicated RetailGrowthAI DEV Supabase; never WineShopPOS.

CI: this migration is run by disposable Supabase SQL setup and poster_draft_negative.sql is discovered by the Part 1 workflow. Check the exact four jobs before internal PR merge.
