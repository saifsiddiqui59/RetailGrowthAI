// Part 3 additive UI model: FFmpeg stays the default, premium unavailable.
// Frontend capability toggles NEVER grant entitlement or allow a paid API call.
// A server-owned permission and dedicated authenticated endpoint are also needed.
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
export const DEFAULT_VIDEO_ENGINE = 'ffmpeg'
export const PREMIUM_VIDEO_STATUS = 'AWAITING_PROVIDER_AND_CREDIT_APPROVAL'

export function premiumVideoChoices({ entitlement = false, endpointReady = false,
                                     featureEnabled = false } = {}) {
  const premiumAvailable = entitlement === true && endpointReady === true && featureEnabled === true
  return [
    { id: 'ffmpeg', label: 'Standard FFmpeg Reel', available: true, cost: 'Included in existing render quota' },
    { id: 'wan', label: 'Premium Wan AI video', available: premiumAvailable,
      cost: 'Premium credits · requires a confirmed server quote' },
  ]
}

export function validatePremiumRequest(input, { entitlement = false,
                                        endpointReady = false, featureEnabled = false } = {}) {
  if (!input || typeof input !== 'object' ||
      !premiumVideoChoices({ entitlement, endpointReady, featureEnabled })[1].available) {
    throw new Error('Premium video is not activated for this business')
  }
  const { day_id, mode, resolution, duration_seconds, input_asset_id } = input
  if (!UUID.test(day_id || '') || !['text','image'].includes(mode) ||
      !['720P','1080P'].includes(resolution) ||
      !Number.isInteger(duration_seconds) || duration_seconds < 2 || duration_seconds > 15 ||
      (mode === 'image' && !UUID.test(input_asset_id || '')) ||
      (mode === 'text' && input_asset_id !== null)) {
    throw new Error('Invalid premium video options')
  }
  return { day_id, mode, resolution, duration_seconds, input_asset_id }
}
