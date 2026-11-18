# Feature #4: pinned npm distribution-license review — NOT YET CLEARED

**Source-only review, 2026-10-28. No legal signoff, no Azure deployment.**

## Exact evidence source

- Existing [GitHub Actions #40676843934](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40676843934) passed all four jobs and **121 media tests** on source head `34ef8af7d2f8ae9e90ad6deb782c881650eaf259`.
- The FFmpeg smoke artifact includes the resolved npm v3 `feature4-review-package-lock.json` (69,904 bytes). Its SHA-256 is `2b4016fde9514ac2771660a3a1e81389ee3b1237c72db6acfa1fc540494948a6`; 138 entries including the root package, 137 installed dependency entries, all with approved npm registry HTTPS URLs and SRI integrity fields.
- **Current Feature4 branch:** the exact reviewed 69,904-byte `video-engine/hyperframes/package-lock.json` is Git-tracked, and `ci-smoke.sh` invokes `lock_guard.py` **before direct `npm ci`** (without temporary install-time lock generation). Previous CI used the same exact SHA after generating a temporary lock; NEW exact-commit CI is required to certify the clean-checkout approach.
- The reviewed upstream source tag is [heygen-com/hyperframes v0.8.185](https://github.com/heygen-com/hyperframes/tree/v0.8.185), which contains the repository's Apache-2.0 LICENSE. The pinned npm package manifests for `@hyperframes/producer`, `core`, `engine`, and `studio-server` omit individual `license` metadata. A missing npm license field is **not** evidence of no license, nor proof every bundled file is Apache-2.0.

## License declarations in the resolved npm lock

| License metadata | Package entries |
| --- | ---: |
| MIT | 71 |
| Apache-2.0 | 19 |
| BSD-2-Clause | 13 |
| ISC | 9 |
| LGPL-3.0-or-later | 10 |
| Apache-2.0 AND LGPL-3.0-or-later | 3 |
| Apache-2.0 AND LGPL-3.0-or-later AND MIT | 1 |
| BSD-3-Clause | 3 |
| Python-2.0 | 1 |
| 0BSD | 1 |
| Missing package metadata | 6 |

The 6 missing fields concern pinned `@hyperframes/{core,engine,lint,parsers,producer,studio-server}` at 0.8.185. The LGPL entries are predominantly Sharp's optional platform-specific libvips variants; these are not proof that all variants ship in a Linux Azure deployment. Track the actual runtime contents and native dynamic/static linking before preparing a third-party notice or license-distribution assessment.

## Production packaging obligations still open

1. Export the **exact runtime SBOM** from the actually deployed package/image, not just the cross-platform npm lock. Distinguish optional platforms that were not installed.
2. Collect upstream notices and full license texts for HyperFrames v0.8.185, npm dependencies, bundled Puppeteer/Chromium Headless Shell and the particular installed Chrome version, and any binary redistribution conditions.
3. Inspect the exact FFmpeg binary's configured build flags and linked libraries, not only the `ffmpeg` command name. The build could have LGPL/GPL/nonfree consequences.
4. Determine compliance and notices for Sharp/libvips including LGPL dependency terms in the actual distribution model; consult qualified licensing counsel if required.
5. **SOURCE IMPLEMENTED; CI verification pending:** exact standard `package-lock.json` is committed to Feature4, temporary lock generation removed, and clean-checkout `npm ci` SHA-verified first. Still review install scripts and all future dependency upgrades under explicit pin-change PRs.
6. Execute cost-bounded, coordinator-authorized Azure runtime verification separately; source CI does not prove Azure memory, cold start, hosting SLA, access controls or published customer-facing quality.

**Security boundary:** no dynamic dependency drift, arbitrary HTML, public media, external model inference, new GPU, Azure state mutation or WineShopPOS modifications were introduced by F4-12. The automated license report states `legal_signoff_for_commercial_saas=false` and must remain non-approving until reviewed.
