# Part 2 decisions — 2026-10-23

1. **Separated secrets:** public `social_accounts` has display metadata only; OAuth access/refresh ciphertext, verification state and claim tokens live in `retail_private`. Authenticated browser users have RLS-limited SELECT on public metadata, no INSERT/UPDATE to publish on their own.
2. **Approval-first:** approved-content SHA-256 binds an exact reviewed caption/media/version. Edits invalidate approval. Draft status is never a publish instruction.
3. **Idempotent external writes:** one local logical job and reserved publishing unit, unique shop/account/idempotency key; ambiguous provider calls become RECONCILE, not automatic retry.
4. **Version-aware official integrations:** Instagram Reels require container creation, processing state and separate media publish; Facebook API scope is Page feed only for initial adapter; LinkedIn REST Posts text only initially; YouTube API resumable session initializes PRIVATE by default. No claim that an initialized upload is an uploaded Short.
5. **No silent scope upgrades:** provider privileges require app review and user-granted permissions. The live-dispatch worker remains disabled until explicit approval, media provenance, quota and remote receipts are tested.
6. **Pending-only migration:** P2 social schema is staged under `supabase/part2/pending`, not `supabase/migrations`, to preserve Part 1's pinned migration CI and prevent unapproved hosted application. Review collision/timestamp and disposable SQL negative tests before moving into canonical migration sequence.
7. **Part 1 preservation:** P2 plans do not alter P1 campaign/render usage or renewal/billing. A separate owner-approved publish quota is needed. No Postiz or Razorpay.
