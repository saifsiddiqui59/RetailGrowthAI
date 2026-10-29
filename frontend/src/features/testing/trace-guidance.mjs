// Evidence-based QA triage; NEVER a model-generated root cause or proof of
// unobserved worker execution. This reads only private browser-observed trace
// events and human reviews, not the authoritative worker ledger.
import { FEATURE_LABELS, summarizeTrace } from './trace-diagnostics.mjs'

const ACTIONS = Object.freeze({
  F1: Object.freeze({
    failed: 'Recheck active OWNER/EDITOR membership and separately authorized media rights before testing this shop.',
    unknown: 'Refresh signed-in tenant state; do not infer authorization from an incomplete response.',
    quality: 'Recheck the retailer context and media suitability with the owner.',
    review: 'Confirm the correct business and media rights before accepting the output.',
  }),
  F2: Object.freeze({
    failed: 'Inspect the exact saved prompt or campaign operation, current campaign state and Feature #2 validation; correct the first failed handoff.',
    unknown: 'Read the saved campaign status and request ID before any new submission. An uncertain POST may already have committed.',
    quality: 'Improve Feature #2 copy, brand fidelity, verified offer claims and storyboard; regenerate only after separate retailer approval.',
    review: 'Review the actual caption, LinkedIn copy and seven-day storyboard before accepting creative quality.',
  }),
  F3: Object.freeze({
    failed: 'Inspect authorized garment/model input and real poster job state; verify private pixels and rights before another job.',
    unknown: 'Verify the existing private poster job and its rights receipt; avoid resubmitting an uncertain generation.',
    quality: 'Review garment identity, human anatomy, typography and visual fidelity against the licensed input.',
    review: 'Review product likeness, source provenance and usable poster quality against the approved input.',
  }),
  F4: Object.freeze({
    failed: 'Inspect the saved FFmpeg job, input manifest and codec result; do not treat the Part 1 renderer as the full professional editor.',
    unknown: 'Check the saved Reel job and private output status before resubmitting; an HTTP timeout does not prove FFmpeg failed.',
    quality: 'Review scene pacing, 1080x1920 frame, transitions, soundtrack and actual licensed video against the brief.',
    review: 'Play the private Reel and rate pacing, audio, captions, encoding and visual polish.',
  }),
  F5: Object.freeze({
    failed: 'Review the real authorized provider request, budget and image-to-video motion result before considering a retry.',
    unknown: 'Reconcile provider usage and job ID before any paid motion retry; spend may have occurred.',
    quality: 'Review temporal coherence, garment continuity, faces, anatomy and motion artifacts.',
    review: 'Compare actual AI motion to the approved storyboard and cost/rights constraints.',
  }),
  F7: Object.freeze({
    failed: 'Inspect the real editor operation, input lineage and private output instead of assuming an automatic edit succeeded.',
    unknown: 'Check the existing edit job before repeating any potentially non-idempotent operation.',
    quality: 'Review cuts, transitions, subtitles, dialogue alignment and the exported final video.',
    review: 'Inspect editing decisions and exported video for timing and narrative coherence.',
  }),
})

const ALLOWED = new Set(['PASS', 'FAIL', 'UNKNOWN', 'NOT_RUN', 'QUALITY_REVIEW'])
const text = v => typeof v === 'string' ? v.slice(0, 120) : ''
const ordered = events => Array.isArray(events) ? events.filter(e =>
  e && typeof e === 'object' && ALLOWED.has(e.status) &&
  Number.isInteger(e.event_seq) && e.event_seq > 0 &&
  FEATURE_LABELS.some(([id]) => id === e.feature)).sort((a,b) => a.event_seq - b.event_seq) : []

export function analyzeImprovementPriorities(events) {
  const normalized = ordered(events)
  const report = summarizeTrace(normalized)
  const entries = report.features.map(feature => {
    const relevant = normalized.filter(e => e.feature === feature.id && e.status !== 'QUALITY_REVIEW')
    const successful = relevant.filter(e => e.status === 'PASS')
    const firstIssue = relevant.find(e => e.status === 'FAIL' || e.status === 'UNKNOWN')
    const rubric = ACTIONS[feature.id]
    // A reviewer cannot establish output quality for an absent feature.
    const score = successful.length ? feature.quality_latest : null
    const lowQuality = score !== null && score <= 2
    let reason, action, category, priority
    if (firstIssue?.status === 'FAIL') {
      reason = 'A stage reported failure. Its stored summary is evidence, not a verified root cause.'
      action = rubric.failed
      category = 'EXECUTION_FAILURE'
      priority = 0
    } else if (firstIssue?.status === 'UNKNOWN') {
      reason = 'An operation or read-back is uncertain. Do not repeat non-idempotent requests.'
      action = rubric.unknown
      category = 'UNCONFIRMED_RESULT'
      priority = 1
    } else if (lowQuality && successful.length) {
      reason = 'The execution returned an output, but a reviewer rated its quality ' + score + '/5.'
      action = rubric.quality
      category = 'LOW_HUMAN_QUALITY'
      priority = 2
    } else if (feature.status === 'PASS') {
      reason = score === null
        ? 'Observed API stage(s) passed, but this feature has no human quality review.'
        : 'Observed API stage(s) passed and the latest human rating was ' + score + '/5.'
      action = score === null ? rubric.review : 'Keep this as a comparison baseline; do not infer model-worker health from browser data alone.'
      category = score === null ? 'AWAITING_QUALITY_REVIEW' : 'REVIEWED_OUTPUT'
      priority = 3
    } else {
      reason = feature.status === 'NOT_RUN'
        ? 'This testing mode explicitly did not execute this feature.'
        : 'No authenticated stage receipt was observed for this feature.'
      action = 'Use an authorized feature-specific test after its real integration is available; do not count an unrun feature as failed or passed.'
      category = feature.status === 'NOT_RUN' ? 'NOT_RUN' : 'UNOBSERVED'
      priority = 4
    }
    const issue = firstIssue ? {action: text(firstIssue.action),
      status: firstIssue.status, summary: text(firstIssue.summary)} : null
    return Object.freeze({
      feature: feature.id, label: feature.label,
      category, priority, status: feature.status,
      completed_steps: successful.length,
      latest_human_score: score,
      first_problem: issue, reason, recommended_action: action,
      // A model/provider call is never inferred from browser stage labels.
      evidence_type: 'browser_observed_and_human_review',
    })
  })
  // Keep the earliest observed failing or uncertain operation as the starting
  // point, then surface independent low-quality outputs even if APIs passed.
  const urgent = entries.filter(e => e.priority <= 2).sort((a,b) =>
    a.priority - b.priority || FEATURE_LABELS.findIndex(([id])=>id===a.feature) -
      FEATURE_LABELS.findIndex(([id])=>id===b.feature))
  const observed = entries.filter(e => e.completed_steps > 0).length
  const untested = entries.filter(e => e.category === 'NOT_RUN' || e.category === 'UNOBSERVED').length
  return Object.freeze({
    entries, attention: urgent,
    first_problem: report.first_problem,
    observed_features: observed, untested_features: untested,
    description: urgent.length
      ? 'Start with the listed observed execution or human-quality problems. These are investigation leads, not independently proven causes.'
      : 'No observed execution problem or low human rating in this trace. Review actual outputs and test unobserved features separately.',
  })
}
