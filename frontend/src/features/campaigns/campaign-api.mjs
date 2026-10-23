// Browser-only authenticated API gateway; never sends service keys or synthetic media IDs.
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

function uuid(value) {
  if (typeof value !== 'string' || !UUID.test(value)) throw new Error('Invalid resource ID')
  return value
}

export function validateSignedVideoUrl(url, supabaseOrigin) {
  const parsed = new URL(url)
  const trusted = new URL(supabaseOrigin)
  if (parsed.protocol !== 'https:' || parsed.origin !== trusted.origin ||
      !parsed.pathname.startsWith('/storage/v1/object/sign/retailgrowth-media/') ||
      !parsed.searchParams.has('token')) {
    throw new Error('The signed download did not come from RetailGrowthAI private storage')
  }
  return parsed.toString()
}

export function createCampaignApi({ baseUrl, tokenProvider, fetchImpl = fetch }) {
  if (!baseUrl || typeof baseUrl !== 'string') return null
  const parsed = new URL(baseUrl)
  if (parsed.protocol !== 'https:' || parsed.username || parsed.password ||
      parsed.search || parsed.hash || !['', '/'].includes(parsed.pathname)) {
    throw new Error('Campaign API must use an HTTPS origin')
  }
  if (typeof tokenProvider !== 'function') throw new Error('Authenticated token provider required')
  const origin = parsed.origin
  async function request(method, path, body) {
    const token = await tokenProvider()
    if (typeof token !== 'string' || !token) throw new Error('Please sign in again')
    const response = await fetchImpl(origin + '/api' + path, {
      method, redirect: 'error', cache: 'no-store',
      headers: {
        Authorization: 'Bearer ' + token,
        ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    })
    const data = await response.json().catch(() => null)
    if (response.status === 401) {
      const error = new Error('Session expired. Please sign in again from Account.')
      error.status = 401
      throw error
    }
    if (!response.ok) {
      const errorCode = data?.error
      const friendly = {
        QUOTA_EXCEEDED: 'This business has reached its current campaign or render limit. Existing drafts are still available.',
        SUBSCRIPTION_REQUIRED: 'This business’s trial or subscription has expired or is inactive. Existing drafts remain available.',
      }
      const error = new Error(friendly[errorCode] || errorCode || 'Campaign API request failed')
      error.status = response.status
      throw error
    }
    return data
  }
  return {
    createCampaign: (payload) => request('POST', '/campaigns', payload),
    getCampaign: (campaignId) => request('GET', '/campaigns/' + uuid(campaignId)),
    saveDay: (campaignId, dayId, day) => {
      if (!day || typeof day !== 'object') throw new Error('A complete draft day is required')
      return request('PATCH', '/campaigns/' + uuid(campaignId) + '/days/' + uuid(dayId), {
        topic: day.topic,
        linkedin: day.linkedin,
        instagram: day.instagram,
      })
    },
    createRender: (campaignId, dayId) => request('POST',
      '/campaigns/' + uuid(campaignId) + '/renders',
      { day_id: uuid(dayId), preset: 'instagram_reel_30s' }),
    getRenderJob: (jobId) => request('GET', '/render-jobs/' + uuid(jobId)),
    getDownload: (jobId) => request('GET', '/render-jobs/' + uuid(jobId) + '/download'),
    createPosterDraft: (campaignId, config) => {
      if (!config || typeof config !== 'object') throw new Error('Poster configuration is required')
      return request('POST', '/campaigns/' + uuid(campaignId) + '/posters', {
        day_id: uuid(config.day_id),
        source_asset_id: uuid(config.source_asset_id),
        logo_asset_id: config.logo_asset_id ? uuid(config.logo_asset_id) : null,
        template: config.template,
        format: config.format,
        business_name: config.business_name,
        accent_color: config.accent_color,
        background_color: config.background_color,
        offer_text: config.offer_text ?? null,
      })
    },
    getPosterDraft: (posterId) => request('GET', '/poster-drafts/' + uuid(posterId)),
  }
}
