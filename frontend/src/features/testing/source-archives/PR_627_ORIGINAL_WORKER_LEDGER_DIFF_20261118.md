# Original DRAFT PR #627 source proposal — complete patch archive (2026-11-18)

Original https://github.com/saifsiddiqui59/RetailGrowthAI/pull/627 exact head `6ef9788a26661c07a3feb851dfe1cb0209b310da` with five changed-file patch hunks.

This is preserved history, **not** a production backend or trusted JWT/RLS acceptance. Main has a NEWER TestingConsole and `createTraceStore.listWorkerSpans(shopId, jobIds)` API; old `readTrustedWorkerSpans(shopId, jobId, 30)` and old UI must not overwrite it. A separately adapted current-API Node regression in the source extraction covers current source and tenant rejection. This archive retains all original changed-file patches and author task notes, not a claim of code parity or Feature #1/F2/F4/F7 DONE.

```diff
diff --git a/docs/testing/TRUSTED_WORKER_READ_UI_20261029.md b/docs/testing/TRUSTED_WORKER_READ_UI_20261029.md
@@ -0,0 +1,45 @@
+# Testing Chat — signed private trusted worker evidence panel
+
+## Source contract
+A retailer Testing Chat run first stores its browser-observed per-feature
+receipts and optional human quality opinions. A separate "Check verified
+worker spans" control performs an **explicit read-only** per-job lookup of
+the **backend-only** ledger created by the separately staged
+`retail_feature_worker_spans` RPC from #622.
+
+- The existing client uses its current signed-in user JWT and the
+  publishable key. Never sends a service key, accesses private tables
+  directly, or reads another shop without the DB's fresh active
+  OWNER/EDITOR membership check.
+- Lookup uses at most two server-known job UUIDs (F2 campaign and F4
+  current Part1 FFmpeg render), a 30-row cap per call, and never enqueues
+  or changes campaign state. The backend RPC derives data from
+  `retail_private.feature_worker_spans` only if its source is
+  `trusted_backend_persisted`.
+- The client requires exactly matching `shop_id`, `job_id`, allowed
+  F2/F4 feature-operation-terminal status, bounded attempts/duration,
+  exact output metadata, unique event UUIDs, and an event count within
+  the requested limit. On malformed, unauthorized, unavailable or
+  missing RPC, it displays **unverified/unavailable**, never PASS.
+- Browser-observed text and runtime HTTP marker remain separate from
+  trusted backend evidence. The UI never upgrades a browser PASS or
+  human 5/5 review to proof that a GPU/VTON/editor ran.
+- React clears stale worker evidence when the selected shop, test run
+  or active user request changes; late responses cannot populate
+  another tenant's report.
+
+## Release and remaining gaps
+This is source-only. Host DEV must first receive two distinct reviewed
+canonical migrations: browser trace run/event tables (#614 candidate)
+and service-only worker span ledger (#622 candidate). The source worker
+sink (#624) must be explicitly enabled only after its real SQL migration,
+role-denial verification and protected deployment. Then release the UI
+through existing RetailGrowthAI DEV Static Web App workflow and run
+signed OWNER/EDITOR, VIEWER, cross-tenant and revoked-account tests.
+Without that complete chain the panel intentionally shows no
+verified backend result.
+
+No Feature3, Feature5, or Feature7 execution is inferred from empty
+ledger responses. Feature4 currently verifies only the existing 30s
+FFmpeg Reel pipeline, not the professional video compositor. Azure
+issue #249 remains open. No paid providers, PROD or WineShopPOS changes.

diff --git a/frontend/src/features/testing/TestingConsole.jsx b/frontend/src/features/testing/TestingConsole.jsx
@@ -75,6 +75,10 @@ export default function TestingConsole() {
   const [baselineError, setBaselineError] = useState('')
   const [historyStats, setHistoryStats] = useState(null)
   const [analyzingHistory, setAnalyzingHistory] = useState(false)
+  const [trustedSpans, setTrustedSpans] = useState([])
+  const [verifyingWorkers, setVerifyingWorkers] = useState(false)
+  const [workerProofError, setWorkerProofError] = useState('')
+  const workerProofEpoch = useRef(0)
   const [ratingFeature, setRatingFeature] = useState('F2')
   const [rating, setRating] = useState(3)
   const [reviewNote, setReviewNote] = useState('')
@@ -124,6 +128,7 @@ export default function TestingConsole() {
     setHistory([]); setEvents([]); setActiveRun(null); setError(''); setOutcome('')
     setBaselineId(''); setBaselineEvents([]); setBaselineError('')
     setHistoryStats(null); setAnalyzingHistory(false)
+    ++workerProofEpoch.current; setTrustedSpans([]); setWorkerProofError(''); setVerifyingWorkers(false)
     setAssets([]); setAssetId('')
     if (!shopId || !store) return () => { alive = false }
     Promise.all([store.listRuns(shopId), client.listMediaAssets(shopId)]).then(([runs, media]) => {
@@ -144,6 +149,7 @@ export default function TestingConsole() {
     try {
       const loaded = await store.listEvents(shopId, run.id)
       if (selection.current !== shopId) return
+      ++workerProofEpoch.current; setTrustedSpans([]); setWorkerProofError(''); setVerifyingWorkers(false)
       setActiveRun(run); setEvents(loaded)
       setBaselineId(''); setBaselineEvents([]); setBaselineError('')
     } catch {
@@ -193,6 +199,7 @@ export default function TestingConsole() {
     busy.current = true
     networkEvidence.current = []
     setRunning(true); setError(''); setOutcome(''); setEvents([])
+    ++workerProofEpoch.current; setTrustedSpans([]); setWorkerProofError(''); setVerifyingWorkers(false)
     setBaselineId(''); setBaselineEvents([]); setBaselineError('')
     setHistoryStats(null)
     const id = crypto.randomUUID()
@@ -222,6 +229,38 @@ export default function TestingConsole() {
       busy.current = false; setRunning(false)
     }
   }
+  const workerJobs = useMemo(() => {
+    const candidates = [
+      events.find(e => e.feature === 'F2' && e.action === 'campaign-planning' &&
+        typeof e.details?.campaign_id === 'string')?.details?.campaign_id,
+      events.find(e => e.feature === 'F4' && e.action === 'ffmpeg-submission' &&
+        typeof e.details?.render_job_id === 'string')?.details?.render_job_id,
+    ]
+    return [...new Set(candidates.filter(Boolean))]
+  }, [events])
+  async function verifyTrustedWorkers() {
+    if (!store || !activeRun || !workerJobs.length || running || verifyingWorkers ||
+        activeRun.shop_id !== shopId) return
+    const epoch = ++workerProofEpoch.current
+    setVerifyingWorkers(true); setWorkerProofError(''); setTrustedSpans([])
+    const requestShop = shopId
+    try {
+      // Only explicit read-only, signed and shop-scoped calls. No worker mutation.
+      const found = []
+      for (const jobId of workerJobs.slice(0, 2)) {
+        const spans = await store.readTrustedWorkerSpans(requestShop, jobId, 30)
+        if (workerProofEpoch.current !== epoch || selection.current !== requestShop) return
+        found.push(...spans)
+      }
+      if (workerProofEpoch.current === epoch && selection.current === requestShop) {
+        setTrustedSpans(found)
+      }
+    } catch {
+      if (workerProofEpoch.current === epoch && selection.current === requestShop) {
+        setWorkerProofError('Trusted backend spans are unavailable or could not be authorized/verified in DEV. No worker success is assumed.')
+      }
+    } finally { if (workerProofEpoch.current === epoch) setVerifyingWorkers(false) }
+  }
   async function submitReview(event) {
     event.preventDefault()
     if (!activeRun || savingReview || running || activeRun.created_by !== user?.id ||
@@ -339,6 +378,23 @@ export default function TestingConsole() {
           <div className="rgt-stages">
             {FEATURES.map(([id, title]) => <StageCard key={id} feature={id} title={title} events={events} />)}
           </div>
+          <section className="rgt-trusted" aria-label="Independently verified backend worker evidence">
+            <h3>Backend worker evidence · separate from browser QA</h3>
+            <p>Server-verified spans are fetched from the private service-only ledger, not from a user-written PASS receipt.</p>
+            <button type="button" disabled={running || verifyingWorkers || !workerJobs.length}
+              onClick={verifyTrustedWorkers}>
+              {verifyingWorkers ? 'Checking signed backend evidence…' : 'Check verified worker spans'}
+            </button>
+            {!workerJobs.length && <p>No campaign or render job ID was returned in this test.</p>}
+            {workerProofError && <p role="alert" className="rgt-error">{workerProofError}</p>}
+            {trustedSpans.length === 0 && !workerProofError && !verifyingWorkers &&
+              <p>No trusted worker span has been loaded. This is not a worker PASS.</p>}
+            {trustedSpans.map(span => <details key={span.id}>
+              <summary><strong>BACKEND VERIFIED</strong> · {span.feature} · {span.operation} · {span.status} · {span.elapsed_ms}ms</summary>
+              <pre>{JSON.stringify({job_id: span.job_id, attempt: span.attempt,
+                metadata: span.metadata, recorded_at: span.recorded_at}, null, 2)}</pre>
+            </details>)}
+          </section>
           <section className="rgt-comparison" aria-label="Compare output with a past test">
             <h3>Compare with a previous run</h3>
             <label>Baseline test

diff --git a/frontend/src/features/testing/testing-console.css b/frontend/src/features/testing/testing-console.css
@@ -1,3 +1,4 @@
 .rgt-page{max-width:1440px;margin:0 auto}.rgt-layout{display:grid;grid-template-columns:minmax(230px,300px) minmax(0,1fr);gap:16px;align-items:start}.rgt-layout .panel{margin:0 0 16px;min-width:0;padding:20px}.rgt-layout h2{font-size:18px;margin:0 0 8px}.rgt-layout p{font-size:13px;line-height:1.55}.rgt-layout label{display:grid;gap:7px;font-size:13px;font-weight:600}.rgt-layout input,.rgt-layout textarea,.rgt-layout select{width:100%;min-width:0;padding:10px;border:1px solid #bfcecf;border-radius:9px;background:var(--rg-surface,#fff);color:inherit;font:inherit}.rgt-layout textarea{resize:vertical}.rgt-options{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:15px 0}.rgt-primary{background:#136956;color:#fff;border:0;padding:12px 20px;border-radius:9px;font-weight:700;cursor:pointer}.rgt-primary:disabled{opacity:.55;cursor:not-allowed}.rgt-run-list{display:grid;gap:8px;margin-top:15px;max-height:620px;overflow:auto}.rgt-run{display:grid;gap:5px;text-align:left;border:1px solid #c9d9d8;border-radius:10px;background:transparent;color:inherit;padding:11px;cursor:pointer;overflow-wrap:anywhere}.rgt-run small{font-size:11px;opacity:.72}.rgt-run.selected{border-color:#19846b;background:rgba(25,132,107,.08)}.rgt-results-title{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}.rgt-results-title small{font-size:11px;opacity:.65;overflow-wrap:anywhere}.rgt-results-title button,.rgt-quality button{border:1px solid #8ba8a3;border-radius:8px;background:transparent;color:inherit;padding:9px 12px;cursor:pointer}.rgt-message{border-radius:12px;background:rgba(65,121,146,.08);padding:15px;margin:15px 0}.rgt-message p{margin:5px 0;overflow-wrap:anywhere}.rgt-disclaimer{opacity:.8}.rgt-stages{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.rgt-stage{min-width:0;border:1px solid #cadbda;border-radius:12px;padding:13px}.rgt-stage-head{display:flex;align-items:center;justify-content:space-between;gap:7px;flex-wrap:wrap;margin-bottom:7px}.rgt-stage-head strong{font-size:13px}.rgt-pill{display:inline-flex;border:1px solid #afc2c0;border-radius:20px;font-size:10px;font-weight:800;letter-spacing:.04em;padding:4px 8px}.rgt-PASS{color:#116147;border-color:#2d9978}.rgt-FAIL{color:#a12f38;border-color:#b84d58}.rgt-UNKNOWN{color:#966019;border-color:#c69147}.rgt-NOT_RUN,.rgt-UNOBSERVED{color:#596b71}.rgt-stage details{padding:8px 0;border-top:1px solid #e5ecec}.rgt-stage summary{font-size:12px;line-height:1.5;cursor:pointer}.rgt-stage pre{overflow:auto;max-height:320px;white-space:pre-wrap;overflow-wrap:anywhere;border-radius:8px;padding:10px;background:rgba(102,121,128,.08);font-size:11px}.rgt-review{font-size:12px!important;border-top:1px solid #e4eded;padding-top:8px}.rgt-quality{display:grid;gap:12px;margin-top:20px;padding-top:17px;border-top:1px solid #cadbda}.rgt-quality .rgt-options{grid-template-columns:repeat(2,minmax(0,1fr));margin:0}.rgt-quality h3{margin:0}.rgt-error{color:#b33f47;font-weight:700}.rgt-outcome{color:#116c50;font-weight:700}@media(max-width:960px){.rgt-layout{grid-template-columns:1fr}.rgt-run-list{max-height:170px}.rgt-options{grid-template-columns:1fr 1fr}}@media(max-width:630px){.rgt-stages,.rgt-options,.rgt-quality .rgt-options{grid-template-columns:1fr}.rgt-layout .panel{padding:14px}}
 
 .rgt-diagnostics,.rgt-comparison{padding:14px;margin:15px 0;border:1px solid #c9d9d8;border-radius:12px;background:rgba(92,134,130,.045)}.rgt-diagnostics h3,.rgt-comparison h3{margin:0 0 9px;font-size:15px}.rgt-compare-table{overflow-x:auto;margin-top:12px}.rgt-compare-table table{width:100%;border-collapse:collapse;min-width:540px;font-size:12px}.rgt-compare-table td,.rgt-compare-table th{padding:9px 8px;border-bottom:1px solid #cedddb;text-align:left;white-space:normal}.rgt-compare-table th{font-weight:700}.rgt-comparison select{max-width:100%;margin-top:8px}
+.rgt-trusted{border:1px solid #a8c5c0;border-radius:12px;padding:15px;margin:17px 0;background:rgba(41,124,104,.055)}.rgt-trusted h3{font-size:15px;margin:0 0 6px}.rgt-trusted button{border:1px solid #4e9b86;border-radius:9px;padding:10px 14px;background:transparent;color:inherit;font-weight:700;cursor:pointer}.rgt-trusted button:disabled{opacity:.55;cursor:not-allowed}.rgt-trusted details{margin-top:10px;padding:10px;border-top:1px solid #b5d0cb;overflow-wrap:anywhere}.rgt-trusted summary{cursor:pointer;font-size:12px;line-height:1.5}.rgt-trusted pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:220px;overflow:auto;font-size:11px}

diff --git a/frontend/src/features/testing/trace-store.mjs b/frontend/src/features/testing/trace-store.mjs
@@ -42,7 +42,72 @@ export function createTraceStore({ supabaseUrl, publishableKey, tokenProvider, f
     if (!UUID.test(value || '')) throw new Error('Invalid tenant trace ID')
     return value
   }
+  async function readTrustedWorkerSpans(shopId, jobId, limit = 30) {
+    checkedUuid(shopId); checkedUuid(jobId)
+    if (!Number.isInteger(limit) || limit < 1 || limit > 50) throw new Error('Invalid private worker trace limit')
+    const token = await tokenProvider()
+    if (!token) throw new Error('Sign in to inspect backend worker evidence')
+    const response = await fetchImpl(url.origin + '/rest/v1/rpc/retail_feature_worker_spans', {
+      method: 'POST', redirect: 'error', cache: 'no-store',
+      headers: { apikey: publishableKey, Authorization: 'Bearer ' + token,
+        'Content-Type': 'application/json' },
+      body: JSON.stringify({ p_shop_id: shopId, p_job_id: jobId, p_limit: limit }),
+    })
+    const data = await response.json().catch(() => null)
+    if (!response.ok) {
+      const error = new Error([404, 406].includes(response.status)
+        ? 'Trusted backend worker trace RPC is not deployed in DEV.'
+        : response.status === 401 || response.status === 403
+          ? 'Backend worker evidence is not authorized for this account and business.'
+          : 'Trusted backend worker evidence cannot currently be verified.')
+      error.status = response.status
+      throw error
+    }
+    if (!data || data.shop_id !== shopId || data.job_id !== jobId ||
+      data.source !== 'trusted_backend_persisted' || !Array.isArray(data.events) ||
+      data.events.length > limit) throw new Error('Unverified backend worker trace identity')
+    const operations = {
+      'planning.complete': ['F2','SUCCEEDED'], 'planning.denied': ['F2','DENIED'],
+      'planning.failed': ['F2','FAILED'], 'planning.unconfigured': ['F2','UNCONFIGURED'],
+      'render.complete': ['F4','SUCCEEDED'], 'render.denied': ['F4','DENIED'],
+      'render.failed': ['F4','FAILED'],
+    }
+    const known = new Set()
+    for (const event of data.events) {
+      const expected = event && operations[event.operation]
+      if (!expected || event.shop_id !== shopId || event.job_id !== jobId ||
+          !UUID.test(event.id || '') || event.feature !== expected[0] ||
+          event.status !== expected[1] || !Number.isInteger(event.attempt) ||
+          event.attempt < 1 || event.attempt > 5 ||
+          !Number.isInteger(event.elapsed_ms) || event.elapsed_ms < 0 ||
+          event.elapsed_ms > 1_800_000 || !event.metadata ||
+          typeof event.metadata !== 'object' || Array.isArray(event.metadata) ||
+          known.has(event.id)) {
+        throw new Error('Backend worker span did not meet the trusted read contract')
+      }
+      known.add(event.id)
+      const required = event.operation === 'planning.complete'
+        ? ['generated_days', 'planner_mode']
+        : event.operation === 'render.complete'
+          ? ['codec', 'duration_seconds', 'video_height', 'video_width'] : []
+      const actual = Object.keys(event.metadata).sort()
+      if (JSON.stringify(actual) !== JSON.stringify(required) ||
+          (event.operation === 'planning.complete' &&
+            (event.metadata.generated_days !== 7 ||
+             !['dev_mock','foundry'].includes(event.metadata.planner_mode))) ||
+          (event.operation === 'render.complete' &&
+            (event.metadata.codec !== 'h264/aac' ||
+             event.metadata.video_width !== 1080 ||
+             event.metadata.video_height !== 1920 ||
+             !Number.isFinite(event.metadata.duration_seconds) ||
+             Math.abs(event.metadata.duration_seconds - 30) > 0.12))) {
+        throw new Error('Backend worker span did not meet the trusted read contract')
+      }
+    }
+    return data.events
+  }
   return {
+    readTrustedWorkerSpans,
     async createRun({ id, shopId, userId, prompt, mode }) {
       checkedUuid(id); checkedUuid(shopId); checkedUuid(userId)
       if (typeof prompt !== 'string' || prompt.trim().length < 10 || prompt.length > 1500 ||

diff --git a/tests/frontend/feature-testing-worker-ledger.test.mjs b/tests/frontend/feature-testing-worker-ledger.test.mjs
@@ -0,0 +1,84 @@
+import test from 'node:test'
+import assert from 'node:assert/strict'
+import {createTraceStore} from '../../frontend/src/features/testing/trace-store.mjs'
+
+const shop='11111111-1111-4111-8111-111111111111'
+const job='22222222-2222-4222-8222-222222222222'
+const sid='33333333-3333-4333-8333-333333333333'
+const row=()=>({
+  id:sid,shop_id:shop,job_id:job,feature:'F2',operation:'planning.complete',
+  status:'SUCCEEDED',attempt:1,elapsed_ms:450,metadata:{generated_days:7,planner_mode:'dev_mock'},
+  recorded_at:'2026-10-29T00:00:00Z',
+})
+const reply=()=>({source:'trusted_backend_persisted',shop_id:shop,job_id:job,events:[row()]})
+function client(fetchImpl,tokenProvider=async()=> 'user-session-jwt'){
+  return createTraceStore({supabaseUrl:'https://tenant.supabase.co',
+    publishableKey:'sb_publishable_test',tokenProvider,fetchImpl})
+}
+const http=(status,content)=>({ok:status>=200&&status<300,status,
+  json:async()=>content})
+
+test('private trusted reads use existing user JWT, not a service credential',async()=>{
+  let observed
+  const store=client(async(url,init)=>{
+    observed={url,init}
+    return http(200,reply())
+  })
+  const spans=await store.readTrustedWorkerSpans(shop,job,30)
+  assert.equal(spans.length,1)
+  assert.equal(spans[0].status,'SUCCEEDED')
+  assert.equal(observed.url,'https://tenant.supabase.co/rest/v1/rpc/retail_feature_worker_spans')
+  assert.equal(observed.init.method,'POST')
+  assert.equal(observed.init.headers.Authorization,'Bearer user-session-jwt')
+  assert.equal(observed.init.headers.apikey,'sb_publishable_test')
+  assert.deepEqual(JSON.parse(observed.init.body),{
+    p_shop_id:shop,p_job_id:job,p_limit:30,
+  })
+  assert.ok(!observed.init.url)
+  assert.ok(!JSON.stringify(observed.init).includes('service_role'))
+})
+
+test('hosted RPC absent or denied never masquerades as worker success',async()=>{
+  for(const code of [403,404,406,503]){
+    const store=client(async()=>http(code,{message:'mock backend failure'}))
+    await assert.rejects(()=>store.readTrustedWorkerSpans(shop,job),
+      /not deployed|not authorized|cannot currently be verified/i)
+  }
+})
+
+test('cross-tenant, wrong job, unknown source and bad schema responses fail closed',async()=>{
+  const mutations=[
+    {...reply(),shop_id:'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'},
+    {...reply(),job_id:'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'},
+    {...reply(),source:'browser_observed'},
+    {...reply(),events:[{...row(),job_id:'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'}]},
+    {...reply(),events:[{...row(),feature:'F5'}]},
+    {...reply(),events:[{...row(),operation:'planning.failed'}]},
+    {...reply(),events:[{...row(),status:'FAILED'}]},
+    {...reply(),events:[{...row(),attempt:0}]},
+    {...reply(),events:[{...row(),elapsed_ms:-1}]},
+    {...reply(),events:[{...row(),id:'not-a-uuid'}]},
+    {...reply(),events:[{...row(),metadata:{jwt:'private'}}]},
+  ]
+  for(const result of mutations){
+    const store=client(async()=>http(200,result))
+    await assert.rejects(()=>store.readTrustedWorkerSpans(shop,job),
+      /Unverified|trusted read contract/)
+  }
+})
+
+test('invalid scoped resource IDs and unbounded reads stop before network',async()=>{
+  let calls=0
+  const store=client(async()=>{calls++;return http(200,reply())})
+  await assert.rejects(()=>store.readTrustedWorkerSpans('bad',job))
+  await assert.rejects(()=>store.readTrustedWorkerSpans(shop,'bad'))
+  await assert.rejects(()=>store.readTrustedWorkerSpans(shop,job,51))
+  assert.equal(calls,0)
+})
+
+test('no signed user JWT stops before sending a Supabase request',async()=>{
+  let calls=0
+  const store=client(async()=>{calls++;return http(200,reply())},async()=>null)
+  await assert.rejects(()=>store.readTrustedWorkerSpans(shop,job),/Sign in/)
+  assert.equal(calls,0)
+})
```
