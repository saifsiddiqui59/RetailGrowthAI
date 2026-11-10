# Feature #2 — Live music and hosted DEV acceptance gate (2026-10-28)

## What is actually connected

- Added \`ai_agents.feature2_live_music\` using **official YouTube Data API** \`videos.list\` with \`chart=mostPopular\`, \`regionCode=IN\`, \`videoCategoryId=10\`, max 25 results. Public music VIDEO metadata supplies **popularity observations**, not verified "viral songs on Instagram" or "YouTube Top Songs on Shorts" chart metrics.
- Reuses Feature #2 \`recommend_audio\` and the existing category-sensitive draft-only audio recommendation UI/contract; no audio download, music playback, remix rights, automatic social posting, model egress or GPU.
- Transport is **disabled by default**. To make an authentic provider call, an approved server runtime must set \`RETAIL_FEATURE2_MUSIC_YT_ENABLED=true\` and **server-only** \`RETAIL_FEATURE2_MUSIC_YT_API_KEY\`. The current developer environment did not have such a key; CI uses simulated official response bytes.
- Auth boundary requires callable current *real* signed user JWT/RLS shop reader, executed before and after the network request. A fake/untrusted shop ID never enables import or music publication. The underlying \`_get\` restricts Google origin, endpoint, all query keys and enforces no redirects, no key logging and 256 KB response cap.
- The source endpoint exists as a callable adapter, **not yet wired into hosted Azure Function** or a web page release. An official Instagram trending music catalogue API has not been verified and therefore **not claimed**.

## Real Pexels license review

All four named source pages from \`ai-agents/test-fixtures/clothing-shop-pexels/manifest.json\` were opened on Pexels' official website on 2026-10-28; creators and item existence were confirmed. Pexels' public License page explicitly allows most free commercial advertisement and social usage, with modification and attribution optional. **This confirms only the provider's general grant.** The pages featuring women (Vitaly Gariev image and Lara Jameson video) have people visible and **no independently verified model releases, endorsements or garment ownership**. Such media remain unapproved for depicting the retailer's product/model. The Maria Orlova clothes-rack still and Ron Lach hanging-clothes video are possible generic background B-roll, pending original byte import and third-party visual rights assessment. Real ORIGINAL downloaded media byte hashes and private tenant uploads are still **not** available (runtime has blocked outbound DNS, no Pexels API key). General license terms cannot substitute those checks.

Pexels: https://www.pexels.com/license/
Pexels help: https://help.pexels.com/hc/en-us/articles/360042295214-Can-I-use-the-photos-and-videos-for-a-commercial-project
YouTube developer API: https://developers.google.com/youtube/data/reference/rest/v3/videos/list
YouTube Charts: https://support.google.com/youtube/answer/9014376

## Hosted truth

Read-only external request successfully reached **https://purple-dune-06b5da200.2.azurestaticapps.net/** and returned a branded sign-in page (2026-10-28). Supabase DEV project \`jeearzffnjbvghwjjjrf\` is ACTIVE_HEALTHY, with two shop rows, one active membership and one media row; public shop membership/media/campaign tables have RLS. **This did not authenticate as an OWNER, import or render anything**. No connected browser has a Supabase signed-in profile; administrative SQL is not a replacement for a live tenant JWT. Existing Azure #249 503 still blocks accepted private hosted flows. Neither a cloud deployment, completed hosted MP4, nor real paid AI inference was performed. We must wait for an actual OWNER/EDITOR login, a verified Pexels API key and real source image/video SHA plus rights review before tenant-private Storage + hosted Reel acceptance.

## Test coverage

New negative/positive Python tests exercise live endpoint construction, category filtering, 25-row bounds, immediate disabled/no-key failure without egress, malicious media metadata, authoritative shop access before/after provider fetch, copyright fail closed, provider outage and duplicate/foreign audio IDs. These tests use mock HTTP bytes; passing them is not a live production chart result.

Existing \`/trends\` free **Improve Prompt with AI** checkbox auto-previews enhanced prompts (requires user explicit Apply); real Foundry enhancement requires a separate approved-budget toggle and click. Keep that behavior.

### Hosted schema constraint independently confirmed

`public.register_uploaded_image` in existing `supabase/migrations/20261022173000_p1_private_upload_registration.sql` accepts authenticated OWNER/EDITOR, checks actual Storage object metadata and `uploads/` paths, supports **JPEG/PNG/WebP only** and persists `source='UPLOAD'`. It does **not** accept licensed Pexels video or register `STOCK` as a separate reviewed provenance class. Writing `media_assets` directly through the admin connector to impersonate signed-in asset import would bypass intended checks and would not be compliant. Coordinator must provide an additive signed real stock-media import and video registration contract before live shop attachment. The real DEV browser has no saved Supabase sign-in in this session. No fake account or synthetic review receipt can replace these conditions.

### Anonymous DEV smoke actually executed

Read-only web requests to `/trends`, `/campaigns`, and `/platform-admin` all redirected to the hosted `/account` sign-in. This is a positive observation of anonymous route gating, **not** a verified API JWT/RLS test or hosted Reel success. The prior unmerged Azure #249 Python 503 behavior is separately unresolved.
