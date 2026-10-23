# Part 3: explicit human approval gate for paid provider calls

A campaign created by Part1 Foundry is `status=DRAFT` and its generated `campaign_days.review_status` is initially `DRAFT`. Previously the source-only Part3 coordinator and prospective SQL reservation denied only `REJECTED`, which could permit a DRAFT day to be submitted to an external paid provider if premium were activated.

**Security fix**: the Part3 coordinator now requires `review_status == 'APPROVED'` for the selected day, and the review-only, NOT APPLIED Part3 SQL reservation trigger uses the exact same predicate. Neither `DRAFT`, `REJECTED` nor missing status can reserve a provider job or transfer business content. The request still requires authenticated OWNER/EDITOR and documented commercial rights.

The current Part1 API may not yet provide an explicit authorized `DRAFT -> APPROVED` campaign-day transition. Do not weaken this gate to force testing. Owner/coordinator must define an authenticated, tenant-scoped, version-pinned human approval workflow and its edit-revocation semantics before premium activation. This source change does not promote the pending SQL migration, and no paid API, cloud, live DB, shared Part1 code or Part2 code was touched.

Regression tests in `tests/api/test_premium_video_jobs.py` exercise all negative review states and verify the check runs before any media/credit reserve. Run existing 4/4 plus Part3 dedicated 2/2 CI before Part3 internal merge.
