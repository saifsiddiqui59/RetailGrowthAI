import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import { createTrendApi } from '../trends/trend-api.mjs'
import { createCampaignApi } from '../campaigns/campaign-api.mjs'
import { createTraceStore } from './trace-store.mjs'
import { executeFeatureTrace } from './trace-runner.mjs'
import { summarizeTrace, compareTraceRuns, aggregateFeatureHistory } from './trace-diagnostics.mjs'
import { analyzeImprovementPriorities } from './trace-guidance.mjs'
import './testing-console.css'

const MODES = [
  { id: 'prompt', label: 'Prompt only · no campaign/render', note: 'Free deterministic Feature #2 request.' },
  { id: 'campaign', label: 'Create a live 7-day campaign', note: 'Creates a real DEV campaign and consumes available usage quota.' },
  { id: 'campaign_reel', label: 'Campaign + first-day 30s Reel', note: 'Queues a real FFmpeg job using existing DEV resources and quotas. No paid AI motion.' },
]
const FEATURES = [
  ['F1', 'Dashboard / tenant'], ['F2', 'Creative director / planner'],
  ['F3', 'Poster studio'], ['F5', 'Premium motion'],
  ['F4', 'Reel composition'], ['F7', 'Smart editor'],
]
function tomorrowInIndia() {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Kolkata', day: '2-digit', month: '2-digit', year: 'numeric',
  }).formatToParts(new Date())
  const get = name => parts.find(p => p.type === name)?.value
  return new Date(Date.UTC(+get('year'), +get('month') - 1, +get('day') + 1)).toISOString().slice(0, 10)
}
function downloadReport(run, events, workerSpans = []) {
  // User-triggered export keeps browser observations and genuine private RPC
  // worker evidence in separate arrays. A job reference is not a proven
  // run-to-job linkage or independent marketing-quality approval.
  const data = JSON.stringify({ schema: 'retailgrowth.feature-test.v1',
    browser_source: 'browser-observed-not-server-audit', run, events,
    trusted_worker_spans: workerSpans,
    worker_job_link_provenance: 'browser-observed-job-reference-only',
    suggested_improvements: analyzeImprovementPriorities(events),
  }, null, 2)
  const url = URL.createObjectURL(new Blob([data + '\n'], { type: 'application/json' }))
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = 'retailgrowth-test-' + run.id + '.json'
  anchor.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
function StageCard({ feature, title, events }) {
  const related = events.filter(e => e.feature === feature && e.status !== 'QUALITY_REVIEW')
  const status = summarizeTrace(events).features.find(item => item.id === feature)?.status || 'UNOBSERVED'
  const reviews = events.filter(e => e.feature === feature && e.status === 'QUALITY_REVIEW')
  return <section className="rgt-stage" aria-label={title}>
    <div className="rgt-stage-head">
      <strong>{feature} · {title}</strong>
      <span className={'rgt-pill rgt-' + status}>
        {status === 'UNOBSERVED' ? 'NOT OBSERVED' : status}
      </span>
    </div>
    {!related.length && <p>No authenticated receipt for this feature in this test.</p>}
    {related.map(e => <details key={e.event_seq} open={related.length === 1}>
      <summary>{e.action}: {e.summary}{e.duration_ms !== null ? ' (' + e.duration_ms + 'ms)' : ''}</summary>
      {Object.keys(e.details || {}).length > 0 && <pre>{JSON.stringify(e.details, null, 2)}</pre>}
    </details>)}
    {reviews.map(e => <p className="rgt-review" key={e.event_seq}>Human review: {e.details?.score}/5 · {e.details?.note || 'No notes'}</p>)}
  </section>
}
export default function TestingConsole() {
  const { client, user, configured } = useRetailAuth()
  const [shops, setShops] = useState([])
  const [shopId, setShopId] = useState('')
  const [assets, setAssets] = useState([])
  const [assetId, setAssetId] = useState('')
  const [prompt, setPrompt] = useState('Create a seven-day clothing boutique campaign with useful outfit tips and clear Instagram Reel ideas.')
  const [mode, setMode] = useState('prompt')
  const [startDate, setStartDate] = useState(tomorrowInIndia)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const [outcome, setOutcome] = useState('')
  const [history, setHistory] = useState([])
  const [activeRun, setActiveRun] = useState(null)
  const [events, setEvents] = useState([])
  const [workerSpans, setWorkerSpans] = useState([])
  const [workerError, setWorkerError] = useState('')
  const [workerLoading, setWorkerLoading] = useState(false)
  const selectedRunId = useRef('')
  const [baselineId, setBaselineId] = useState('')
  const [baselineEvents, setBaselineEvents] = useState([])
  const [baselineError, setBaselineError] = useState('')
  const [historyStats, setHistoryStats] = useState(null)
  const [analyzingHistory, setAnalyzingHistory] = useState(false)
  const [ratingFeature, setRatingFeature] = useState('F2')
  const [rating, setRating] = useState(3)
  const [reviewNote, setReviewNote] = useState('')
  const [savingReview, setSavingReview] = useState(false)
  const selection = useRef('')
  const busy = useRef(false)
  const networkEvidence = useRef([])
  const captureHttpReceipt = useCallback(receipt => {
    if (busy.current && networkEvidence.current.length < 80) {
      networkEvidence.current.push(receipt)
    }
  }, [])
  const apiOrigin = import.meta.env?.VITE_CAMPAIGN_API_BASE_URL
  const supabaseOrigin = import.meta.env?.VITE_SUPABASE_URL
  const pubKey = import.meta.env?.VITE_SUPABASE_PUBLISHABLE_KEY
  const store = useMemo(() => createTraceStore({
    supabaseUrl: supabaseOrigin, publishableKey: pubKey,
    tokenProvider: () => client.getAccessToken(),
  }), [client, supabaseOrigin, pubKey])
  const trendApi = useMemo(() => createTrendApi({
    baseUrl: apiOrigin, tokenProvider: () => client.getAccessToken(),
    onResponse: captureHttpReceipt,
  }), [apiOrigin, client, captureHttpReceipt])
  const campaignApi = useMemo(() => createCampaignApi({
    baseUrl: apiOrigin, tokenProvider: () => client.getAccessToken(),
    supabaseOrigin: supabaseOrigin || '', supabasePublishableKey: pubKey || '',
    onResponse: captureHttpReceipt,
  }), [apiOrigin, client, supabaseOrigin, pubKey, captureHttpReceipt])

  useEffect(() => {
    let alive = true
    if (!configured || !user) return
    client.listShops().then(rows => {
      if (!alive) return
      const writers = rows.filter(s => s.membership?.active &&
        ['OWNER', 'EDITOR'].includes(s.membership.role))
      setShops(writers)
      const nextId = writers[0]?.id || ''
      selection.current = nextId
      setShopId(nextId)
    }).catch(() => { if (alive) setError('Authorized businesses could not be loaded.') })
    return () => { alive = false }
  }, [client, configured, user?.id])

  useEffect(() => {
    let alive = true
    setHistory([]); setEvents([]); setActiveRun(null); setError(''); setOutcome('')
    selectedRunId.current = ''
    setWorkerSpans([]); setWorkerError(''); setWorkerLoading(false)
    setBaselineId(''); setBaselineEvents([]); setBaselineError('')
    setHistoryStats(null); setAnalyzingHistory(false)
    setAssets([]); setAssetId('')
    if (!shopId || !store) return () => { alive = false }
    Promise.all([store.listRuns(shopId), client.listMediaAssets(shopId)]).then(([runs, media]) => {
      if (!alive || selection.current !== shopId) return
      setHistory(runs)
      const licensed = media.filter(m => m.shop_id === shopId && m.license_name)
      setAssets(licensed)
      setAssetId(licensed[0]?.id || '')
    }).catch(() => {
      if (alive) setError('Trace schema may be awaiting DEV migration, or private history/media is unavailable.')
    })
    return () => { alive = false }
  }, [shopId, store, client])

  async function selectRun(run) {
    if (busy.current || run.shop_id !== shopId) return
    setError(''); setOutcome('')
    try {
      const loaded = await store.listEvents(shopId, run.id)
      if (selection.current !== shopId) return
      selectedRunId.current = run.id
      setActiveRun(run); setEvents(loaded)
      setWorkerSpans([]); setWorkerError('')
      setBaselineId(''); setBaselineEvents([]); setBaselineError('')
    } catch {
      setError('Unable to load private trace events for this business.')
    }
  }
  async function selectBaseline(runId) {
    setBaselineId(runId); setBaselineEvents([]); setBaselineError('')
    if (!runId || !activeRun || runId === activeRun.id) return
    const candidate = history.find(run => run.id === runId && run.shop_id === shopId)
    if (!candidate) { setBaselineError('Baseline is not available in this shop.'); return }
    try {
      const items = await store.listEvents(shopId, runId)
      if (selection.current === shopId) setBaselineEvents(items)
    } catch { setBaselineError('Baseline trace could not be loaded. No comparison is available.') }
  }
  async function inspectServerSpans() {
    if (!store || !shopId || !activeRun || busy.current || workerLoading) return
    const expectedRun = activeRun.id
    const expectedShop = shopId
    // Browser event IDs are user-observed references, not an authenticated
    // server-issued run->job link. RLS independently enforces active membership.
    const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
    const ids = [...new Set(events.flatMap(item => [
      item.feature === 'F2' ? item.details?.campaign_id : null,
      item.feature === 'F4' ? item.details?.render_job_id : null,
    ]).filter(id => typeof id === 'string' && uuid.test(id)))].slice(0, 5)
    setWorkerSpans([]); setWorkerError('')
    if (!ids.length) {
      setWorkerError('This test has no verified job ID references to inspect.')
      return
    }
    setWorkerLoading(true)
    try {
      const rows = await store.listWorkerSpans(expectedShop, ids)
      if (selection.current === expectedShop && selectedRunId.current === expectedRun) {
        setWorkerSpans(rows)
        if (!rows.length) setWorkerError('No persisted worker receipts were found for these job references. This is not proof the jobs never ran.')
      }
    } catch {
      if (selection.current === expectedShop && selectedRunId.current === expectedRun) {
        setWorkerError('Trusted span table is not released, unavailable or access is denied. Browser-only receipts remain unchanged.')
      }
    } finally { setWorkerLoading(false) }
  }
  const diagnostics = useMemo(() => summarizeTrace(events), [events])
  const improvements = useMemo(() => analyzeImprovementPriorities(events), [events])
  const rateableFeatures = useMemo(() => diagnostics.features.filter(f =>
    f.id !== 'F1' && f.status === 'PASS'), [diagnostics])
  async function analyzeHistory() {
    if (!store || !shopId || running || analyzingHistory || !history.length) return
    const scopedShop = shopId
    setAnalyzingHistory(true); setError('')
    try {
      // Deliberately capped at ten same-shop reads and no auto polling.
      const collected = []
      for (const run of history.slice(0, 10)) {
        if (selection.current !== scopedShop) return
        if (run.shop_id !== scopedShop) throw new Error('Scope mismatch')
        collected.push({run, events: await store.listEvents(scopedShop, run.id)})
      }
      if (selection.current === scopedShop) setHistoryStats({
        runs: collected.length, features: aggregateFeatureHistory(collected),
      })
    } catch { if (selection.current === scopedShop) setError('Private test summary could not be verified.') }
    finally { setAnalyzingHistory(false) }
  }
  const comparisons = useMemo(() => baselineEvents.length
    ? compareTraceRuns(events, baselineEvents) : null, [events, baselineEvents])
  async function runTest(event) {
    event.preventDefault()
    if (busy.current || !store || !trendApi || !shopId || !user) return
    if (mode !== 'prompt' && !assets.some(a => a.id === assetId && a.shop_id === shopId)) {
      setError('Select a licensed image in this business before starting a campaign.')
      return
    }
    busy.current = true
    networkEvidence.current = []
    selectedRunId.current = ''
    setWorkerSpans([]); setWorkerError('')
    setRunning(true); setError(''); setOutcome(''); setEvents([])
    setBaselineId(''); setBaselineEvents([]); setBaselineError('')
    setHistoryStats(null)
    const id = crypto.randomUUID()
    const run = { id, shop_id: shopId, created_by: user.id,
      prompt: prompt.trim(), mode, created_at: new Date().toISOString() }
    selectedRunId.current = run.id
    setActiveRun(run)
    try {
      const result = await executeFeatureTrace({
        id, shopId, userId: user.id, prompt: prompt.trim(), mode,
        assetId, startDate, client, trendApi, campaignApi, store,
        getNetworkEvidence: () => networkEvidence.current,
        onEvent: logged => {
          if (selection.current === shopId) setEvents(current =>
            [...current.filter(e => e.event_seq !== logged.event_seq), logged])
        },
      })
      setOutcome(result.status === 'PASS' ? 'Live steps verified. Review content quality separately.'
        : result.status === 'UNKNOWN'
          ? 'Execution outcome is uncertain. Inspect saved job state before another submission.'
          : 'A checked stage failed. Inspect its receipt below.')
      const runs = await store.listRuns(shopId)
      if (selection.current === shopId) setHistory(runs)
    } catch {
      // Never claim a network error means campaign/FFmpeg POST did not commit.
      setError('Trace storage or execution failed. Check saved history and Campaign Studio before retrying.')
    } finally {
      busy.current = false; setRunning(false)
    }
  }
  async function submitReview(event) {
    event.preventDefault()
    if (!activeRun || savingReview || running || activeRun.created_by !== user?.id ||
        !rateableFeatures.some(f => f.id === ratingFeature)) return
    const seq = events.reduce((n, e) => Math.max(n, e.event_seq), 0) + 1
    if (seq > 1000) return setError('Trace event limit reached.')
    setSavingReview(true); setError('')
    try {
      const logged = await store.append({
        runId: activeRun.id, shopId: activeRun.shop_id, userId: user.id, seq,
        feature: ratingFeature, action: 'human-quality-review', status: 'QUALITY_REVIEW',
        summary: 'Reviewer submitted a subjective output-quality rating.',
        details: { score: rating, note: reviewNote.trim().slice(0, 300) },
      })
      setEvents(current => [...current, logged]); setReviewNote('')
      setOutcome('Human quality rating saved. An execution PASS is not a quality PASS.')
    } catch {
      setError('Quality review save was not confirmed. Refresh the trace before retrying.')
    } finally { setSavingReview(false) }
  }
  if (!configured || !user || !store || !trendApi) return <section className="panel">
    <h1>Testing Chat</h1><p>Sign in with RetailGrowthAI DEV and configure the existing Supabase and campaign API origins to run real authenticated tests.</p>
    <Link to="/account">Open account</Link>
  </section>
  return <div className="rgt-page" aria-label="Feature testing chat">
    <div className="page-heading"><div>
      <div className="eyebrow">INTERNAL QUALITY LAB</div>
      <h1>Testing Chat &amp; Feature Trace</h1>
      <p className="lead">Run actual retailer requests, inspect each verified feature handoff, and rate output quality. No publishing or paid motion.</p>
    </div></div>
    <div className="rgt-layout">
      <aside className="panel rgt-history" aria-label="Saved test history">
        <h2>Saved test runs</h2>
        <p>Private Supabase history · up to 30 recent runs in this business.</p>
        <label>Business
          <select disabled={running} value={shopId} onChange={e => {
            selection.current = e.target.value; setShopId(e.target.value)
          }}>
            <option value="">Select a business</option>
            {shops.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </label>
        {!shops.length && <p>No active OWNER/EDITOR business is available.</p>}
        <button type="button" disabled={running || analyzingHistory || !history.length}
          onClick={analyzeHistory}>{analyzingHistory ? 'Analyzing history…' : 'Analyze last 10 tests'}</button>
        {historyStats && <div className="rgt-history-summary" aria-label="Feature-level test trends">
          <h3>Last {historyStats.runs} run(s)</h3>
          {historyStats.features.map(f => <div key={f.id}>
            <strong>{f.id} · {f.label}</strong>
            <small>PASS {f.passed} · FAIL {f.failed} · UNKNOWN {f.uncertain} · NOT RUN {f.skipped}</small>
            <small>Human quality: {f.quality_mean === null ? 'Not rated' : f.quality_mean + '/5 (' + f.quality_sample_count + ' ratings)'}</small>
          </div>)}
          <p>Only observed browser receipts; not a backend uptime or provider-quality measurement.</p>
        </div>}
        <div className="rgt-run-list">
          {history.map(run => <button key={run.id} type="button"
            className={activeRun?.id === run.id ? 'rgt-run selected' : 'rgt-run'}
            disabled={running} onClick={() => selectRun(run)}>
            <strong>{run.prompt.slice(0, 76)}</strong>
            <small>{new Date(run.created_at).toLocaleString()} · {run.mode}</small>
          </button>)}
        </div>
      </aside>
      <div className="rgt-main">
        <form className="panel rgt-chat" onSubmit={runTest}>
          <h2>Your test request</h2>
          <label>Enter a request like a real retailer
            <textarea rows={4} maxLength={1500} minLength={10} required disabled={running}
              value={prompt} onChange={e => setPrompt(e.target.value)} />
          </label>
          <div className="rgt-options">
            <label>Test depth
              <select value={mode} disabled={running} onChange={e => setMode(e.target.value)}>
                {MODES.map(m => <option key={m.id} value={m.id}>{m.label}</option>)}
              </select>
            </label>
            <label>Approved input image
              <select value={assetId} disabled={running || mode === 'prompt'}
                onChange={e => setAssetId(e.target.value)}>
                <option value="">Choose licensed media</option>
                {assets.map(a => <option key={a.id} value={a.id}>{a.id.slice(0, 8)} · {a.license_name}</option>)}
              </select>
            </label>
            <label>Campaign begins
              <input type="date" value={startDate} min={tomorrowInIndia()}
                disabled={running || mode === 'prompt'} onChange={e => setStartDate(e.target.value)} />
            </label>
          </div>
          <p>{MODES.find(m => m.id === mode)?.note}</p>
          <button className="rgt-primary" type="submit"
            disabled={running || !shopId || prompt.trim().length < 10 ||
              (mode !== 'prompt' && (!assetId || !startDate))}>
            {running ? 'Running real feature checks…' : 'Run & save feature trace'}
          </button>
          {running && <p role="status">Keep this page open while active API responses are checked. No unsafe POST retries.</p>}
          {error && <p role="alert" className="rgt-error">{error}</p>}
          {outcome && <p role="status" className="rgt-outcome">{outcome}</p>}
        </form>
        {activeRun && <div className="panel rgt-results">
          <div className="rgt-results-title"><div>
            <h2>Feature execution evidence</h2>
            <small>Run {activeRun.id} · {activeRun.mode}</small>
          </div><button type="button" disabled={running} onClick={() => downloadReport(activeRun, events, workerSpans)}>
            Export JSON
          </button></div>
          <div className="rgt-message"><strong>You</strong><p>{activeRun.prompt}</p></div>
          <p className="rgt-disclaimer">Browser-observed receipts, not backend worker spans or independent quality scores. An unobserved feature is not a success or failure.</p>
          <section className="rgt-diagnostics" aria-label="Test diagnosis">
            <h3>Root-cause starting point</h3>
            {diagnostics.first_problem
              ? <p><strong>{diagnostics.first_problem.feature} · {diagnostics.first_problem.action} ({diagnostics.first_problem.status})</strong>: {diagnostics.first_problem.summary}</p>
              : <p>{diagnostics.event_count ? 'No reported API failure. This does not establish final media quality or unobserved worker health.' : 'No stage receipts observed yet.'}</p>}
            <p>{diagnostics.reviewed_features} feature(s) have human quality ratings. A technically successful run can still need improvement.</p>
          </section>
          <section className="rgt-diagnostics" aria-label="Trusted worker evidence">
            <h3>Server-authored worker receipts</h3>
            <p>Optional private-RPC job observations, separate from browser logs. Job references came from this test's client receipts and are not independently bound to the run.</p>
            <button type="button" disabled={running || workerLoading} onClick={inspectServerSpans}>
              {workerLoading ? 'Checking worker receipts…' : 'Check server worker receipts'}
            </button>
            {workerError && <p role="status">{workerError}</p>}
            {workerSpans.map(item => <p key={item.id}>
              <strong>{item.feature} · {item.operation} · {item.status}</strong>
              {' — '}attempt {item.attempt}, {item.elapsed_ms} ms,
              job {item.job_id.slice(0, 8)}
              {item.feature === 'F4' && item.status === 'SUCCEEDED' ? ' (private FFmpeg job)' : ''}
            </p>)}
            {workerSpans.length > 0 && <p>These entries came from the service-only database table. A completed job is not an independently approved marketing output.</p>}
          </section>
          <section className="rgt-diagnostics" aria-label="What to improve next">
            <h3>What to improve next</h3>
            <p>{improvements.description}</p>
            <p>{improvements.observed_features} feature(s) returned observed work; {improvements.untested_features} were not run or not observed.</p>
            {improvements.attention.map(item => <div key={item.feature} className="rgt-guidance-item">
              <strong>{item.feature} · {item.label}</strong>
              <p>{item.category === 'LOW_HUMAN_QUALITY'
                ? 'Output quality: ' + item.latest_human_score + '/5 (human rating)'
                : item.category === 'UNCONFIRMED_RESULT'
                  ? 'Unconfirmed result — verify existing job before a new submission'
                  : 'Observed execution failure — investigate the recorded operation'}</p>
              <p>{item.reason}</p>
              <p><strong>Suggested next check:</strong> {item.recommended_action}</p>
            </div>)}
            <details>
              <summary>Review all feature assessments</summary>
              {improvements.entries.map(item => <p key={item.feature}>
                <strong>{item.feature} · {item.label}</strong> — {item.category};
                {item.completed_steps} successful browser-observed stage(s).
                {' '}{item.recommended_action}
              </p>)}
            </details>
            <p>Suggestions are based on saved browser receipts and human reviews, not automatic diagnosis of backend failures.</p>
          </section>
          <div className="rgt-stages">
            {FEATURES.map(([id, title]) => <StageCard key={id} feature={id} title={title} events={events} />)}
          </div>
          <section className="rgt-comparison" aria-label="Compare output with a past test">
            <h3>Compare with a previous run</h3>
            <label>Baseline test
              <select value={baselineId} disabled={running} onChange={e => selectBaseline(e.target.value)}>
                <option value="">No baseline selected</option>
                {history.filter(run => run.id !== activeRun.id && run.shop_id === activeRun.shop_id)
                  .map(run => <option value={run.id} key={run.id}>{run.prompt.slice(0, 70)} · {run.mode}</option>)}
              </select>
            </label>
            {baselineError && <p role="alert">{baselineError}</p>}
            {comparisons && <div className="rgt-compare-table"><table>
              <thead><tr><th>Feature</th><th>Baseline</th><th>Current</th><th>Quality change</th><th>Latency change</th></tr></thead>
              <tbody>{comparisons.map(item => <tr key={item.id}>
                <td>{item.id} · {item.label}</td><td>{item.baseline_status}</td><td>{item.status}</td>
                <td>{item.score_delta === null ? 'Not comparable' : (item.score_delta > 0 ? '+' : '') + item.score_delta + '/5'}</td>
                <td>{item.duration_delta_ms === null ? 'Not comparable' : (item.duration_delta_ms > 0 ? '+' : '') + item.duration_delta_ms + 'ms'}</td>
              </tr>)}</tbody>
            </table></div>}
            {comparisons && <p>These are browser-observed differences, not proof of a statistically significant model or worker improvement.</p>}
          </section>
          <form className="rgt-quality" onSubmit={submitReview}>
            <h3>Rate output quality</h3>
            <p>Human scores help distinguish successful execution from poor output.</p>
            <div className="rgt-options">
              <label>Feature with a completed observed output
                <select value={rateableFeatures.some(f => f.id === ratingFeature) ? ratingFeature : ''}
                  onChange={e => setRatingFeature(e.target.value)}>
                  {!rateableFeatures.some(f => f.id === ratingFeature) && <option value="">Select a completed output</option>}
                  {rateableFeatures.map(f => <option key={f.id} value={f.id}>{f.id} · {f.label}</option>)}
                </select>
              </label>
              <label>Score (1 = poor, 5 = excellent)
                <select value={rating} onChange={e => setRating(Number(e.target.value))}>
                  {[1, 2, 3, 4, 5].map(n => <option key={n} value={n}>{n}/5</option>)}
                </select>
              </label>
            </div>
            <label>What should be improved?
              <textarea rows={2} maxLength={300} value={reviewNote}
                onChange={e => setReviewNote(e.target.value)} />
            </label>
            <button type="submit" disabled={running || savingReview ||
              activeRun.created_by !== user.id || !rateableFeatures.some(f => f.id === ratingFeature)}>Save human quality review</button>
          </form>
          <p><Link to="/campaigns">Open Campaign Studio for saved campaign and private MP4 status</Link></p>
        </div>}
      </div>
    </div>
  </div>
}
