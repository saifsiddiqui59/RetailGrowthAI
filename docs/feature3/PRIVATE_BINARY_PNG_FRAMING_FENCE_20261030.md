# Feature3 F3-08 / F3-13 — private binary PNG framing fence (2026-10-30)

**Status: IN PROGRESS (source-only).** Not integrated or hosted DONE.

The future authenticated no-URL HTTP adapter now independently rejects reader receipts that have a matching SHA-256 but do not begin with the PNG signature and end with the canonical IEND chunk. A valid immutable SHA is necessary but not sufficient for image/PDF content safety. The existing trusted reader remains responsible for complete Pillow decode, current signed JWT/RLS rights and post-read revocation checks.

Fixture-only tests cover forged non-PNG bytes, valid PNG with appended payload, truncated IEND, and unchanged valid PNG. No customer poster was generated or accepted. The Azure route remains **unmounted**, no live output or approved rights were verified, and GPU/paid inference stayed OFF.

**Acceptance still blocked by:** #471 / #325 (Feature3/coordinator-owned signed no-URL route and real private generated output); F3-LICENSED-MEDIA (rights reviewer-approved source); #249 (Azure reliability lead's hosted signed 503 proof); DEV-AUTH-TEST-USERS (Auth Admin/operator two nonprivileged isolated shops); F5-GPU-AUTHORIZATION / PART3-WAN22-CONTRACT (coordinator paid runtime release). Acceptance requires coordinator merge, fresh four-job main CI, real signed DEV negatives and current commercial rights. No shared canonical docs or task manager mutated by this worker; coordinator must review proposed evidence before any DONE event.

No PROD, hosted SQL, samples, WineShopPOS, or extra paid infrastructure.
