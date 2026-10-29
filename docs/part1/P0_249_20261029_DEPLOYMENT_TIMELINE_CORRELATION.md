# Azure #249: Original baseline vs candidate deployment timeline (29 Oct 2026)

**Evidence class:** actual protected Azure Portal deployment diagnostic observations and immutable GitHub Actions stdout. **Verdict:** Original Python Flex HTTP503 remains unresolved; overlapping deployment cannot alone explain the incident.

## Azure Flex Consumption Deployment (read-only)

Existing tagged Central India RetailGrowthAI DEV only. [Portal session](https://agent.tinyfish.ai/runs/de90970d-897f-45a7-844f-a002c37a33ec) opened the Microsoft-documented **Flex Consumption Deployment** detector. Its default Last 24 Hours view displayed two Azure CLI Python 3.12 deployment pipelines starting **2026-10-28 19:34:30 UTC** and **19:50:08 UTC**. The latter site's update displayed **19:50:42 UTC, 6/6 instances updated**, while the detector also displayed a contradictory **Function app updates summary = Failed** (“errors in deployment pipeline logs”).

The displayed Oryx/Python build steps completed, including pip dependencies; **no host.json permission or package mount error appeared in the inspected deployment step logs**, and no named activation failure was surfaced. Do not turn absence of a matching filtered log into proof of no host/worker problem. Six distinct instances updated is compatible with independent HTTP/Queue/Timer Flex scale groups; not evidence that HTTP had six instances. Nor does “100% updated” verify byte-identical prior rollback ZIP or a stable authenticated API. Do **not** label the contradictory Failed summary as definitely benign without its underlying failure cause.

## Time-correlation against separately recorded HTTP observations

| Actual independent test | UTC window | Original Python Flex | Existing Free SWA Node | Deployment relevance |
|---|---|---|---|---|
| [Original equal-route #40691854364](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40691854364) | ~12:55–13:10 Oct 28 | **9/20 genuine app-unmarked ~61s 503** | **0/20 503** | **Hours before** observed 19:34/19:50 activity, so latter deployments cannot cause this baseline |
| [Unmerged import-isolation candidate #40755301253](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40755301253) | 19:33–19:51 Oct 28 | **9/20 genuine ~61s 503** | **0/20 503** | Overlaps first candidate package deployment/rollout at 19:34 and rollback at 19:50; rollout is a **confounder**, but not proof of all failed GET causes |
| [Postrollback original #40759193001](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40759193001) | 19:59–20:01 Oct 28 | One application 401 (5.021s), then one genuine unmarked 503 (61.009s) | Not checked | After detector's 19:50:42 completion; no evidence the update itself produced this later failure |

Across actual observed runs: TLS completed; timed-out original 503 responses had **no Python handler request marker**. Application Insights [#40768869977](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40768869977) reported 11 explicit 401 and 14 missing/zero result codes, NOT nine matched 503 records. The new deployment detector **does not provide individual edge request → HTTP scale group → host specialization or Python language worker correlation**.

## Next actions that would change the answer

1. **Do not conflate two issues:** the “Failed” deployment summary vs successful-looking Oryx/instance-update entries merits targeted read-only review (exact failing step and package activation), but no identified 503 trigger is yet demonstrated. Do not deploy speculative ZIP modifications, buy AlwaysReady or raise concurrency just because the failures occur around one minute.
2. Preserve original baseline **predeployment** 9/20, and seek the Azure internal per-request ingress/HTTP-group host/specialization worker logs if accessible; if not, retain blocker `AZURE_INTERNAL_TRACE_REQUIRED`. No Microsoft support ticket unless owner changes that restriction.
3. Separately complete **protected manual** `node-poster-reel` and `node-browser-reel` real JWT/RLS full media canary now integrated through #605, original queue/FFmpeg and signed download acceptance, and repeated Node HTTP reliability. Only then consider an approved tenant-safe frontend HTTP cutover.
4. Preserve no retry of mutating POST/PATCH on uncertain acknowledgment, strict role/tenant checks and private media rights. **No cloud resource/settings/paid plan, customer traffic, PROD or WineShopPOS changes** occurred through the diagnostic run.

Official references: [Azure Functions deployment technologies](https://learn.microsoft.com/en-us/azure/azure-functions/functions-deployment-technologies), [Azure Functions Flex package deployment](https://learn.microsoft.com/en-us/azure/azure-functions/deployment-zip-push), [Functions troubleshooting](https://learn.microsoft.com/en-us/troubleshoot/azure/azure-functions/availability/functions-troubleshoot-issues).
