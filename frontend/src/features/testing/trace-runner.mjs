// Uses live existing RetailGrowthAI APIs; never claims to execute stages without a receipt.
// Browser-observed receipts are distinct from backend/worker-level spans.
const ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
export const TRACE_STAGES = [
  ['F1', 'Tenant / licensed media'],
  ['F2', 'Prompt improvement'],
  ['F2', 'Campaign planning'],
  ['F3', 'Poster / model studio'],
  ['F5', 'Premium AI motion'],
  ['F4', 'FFmpeg Reel worker'],
  ['F7', 'Smart video editor'],
]
const delay = ms => new Promise(resolve => setTimeout(resolve, ms))
const elapsed = start => Date.now() - start
function requireShop(value, shopId) {
  if (!value || value.shop_id !== shopId) throw new Error('Cross-shop or missing API response')
  return value
}
function errorText(error) {
  // No URLs, bearer tokens, upstream stack traces or request bodies in receipts.
  if (error?.status === 401) return 'Session expired (401)'
  if (error?.status === 403) return 'Authorization denied (403)'
  if (error?.status === 404) return 'Resource unavailable or denied (404)'
  if (error?.status === 503) return 'API unavailable (503); Azure #249 may affect this request'
  return 'Request could not be verified; inspect the authorized application status'
}
function excerpt(text, max = 1200) {
  return typeof text === 'string' ? text.slice(0, max) : ''
}
export async function executeFeatureTrace({
  id, shopId, userId, prompt, mode, assetId, startDate,
  client, trendApi, campaignApi, store, onEvent = () => {},
  getNetworkEvidence = () => [],
  sleep = delay, maxPolls = 15,
}) {
  if (!ID.test(id) || !ID.test(shopId) || !ID.test(userId) ||
      typeof prompt !== 'string' || prompt.trim().length < 10 || prompt.length > 1500 ||
      !['prompt', 'campaign', 'campaign_reel'].includes(mode)) {
    throw new Error('Choose a signed-in business and a valid testing brief')
  }
  if (!store || !trendApi) throw new Error('Live authenticated feature tracing is not configured')
  // A rejected first write means no test begins; never generate an unlogged result.
  await store.createRun({ id, shopId, userId, prompt, mode })
  let seq = 0
  let seenTransport = 0
  const log = async (feature, action, status, summary, details = {}, durationMs = null) => {
    const all = getNetworkEvidence()
    const receipts = Array.isArray(all) ? all.slice(seenTransport, seenTransport + 8) : []
    seenTransport = Array.isArray(all) ? all.length : seenTransport
    // Keep only sanitized, known fields returned by the existing HTTP clients.
    // Response marker absent is an observation, never a proven Azure root cause.
    const safeReceipts = receipts.map(r => ({
      source: r.source, operation: r.operation, method: r.method,
      status_code: r.status_code, request_id: r.request_id,
      handler_marker_seen: r.handler_marker_seen,
      elapsed_ms: r.elapsed_ms, attempt: r.attempt,
    }))
    const persistedDetails = safeReceipts.length
      ? { ...details, http_receipts: safeReceipts } : details
    const event = await store.append({
      runId: id, shopId, userId, seq: ++seq, feature, action, status, summary,
      details: persistedDetails, durationMs,
    })
    onEvent(event)
    return event
  }
  let media
  let improved
  let draft
  let campaignId
  const started = Date.now()
  try {
    const shops = await client.listShops()
    const selected = shops.find(s => s.id === shopId && s.membership?.active &&
      ['OWNER', 'EDITOR'].includes(s.membership.role))
    if (!selected) throw new Error('No active writer membership')
    media = await client.listMediaAssets(shopId)
    if (mode !== 'prompt' && (!ID.test(assetId || '') ||
        !media.some(a => a.id === assetId && a.shop_id === shopId && a.license_name))) {
      throw new Error('No authorized registered media for campaign run')
    }
    await log('F1', 'tenant-and-rights', 'PASS',
      'Signed-in OWNER/EDITOR shop and registered licensed-media metadata verified.',
      { shop_name: excerpt(selected.name, 100), role: selected.membership.role,
        licensed_media_count: media.length, selected_media_id: mode === 'prompt' ? null : assetId },
      elapsed(started))
  } catch (error) {
    await log('F1', 'tenant-and-rights', 'FAIL',
      'Current role or registered media could not be verified.', { reason: errorText(error) }, elapsed(started))
    return { id, status: 'FAIL', feature: 'F1' }
  }
  const improveStart = Date.now()
  try {
    improved = requireShop(await trendApi.improvePrompt(shopId, prompt,
      ['instagram_caption', 'linkedin_post', 'poster_brief', 'reel_storyboard'], 'en-IN'), shopId)
    if (improved.original_prompt !== prompt || improved.provider_mode !== 'deterministic' ||
        improved.review_status !== 'NEEDS_REVIEW' || improved.can_publish !== false ||
        improved.usage?.paid_inference_calls !== 0 ||
        !excerpt(improved.improved_prompt).trim()) {
      throw new Error('Invalid deterministic prompt receipt')
    }
    await log('F2', 'prompt-improvement', 'PASS',
      'Existing Feature #2 deterministic prompt improvement returned a review-only result.',
      { provider_mode: improved.provider_mode,
        improved_prompt: excerpt(improved.improved_prompt, 1500),
        suggestions: Array.isArray(improved.improvement_suggestions)
          ? improved.improvement_suggestions.slice(0, 5).map(s => excerpt(String(s), 180)) : [],
        paid_inference_calls: 0 }, elapsed(improveStart))
  } catch (error) {
    await log('F2', 'prompt-improvement', 'FAIL',
      'Prompt improvement did not return a valid shop-scoped result.',
      { reason: errorText(error) }, elapsed(improveStart))
    return { id, status: 'FAIL', feature: 'F2' }
  }
  if (mode === 'prompt') {
    await log('F2', 'campaign-planning', 'NOT_RUN', 'Prompt-only test: no campaign was submitted.')
    await log('F3', 'poster-model', 'NOT_RUN', 'Poster/model generation is not invoked by this test.')
    await log('F5', 'premium-motion', 'NOT_RUN', 'Paid AI motion/provider calls remain disabled.')
    await log('F4', 'ffmpeg-reel', 'NOT_RUN', 'No Reel was queued in prompt-only mode.')
    await log('F7', 'smart-editor', 'NOT_RUN', 'Feature #7 has no verified runtime receipt in this test.')
    return { id, status: 'PASS', feature: 'F2' }
  }
  if (!campaignApi) {
    await log('F2', 'campaign-planning', 'FAIL', 'Campaign API not configured.')
    return { id, status: 'FAIL', feature: 'F2' }
  }
  const planStart = Date.now()
  try {
    // One non-idempotent POST ONLY. On failure, actual server outcome may be unknown.
    const receipt = await campaignApi.createCampaign({
      shop_id: shopId, brief: improved.improved_prompt, duration_days: 7,
      start_date: startDate, timezone: 'Asia/Kolkata', language: 'en-IN',
      platforms: ['linkedin', 'instagram'], media_asset_ids: [assetId], offer: null,
    })
    if (receipt?.status !== 'PLANNING' || !ID.test(receipt.campaign_id || '')) {
      throw new Error('Campaign creation acknowledgement unverified')
    }
    campaignId = receipt.campaign_id
    await log('F2', 'campaign-submission', 'PASS',
      'Existing campaign API acknowledged one seven-day planning job.',
      { campaign_id: campaignId, initial_status: 'PLANNING', media_asset_id: assetId },
      elapsed(planStart))
  } catch (error) {
    await log('F2', 'campaign-submission', 'UNKNOWN',
      'Campaign POST may have committed. Do not resend automatically; inspect Campaign Studio.',
      { reason: errorText(error), automatic_retry: false }, elapsed(planStart))
    return { id, status: 'UNKNOWN', feature: 'F2' }
  }
  const pollStart = Date.now()
  try {
    for (let attempt = 0; attempt < maxPolls; attempt++) {
      const result = requireShop(await campaignApi.getCampaign(campaignId), shopId)
      if (result.id !== campaignId) throw new Error('Unexpected campaign identity')
      if (result.status === 'DRAFT') {
        if (!Array.isArray(result.days) || result.days.length !== 7 ||
            result.duration_days !== undefined && result.duration_days !== 7) {
          throw new Error('Incomplete seven-day planning output')
        }
        const days = [...result.days].sort((a, b) => a.day_index - b.day_index)
        if (days.some((day, index) => !ID.test(day.id || '') ||
             day.day_index !== index + 1 || day.shop_id !== shopId ||
             day.campaign_id !== campaignId ||
             typeof day.topic !== 'string' ||
             typeof day.linkedin?.post_text !== 'string' ||
             typeof day.instagram?.caption !== 'string' ||
             !Array.isArray(day.instagram?.reel?.storyboard)) ||
            new Set(days.map(day => day.id)).size !== 7) {
          throw new Error('Planning days failed identity or output contract verification')
        }
        draft = days[0]
        await log('F2', 'campaign-planning', 'PASS',
          'Seven complete tenant-scoped campaign days returned by authenticated planner.',
          { campaign_id: campaignId, generated_days: days.length, first_day_id: draft.id },
          elapsed(pollStart))
        // Store each real day as its own bounded, private trace receipt. This is
        // selected API output, not a model-internal step or publishing approval.
        for (const day of days) {
          await log('F2', 'campaign-day-' + day.day_index, 'PASS',
            'Saved daily copy and storyboard returned by the campaign API.',
            { campaign_id: campaignId, day_id: day.id, day_index: day.day_index,
              scheduled_date: excerpt(day.scheduled_date, 32),
              topic: excerpt(day.topic, 250),
              linkedin_post: excerpt(day.linkedin.post_text, 1200),
              instagram_caption: excerpt(day.instagram.caption, 1200),
              storyboard: day.instagram.reel.storyboard.slice(0, 12).map(scene => ({
                asset_id: ID.test(scene?.asset_id || '') ? scene.asset_id : null,
                start_seconds: Number.isFinite(scene?.start_seconds) ? scene.start_seconds : null,
                duration_seconds: Number.isFinite(scene?.duration_seconds) ? scene.duration_seconds : null,
                overlay_text: excerpt(scene?.overlay_text, 120),
              })),
              storyboard_total_scenes: day.instagram.reel.storyboard.length,
            })
        }
        break
      }
      if (result.status === 'FAILED') {
        await log('F2', 'campaign-planning', 'FAIL',
          'Authenticated campaign planner returned FAILED.',
          { campaign_id: campaignId }, elapsed(pollStart))
        return { id, status: 'FAIL', feature: 'F2', campaignId }
      }
      if (result.status !== 'PLANNING') throw new Error('Unrecognized planning state')
      if (attempt + 1 < maxPolls) await sleep(3000)
    }
    if (!draft) {
      await log('F2', 'campaign-planning', 'UNKNOWN',
        'Planning is still pending or was not observed within the bounded polling window.',
        { campaign_id: campaignId, follow_up: 'Open Campaign Studio to inspect current state.' },
        elapsed(pollStart))
      return { id, status: 'UNKNOWN', feature: 'F2', campaignId }
    }
  } catch (error) {
    await log('F2', 'campaign-planning', 'UNKNOWN',
      'Draft read-back failed; campaign outcome cannot be assumed.',
      { campaign_id: campaignId, reason: errorText(error) }, elapsed(pollStart))
    return { id, status: 'UNKNOWN', feature: 'F2', campaignId }
  }
  await log('F3', 'poster-model', 'NOT_RUN',
    'Feature #3 poster/model inference is not invoked by the Part 1 campaign planner.')
  await log('F5', 'premium-motion', 'NOT_RUN',
    'Feature #5 paid motion provider was not authorized or invoked.')
  if (mode !== 'campaign_reel') {
    await log('F4', 'ffmpeg-reel', 'NOT_RUN', 'No FFmpeg Reel requested in campaign-only mode.')
    await log('F7', 'smart-editor', 'NOT_RUN', 'Feature #7 editor not connected to this path.')
    return { id, status: 'PASS', feature: 'F2', campaignId }
  }
  let jobId
  const renderStart = Date.now()
  try {
    const receipt = await campaignApi.createRender(campaignId, draft.id)
    jobId = receipt?.job_id
    if (!ID.test(jobId || '') || !['QUEUED', 'RUNNING', 'SUCCEEDED'].includes(receipt.status)) {
      throw new Error('Unverified FFmpeg job creation')
    }
    await log('F4', 'ffmpeg-submission', 'PASS',
      'Part 1 FFmpeg 30-second Reel job acknowledged (not full Feature #4 compositor).',
      { campaign_id: campaignId, day_id: draft.id, render_job_id: jobId, status: receipt.status },
      elapsed(renderStart))
  } catch (error) {
    await log('F4', 'ffmpeg-submission', 'UNKNOWN',
      'Render POST may have committed; no automatic retry.',
      { campaign_id: campaignId, reason: errorText(error), automatic_retry: false }, elapsed(renderStart))
    return { id, status: 'UNKNOWN', feature: 'F4', campaignId }
  }
  try {
    for (let attempt = 0; attempt < maxPolls; attempt++) {
      const job = requireShop(await campaignApi.getRenderJob(jobId), shopId)
      if (job.job_id !== jobId && job.id !== jobId) throw new Error('Render job identity mismatch')
      if (job.status === 'SUCCEEDED' || job.status === 'FAILED') {
        await log('F4', 'ffmpeg-result', job.status === 'SUCCEEDED' ? 'PASS' : 'FAIL',
          job.status === 'SUCCEEDED'
            ? 'Private FFmpeg job reports success. Visual/audio quality still needs human review.'
            : 'FFmpeg worker reported FAILED.',
          { render_job_id: jobId, status: job.status,
            output_asset_id: job.output_asset_id || null, error_code: excerpt(job.error_code, 80) },
          elapsed(renderStart))
        await log('F7', 'smart-editor', 'NOT_RUN',
          'Feature #7 smart editor was not part of the verified Part 1 FFmpeg path.')
        return { id, status: job.status === 'SUCCEEDED' ? 'PASS' : 'FAIL',
          feature: 'F4', campaignId, jobId }
      }
      if (!['QUEUED', 'RUNNING'].includes(job.status)) throw new Error('Unknown render state')
      if (attempt + 1 < maxPolls) await sleep(3000)
    }
    await log('F4', 'ffmpeg-result', 'UNKNOWN',
      'Reel job is not terminal within test window. Check the saved private render status.',
      { render_job_id: jobId }, elapsed(renderStart))
  } catch (error) {
    await log('F4', 'ffmpeg-result', 'UNKNOWN',
      'Could not verify FFmpeg output; do not treat HTTP failure as a failed job.',
      { render_job_id: jobId, reason: errorText(error) }, elapsed(renderStart))
  }
  await log('F7', 'smart-editor', 'NOT_RUN',
    'No live Feature #7 editor receipt in this test.')
  return { id, status: 'UNKNOWN', feature: 'F4', campaignId, jobId }
}
