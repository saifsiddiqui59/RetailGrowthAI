# Part 1 — approval notification emails (source only)

## Scope and status
- Retains Supabase Auth verification/reset emails as a **separate provider setup**.
- Retailer signup and root approval/rejection now enqueue private, tenant-agnostic notification events transactionally via `20261024160000_p1_notification_outbox.sql`.
- Stores event type, user ID and deduplication key, **not recipient address, tokens, passwords or verification links**. Backend resolves recipients from confirmed RetailGrowthAI Auth users at send time. Signups go only to active, confirmed platform administrators.
- New backend `notification_store.py` calls service-role-only claim/recipient/ack RPCs. `notification_worker.py` sends plain-text, branded links over SSL-only SMTP port 465, with at-least-once delivery, lease tokens, bounded retry/backoff and dead-letter state after 8 attempts.
- `function_app.py` has a ten-minute timer guarded by `RETAIL_NOTIFICATIONS_ENABLED=true`. OFF by default: no SMTP calls or live sends before explicit owner setup.
- No Part 2/Part 3, WineShopPOS or existing confirmation/recovery email credentials are referenced. No hosted resources or migrations were altered.

## Operator gates — not yet performed
1. Review security CI and apply the additive migration to **RetailGrowthAI DEV only** using a separately approved, backed-up migration.
2. Provision dedicated authorized RetailGrowthAI SMTP mailbox/domain credentials (never copy WineShopPOS), configure SPF/DKIM/DMARC and verify real inbox delivery/links.
3. Set backend-only `RETAIL_SMTP_HOST`, `RETAIL_SMTP_PORT=465`, `RETAIL_SMTP_USERNAME`, `RETAIL_SMTP_PASSWORD`, `RETAIL_SMTP_FROM`, `RETAIL_WEBSITE_ORIGIN` and `RETAIL_NOTIFICATIONS_ENABLED=true` only after steps 1-2. Never use `VITE_*` for secrets.
4. If reliable exactly-once email is required, use a transactional email provider with a stable event idempotency key: generic SMTP cannot promise exactly-once after a lost ACK or partial multi-recipient send. Current implementation is explicitly at-least-once.
5. Conduct controlled signup, root approve/reject, delivery/failure/retry tests without logging addresses, SMTP credentials or links with auth tokens.

## Source verification
- `tests/reliability/test_notification_worker.py` covers default-off delivery, status confirmation, missing recipients, email safety and SMTP errors.
- `tests/security/notification_outbox_negative.sql` runs in disposable CI to verify authenticated/anonymous denials and fenced service-only delivery.
- No claim of live mailbox delivery is made.
