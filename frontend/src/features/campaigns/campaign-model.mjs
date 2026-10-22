// Pure campaign editor utilities. No auth, persistence or rendering occurs here.
export const REEL_SECONDS = 30
export const CAMPAIGN_DAYS = 7
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

export function cloneCampaign(campaign) {
  return JSON.parse(JSON.stringify(campaign))
}

export function isValidDate(value) {
  if (!ISO_DATE.test(value || '')) return false
  const date = new Date(value + 'T00:00:00Z')
  return !Number.isNaN(date.valueOf()) && date.toISOString().slice(0, 10) === value
}

export function buildCampaignRequest({ brief, start_date, offer_description = '', offer_valid_until = '' }, sample) {
  const cleanedBrief = String(brief || '').trim()
  if (cleanedBrief.length < 10 || cleanedBrief.length > 2000) {
    throw new Error('Describe your campaign in 10–2,000 characters.')
  }
  if (!isValidDate(start_date)) throw new Error('Choose a valid campaign start date.')
  const description = String(offer_description || '').trim()
  if (description && !isValidDate(offer_valid_until)) {
    throw new Error('Provide a valid offer expiry date, or remove the offer.')
  }
  if (!description && offer_valid_until) {
    throw new Error('Add an offer description or remove its expiry date.')
  }
  if (description && offer_valid_until < start_date) {
    throw new Error('Offer expiry must not be before the campaign starts.')
  }
  // Fixture UUIDs are synthetic; do not pass them as supposedly authorized uploads.
  return {
    shop_id: sample.shop_id,
    brief: cleanedBrief,
    duration_days: CAMPAIGN_DAYS,
    start_date,
    timezone: 'Asia/Kolkata',
    language: 'en-IN',
    platforms: ['linkedin', 'instagram'],
    media_asset_ids: [],
    offer: description ? { description, valid_until: offer_valid_until } : null,
  }
}

export function timelineErrors(storyboard) {
  if (!Array.isArray(storyboard) || storyboard.length === 0) return ['Add at least one scene.']
  const errors = []
  let nextStart = 0
  for (const [index, scene] of storyboard.entries()) {
    if (!Number.isInteger(scene.start_seconds) || scene.start_seconds !== nextStart) {
      errors.push('Scene ' + (index + 1) + ' must start at ' + nextStart + 's.')
    }
    if (!Number.isInteger(scene.duration_seconds) || scene.duration_seconds < 1) {
      errors.push('Scene ' + (index + 1) + ' needs a positive whole-second duration.')
    }
    if (!UUID.test(scene.asset_id || '')) errors.push('Scene ' + (index + 1) + ' needs a valid asset ID.')
    if (!String(scene.overlay_text || '').trim()) errors.push('Scene ' + (index + 1) + ' needs overlay text.')
    if (!Number.isInteger(scene.duration_seconds) || scene.duration_seconds < 1) break
    nextStart += scene.duration_seconds
  }
  if (nextStart !== REEL_SECONDS) errors.push('Scenes must total exactly 30 seconds (currently ' + nextStart + 's).')
  return errors
}

export function updateScene(storyboard, sceneIndex, field, value) {
  if (!['duration_seconds', 'overlay_text'].includes(field)) throw new Error('Unsupported scene field.')
  if (sceneIndex < 0 || sceneIndex >= storyboard.length) throw new Error('Scene does not exist.')
  const updated = storyboard.map((scene, index) => index === sceneIndex
    ? { ...scene, [field]: field === 'duration_seconds' ? Number(value) : String(value) }
    : { ...scene })
  let start = 0
  return updated.map((scene) => {
    const result = { ...scene, start_seconds: start }
    start += Number.isFinite(scene.duration_seconds) ? scene.duration_seconds : 0
    return result
  })
}

export function updateCampaignDay(campaign, dayId, update) {
  if (!campaign.days.some(day => day.id === dayId)) throw new Error('Unknown campaign day.')
  return { ...campaign, days: campaign.days.map(day => day.id === dayId ? update(day) : day) }
}

export function formatDayDate(date) {
  if (!isValidDate(date)) return date
  return new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', weekday: 'short', timeZone: 'UTC' })
    .format(new Date(date + 'T12:00:00Z'))
}

export function linkedInText(day) {
  return [day.linkedin.post_text.trim(), day.linkedin.hashtags.join(' ')].filter(Boolean).join('\n\n') + '\n'
}

export function serializeDraftDay(day) {
  const errors = timelineErrors(day.instagram.reel.storyboard)
  if (errors.length) throw new Error('Fix the storyboard before exporting: ' + errors.join(' '))
  return JSON.stringify(day, null, 2) + '\n'
}
