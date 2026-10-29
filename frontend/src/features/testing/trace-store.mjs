// Browser-observed trace receipts only. This is not a worker-level audit stream.
// PostgREST RLS checks current OWNER/EDITOR membership on every request.
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

export function createTraceStore({ supabaseUrl, publishableKey, tokenProvider, fetchImpl = fetch }) {
  if (!supabaseUrl || !publishableKey) return null
  const url = new URL(supabaseUrl)
  if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash ||
      !['', '/'].includes(url.pathname)) throw new Error('Trace storage must use a trusted HTTPS origin')
  if (typeof tokenProvider !== 'function') throw new Error('Trace storage requires a signed-in user')
  async function request(table, { method = 'GET', query = {}, body } = {}) {
    if (!['feature_test_runs', 'feature_test_events'].includes(table)) throw new Error('Unsupported trace table')
    const token = await tokenProvider()
    if (!token) throw new Error('Sign in to access private test results')
    const target = new URL(url.origin + '/rest/v1/' + table)
    for (const [key, value] of Object.entries(query)) target.searchParams.set(key, String(value))
    const response = await fetchImpl(target.toString(), {
      method, redirect: 'error', cache: 'no-store',
      headers: {
        apikey: publishableKey,
        Authorization: 'Bearer ' + token,
        ...(body === undefined ? {} : {
          'Content-Type': 'application/json',
          Prefer: 'return=representation',
        }),
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    })
    const data = await response.json().catch(() => null)
    if (!response.ok) {
      const error = new Error(response.status === 404 || response.status === 406
        ? 'Feature trace storage is not deployed in this DEV environment.'
        : response.status === 401 || response.status === 403
          ? 'Feature trace access denied for this signed-in business.'
          : 'Private feature trace could not be saved or loaded.')
      error.status = response.status
      throw error
    }
    return data
  }
  function checkedUuid(value) {
    if (!UUID.test(value || '')) throw new Error('Invalid tenant trace ID')
    return value
  }
  async function readTrustedWorkerSpans(shopId, jobId, limit = 30) {
    checkedUuid(shopId); checkedUuid(jobId)
    if (!Number.isInteger(limit) || limit < 1 || limit > 50) throw new Error('Invalid private worker trace limit')
    const token = await tokenProvider()
    if (!token) throw new Error('Sign in to inspect backend worker evidence')
    const response = await fetchImpl(url.origin + '/rest/v1/rpc/retail_feature_worker_spans', {
      method: 'POST', redirect: 'error', cache: 'no-store',
      headers: { apikey: publishableKey, Authorization: 'Bearer ' + token,
        'Content-Type': 'application/json' },
      body: JSON.stringify({ p_shop_id: shopId, p_job_id: jobId, p_limit: limit }),
    })
    const data = await response.json().catch(() => null)
    if (!response.ok) {
      const error = new Error([404, 406].includes(response.status)
        ? 'Trusted backend worker trace RPC is not deployed in DEV.'
        : response.status === 401 || response.status === 403
          ? 'Backend worker evidence is not authorized for this account and business.'
          : 'Trusted backend worker evidence cannot currently be verified.')
      error.status = response.status
      throw error
    }
    if (!data || data.shop_id !== shopId || data.job_id !== jobId ||
      data.source !== 'trusted_backend_persisted' || !Array.isArray(data.events) ||
      data.events.length > limit) throw new Error('Unverified backend worker trace identity')
    const operations = {
      'planning.complete': ['F2','SUCCEEDED'], 'planning.denied': ['F2','DENIED'],
      'planning.failed': ['F2','FAILED'], 'planning.unconfigured': ['F2','UNCONFIGURED'],
      'render.complete': ['F4','SUCCEEDED'], 'render.denied': ['F4','DENIED'],
      'render.failed': ['F4','FAILED'],
    }
    const known = new Set()
    for (const event of data.events) {
      const expected = event && operations[event.operation]
      if (!expected || event.shop_id !== shopId || event.job_id !== jobId ||
          !UUID.test(event.id || '') || event.feature !== expected[0] ||
          event.status !== expected[1] || !Number.isInteger(event.attempt) ||
          event.attempt < 1 || event.attempt > 5 ||
          !Number.isInteger(event.elapsed_ms) || event.elapsed_ms < 0 ||
          event.elapsed_ms > 1_800_000 || !event.metadata ||
          typeof event.metadata !== 'object' || Array.isArray(event.metadata) ||
          known.has(event.id)) {
        throw new Error('Backend worker span did not meet the trusted read contract')
      }
      known.add(event.id)
      const required = event.operation === 'planning.complete'
        ? ['generated_days', 'planner_mode']
        : event.operation === 'render.complete'
          ? ['codec', 'duration_seconds', 'video_height', 'video_width'] : []
      const actual = Object.keys(event.metadata).sort()
      if (JSON.stringify(actual) !== JSON.stringify(required) ||
          (event.operation === 'planning.complete' &&
            (event.metadata.generated_days !== 7 ||
             !['dev_mock','foundry'].includes(event.metadata.planner_mode))) ||
          (event.operation === 'render.complete' &&
            (event.metadata.codec !== 'h264/aac' ||
             event.metadata.video_width !== 1080 ||
             event.metadata.video_height !== 1920 ||
             !Number.isFinite(event.metadata.duration_seconds) ||
             Math.abs(event.metadata.duration_seconds - 30) > 0.12))) {
        throw new Error('Backend worker span did not meet the trusted read contract')
      }
    }
    return data.events
  }
  return {
    readTrustedWorkerSpans,
    async createRun({ id, shopId, userId, prompt, mode }) {
      checkedUuid(id); checkedUuid(shopId); checkedUuid(userId)
      if (typeof prompt !== 'string' || prompt.trim().length < 10 || prompt.length > 1500 ||
          !['prompt', 'campaign', 'campaign_reel'].includes(mode)) throw new Error('Invalid test input')
      const result = await request('feature_test_runs', {
        method: 'POST', body: {
          id, shop_id: shopId, created_by: userId, prompt: prompt.trim(), mode,
        },
      })
      if (!Array.isArray(result) || result.length !== 1 || result[0].id !== id ||
          result[0].shop_id !== shopId || result[0].created_by !== userId) {
        throw new Error('Private test creation could not be confirmed')
      }
      return result[0]
    },
    async append({ runId, shopId, userId, seq, feature, action, status, summary, details = {}, durationMs = null }) {
      checkedUuid(runId); checkedUuid(shopId); checkedUuid(userId)
      const allowed = ['PASS', 'FAIL', 'UNKNOWN', 'NOT_RUN', 'QUALITY_REVIEW']
      if (!Number.isInteger(seq) || seq < 1 || seq > 1000 || !allowed.includes(status) ||
          typeof feature !== 'string' || typeof action !== 'string' || typeof summary !== 'string' ||
          !details || Array.isArray(details) || typeof details !== 'object' ||
          JSON.stringify(details).length > 8000) throw new Error('Invalid trace receipt')
      const result = await request('feature_test_events', {
        method: 'POST', body: {
          run_id: runId, shop_id: shopId, actor_user_id: userId, event_seq: seq,
          feature, action, status, summary, details,
          duration_ms: durationMs === null ? null : Math.max(0, Math.round(durationMs)),
        },
      })
      if (!Array.isArray(result) || result.length !== 1 || result[0].run_id !== runId ||
          result[0].shop_id !== shopId || result[0].event_seq !== seq) {
        throw new Error('Trace append could not be confirmed. Do not replay this action.')
      }
      return result[0]
    },
    async listRuns(shopId) {
      checkedUuid(shopId)
      const rows = await request('feature_test_runs', { query: {
        select: 'id,shop_id,created_by,prompt,mode,created_at',
        shop_id: 'eq.' + shopId, order: 'created_at.desc', limit: 30,
      } })
      if (!Array.isArray(rows) || rows.some(row => row.shop_id !== shopId)) throw new Error('Trace history tenant mismatch')
      return rows
    },
    async listEvents(shopId, runId) {
      checkedUuid(shopId); checkedUuid(runId)
      const rows = await request('feature_test_events', { query: {
        select: 'run_id,shop_id,actor_user_id,event_seq,feature,action,status,summary,details,duration_ms,created_at',
        shop_id: 'eq.' + shopId, run_id: 'eq.' + runId, order: 'event_seq.asc', limit: 1000,
      } })
      if (!Array.isArray(rows) || rows.some(row => row.shop_id !== shopId || row.run_id !== runId)) {
        throw new Error('Trace events tenant mismatch')
      }
      return rows
    },
  }
}
