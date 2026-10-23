# Part 3 private output and probe hardening (source only)

Internal branch: `feat/p3-media-fence-hardening` -> `feat/part3-integration`.

The existing premium output importer already restricts Alibaba signed video origins, disables HTTP redirects, bounds download size, validates MP4 bytes and applies lease-fenced DB completion. This change strengthens two additional checks:

1. **Exact lease-scoped storage receipt**: after calling the existing `PrivateMedia.upload`, importer now requires the returned object path to equal `{shop_uuid}/renders/{job_uuid}/{lease_uuid}.mp4` precisely. A malicious or faulty storage adapter cannot substitute the same prefix with a suffix, additional path segment, different job or an altered extension and then mark the job complete.
2. **Local-only media probe**: `probe_mp4` invokes ffprobe with `-protocol_whitelist file` to prevent crafted provider MP4 references from causing network fetches via unexpected protocols. Media input still comes only from the bounded verified local download.

Regression coverage in `tests/reliability/test_premium_private_import.py` denies six receipt-faking variants before the database completion callback and asserts the local-only ffprobe invocation.

These are backend source/offline test changes only. No approved or paid Wan workspace, Azure deployment, Supabase hosted migration, queue provisioning or customer charge. Actual premium service integration remains disabled until formal DB/worker/security/rights/cost approvals.
