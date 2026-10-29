// Pure, deterministic browser-receipt analysis. NOT trusted server telemetry.
import { acceptedDimension } from './quality-rubrics.mjs'
// Every metric preserves the distinction between API execution and subjective QA.
export const FEATURE_LABELS = Object.freeze([
  ['F1', 'Tenant and rights'], ['F2', 'Creative director'],
  ['F3', 'Poster / model'], ['F5', 'Premium motion'],
  ['F4', 'Video rendering'], ['F7', 'Smart editing'],
])
const TERMINAL = new Set(['PASS', 'FAIL', 'UNKNOWN', 'NOT_RUN'])
const VALID = new Set([...TERMINAL, 'QUALITY_REVIEW'])
const finite = v => Number.isFinite(v) && v >= 0
const safeEvents = events => Array.isArray(events) ? events.filter(e =>
  e && typeof e === 'object' && VALID.has(e.status) && typeof e.feature === 'string' &&
  Number.isInteger(e.event_seq) && e.event_seq > 0).sort((a,b) => a.event_seq - b.event_seq) : []

export function summarizeTrace(events) {
  const ordered = safeEvents(events)
  const features = FEATURE_LABELS.map(([id, label]) => {
    const stageEvents = ordered.filter(e => e.feature === id && e.status !== 'QUALITY_REVIEW')
    const observed = stageEvents.filter(e => TERMINAL.has(e.status))
    const firstFailure = observed.find(e => e.status === 'FAIL' || e.status === 'UNKNOWN')
    const latest = observed.at(-1) || null
    // A prior failure must never be hidden by a later success. If an outcome
    // is UNKNOWN it stays visible even if a later step returned successfully.
    // A prompt-only F2 test emits an actual prompt PASS followed by a
    // campaign-planning NOT_RUN. The skipped optional substage must never
    // erase already completed F2 work or its QA eligibility.
    const status = firstFailure?.status ||
      (observed.some(e => e.status === 'PASS') ? 'PASS' : latest?.status || 'UNOBSERVED')
    const durations = observed.map(e => e.duration_ms).filter(finite)
    // Ignore a forged review before any observed output. Legacy reviews without
    // dimensions are 'overall'; unrecognized explicit aspects do not count.
    const ratings = []
    let completedOutputSeen = false
    for (const e of ordered) {
      if (e.feature !== id) continue
      if (e.status === 'PASS') completedOutputSeen = true
      if (e.status !== 'QUALITY_REVIEW' || !completedOutputSeen ||
          !Number.isInteger(e.details?.score) || e.details.score < 1 ||
          e.details.score > 5) continue
      const dimension = e.details?.dimension === undefined ? 'overall' : e.details.dimension
      if (!acceptedDimension(id, dimension)) continue
      ratings.push({score:e.details.score,dimension})
    }
    return {
      id, label, status, observed_steps: observed.length,
      first_problem: firstFailure ? { action: firstFailure.action,
        status: firstFailure.status, summary: firstFailure.summary } : null,
      latest_action: latest?.action || null,
      duration_ms: durations.length ? Math.max(...durations) : null,
      quality_latest: ratings.at(-1)?.score ?? null,
      quality_dimension_latest: ratings.at(-1)?.dimension ?? null,
      quality_count: ratings.length,
    }
  })
  const firstProblem = ordered.find(e => e.status === 'FAIL' || e.status === 'UNKNOWN')
  return {
    features, first_problem: firstProblem ? {
      feature: firstProblem.feature, action: firstProblem.action,
      status: firstProblem.status, summary: firstProblem.summary,
    } : null,
    // An incomplete history cannot be called PASS. Do not invent success.
    status: firstProblem?.status || (ordered.length ? 'NO_REPORTED_FAILURE' : 'UNOBSERVED'),
    event_count: ordered.length,
    reviewed_features: features.filter(f => f.quality_latest !== null).length,
  }
}

export function compareTraceRuns(current, baseline) {
  const a = summarizeTrace(current), b = summarizeTrace(baseline)
  return a.features.map(row => {
    const previous = b.features.find(x => x.id === row.id)
    // A 1/5 sound review must not compare to a 4/5 caption review.
    const sameAspect = row.quality_dimension_latest !== null &&
      row.quality_dimension_latest === previous.quality_dimension_latest
    const scoreDelta = sameAspect && row.quality_latest !== null &&
      previous.quality_latest !== null
      ? row.quality_latest - previous.quality_latest : null
    // Durations from separately sampled browser requests are informative
    // indicators only, not statistically significant performance conclusions.
    const durationDelta = row.duration_ms !== null && previous.duration_ms !== null
      ? row.duration_ms - previous.duration_ms : null
    return {
      id: row.id, label: row.label, status: row.status,
      baseline_status: previous.status, score: row.quality_latest,
      baseline_score: previous.quality_latest, score_delta: scoreDelta,
      quality_dimension: row.quality_dimension_latest,
      baseline_quality_dimension: previous.quality_dimension_latest,
      duration_delta_ms: durationDelta,
    }
  })
}

export function aggregateFeatureHistory(runsWithEvents) {
  if (!Array.isArray(runsWithEvents)) return []
  return FEATURE_LABELS.map(([id, label]) => {
    let pass = 0, fail = 0, unknown = 0, notRun = 0, observed = 0
    const durations = [], ratings = []
    for (const run of runsWithEvents) {
      const feature = summarizeTrace(run?.events).features.find(x => x.id === id)
      if (!feature) continue
      if (feature.status === 'PASS') pass++
      else if (feature.status === 'FAIL') fail++
      else if (feature.status === 'UNKNOWN') unknown++
      else if (feature.status === 'NOT_RUN') notRun++
      else continue
      observed++
      if (feature.duration_ms !== null && feature.status === 'PASS') durations.push(feature.duration_ms)
      if (feature.quality_latest !== null) ratings.push(feature.quality_latest)
    }
    durations.sort((a,b) => a - b)
    return { id, label, tested_runs: observed, passed: pass,
      failed: fail, uncertain: unknown, skipped: notRun,
      p95_ms: durations.length ? durations[Math.ceil(durations.length * 0.95) - 1] : null,
      quality_mean: ratings.length ? Math.round(10 * ratings.reduce((a,b)=>a+b,0) / ratings.length)/10 : null,
      quality_sample_count: ratings.length }
  })
}
