import { createRenderReadFallback } from './reel-rls-fallback.mjs'
import { collectHttpReceipt } from '../../lib/feature-http-receipt.mjs'
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

export function createCampaignApi({ baseUrl, tokenProvider, fetchImpl = fetch,
  supabaseOrigin = '', supabasePublishableKey = '', onResponse = null }) {
  if (!baseUrl || typeof baseUrl !== 'string') return null
  const parsed = new URL(baseUrl)
  if (parsed.protocol !== 'https:' || parsed.username || parsed.password ||
      parsed.search || parsed.hash || !['', '/'].includes(parsed.pathname)) {
    throw new Error('Campaign API must use an HTTPS origin')
  }
  if (typeof tokenProvider !== 'function') throw new Error('Authenticated token provider required')
  const origin = parsed.origin
  const statusFallback = createRenderReadFallback({
    supabaseOrigin, publishableKey: supabasePublishableKey,
    tokenProvider, fetchImpl,
  })
  async function withVideoReadFallback(jobId, endpoint, action) {
    const verified = uuid(jobId)
    try {
      return await request('GET', endpoint + verified)
    } catch (error) {
      // Only a transient upstream gateway 503 permits a direct tenant-JWT
      // Supabase READ fallback. Auth 401/403, 404 and other errors remain
      // denied; never replay a video-create or campaign-edit mutation.
      if (error?.status !== 503 || !statusFallback) throw error
      return statusFallback[action](verified)
    }
  }
  // Azure Flex DEV has intermittently produced pre-handler 503s after about
  // 60 seconds, even on protected GETs with no JWT. Browser callers must not
  // wait indefinitely or replay non-idempotent campaigns, edits or jobs.
  const READ_TIMEOUT_MS = 12000
  const READ_ATTEMPTS = 2
  async function request(method, path, body) {
    const token = await tokenProvider()
    if (typeof token !== 'string' || !token) throw new Error('Please sign in again')
    // Only pure reads can be re-issued. A lost acknowledgement of POST/PATCH
    // may mean the DB transaction already committed; never blindly replay it.
    const attempts = method === 'GET' ? READ_ATTEMPTS : 1
    for (let attempt = 0; attempt < attempts; attempt++) {
      const controller = method === 'GET' ? new AbortController() : null
      const timer = controller ? setTimeout(() => controller.abort(), READ_TIMEOUT_MS) : null
      let response
      const startedAt = Date.now()
      try {
        response = await fetchImpl(origin + '/api' + path, {
          method, redirect: 'error', cache: 'no-store',
          headers: {
            Authorization: 'Bearer ' + token,
            ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
          },
          ...(controller ? { signal: controller.signal } : {}),
          ...(body === undefined ? {} : { body: JSON.stringify(body) }),
        })
      } catch (error) {
        const transientNetwork = error?.name === 'AbortError' || error instanceof TypeError
        if (method === 'GET' && transientNetwork && attempt + 1 < attempts) continue
        if (method === 'GET' && transientNetwork) {
          const unavailable = new Error('Campaign service is temporarily unavailable. Try again.')
          unavailable.status = 503
          throw unavailable
        }
        throw error
      } finally {
        if (timer !== null) clearTimeout(timer)
      }
      collectHttpReceipt(onResponse, {
        source: 'campaign', method, path, response, startedAt, attempt: attempt + 1,
      })
      if (method === 'GET' && [502, 503, 504].includes(response.status) &&
          attempt + 1 < attempts) continue
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
        const error = new Error(friendly[errorCode] || errorCode ||
          (method === 'GET' && [502, 503, 504].includes(response.status)
            ? 'Campaign service is temporarily unavailable. Try again.'
            : 'Campaign API request failed'))
        error.status = response.status
        throw error
      }
      return data
    }
    throw new Error('Campaign read retry budget exhausted')
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
    getRenderJob: (jobId) => withVideoReadFallback(jobId, '/render-jobs/', 'getRenderJob'),
    getDownload: async (jobId) => {
      const id = uuid(jobId)
      try {
        return await request('GET', '/render-jobs/' + id + '/download')
      } catch (error) {
        if (error?.status !== 503 || !statusFallback) throw error
        return statusFallback.getDownload(id)
      }
    },
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
    listPosterDrafts: (campaignId, dayId) => request('GET',
      '/campaigns/' + uuid(campaignId) + '/days/' + uuid(dayId) + '/posters'),

    createPosterRender: (posterId) => request('POST',
      '/poster-drafts/' + uuid(posterId) + '/renders', {}),
    getPosterJob: (jobId) => request('GET', '/poster-jobs/' + uuid(jobId)),
    getPosterDownload: (jobId) => request('GET',
      '/poster-jobs/' + uuid(jobId) + '/download'),
    selectPosterBanner: (posterId, expectedInstagram) => {
      if (!expectedInstagram || typeof expectedInstagram !== 'object' ||
          !('banner_asset_id' in expectedInstagram)) {
        throw new Error('Load the complete saved Instagram draft before selection')
      }
      return request('POST', '/poster-drafts/' + uuid(posterId) + '/select',
        { expected_instagram: expectedInstagram })
    },
  }
}
