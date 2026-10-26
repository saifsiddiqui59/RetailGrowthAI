// Feature #2 v1: authenticated-only HTTP client. No service keys or cached JWT.
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

export function createTrendApi({ baseUrl, tokenProvider, fetchImpl = fetch }) {
  if (!baseUrl) return null
  const endpoint = new URL(baseUrl)
  if (endpoint.protocol !== 'https:' || endpoint.username || endpoint.password ||
      endpoint.search || endpoint.hash || !['', '/'].includes(endpoint.pathname)) {
    throw new Error('Trend API must use an HTTPS origin')
  }
  if (typeof tokenProvider !== 'function') throw new Error('A signed-in token provider is required')
  async function request(method, shopId, path, body) {
    if (!UUID.test(shopId || '')) throw new Error('Select an authorized shop')
    const token = await tokenProvider()
    if (!token) throw new Error('Please sign in again')
    const response = await fetchImpl(endpoint.origin + '/api/shops/' + shopId + '/' + path, {
      method, redirect: 'error', cache: 'no-store',
      headers: { Authorization: 'Bearer ' + token,
        ...(body ? { 'Content-Type': 'application/json' } : {}) },
      ...(body ? { body: JSON.stringify(body) } : {}),
    })
    const data = await response.json().catch(() => null)
    if (response.status === 401) throw new Error('Your session expired; please sign in again')
    if (!response.ok) {
      const problem = new Error(
        response.status === 503 ? 'Trend intelligence is not enabled or temporarily unavailable in DEV.'
          : response.status === 403 || response.status === 404
            ? 'This shop or asset is not authorized for this action.'
            : 'Trend request could not be completed.'
      )
      problem.status = response.status
      throw problem
    }
    return data
  }
  return {
    improvePrompt: (shopId, originalPrompt, outputFormats, language = 'en-IN') => {
      if (typeof originalPrompt !== 'string' || !originalPrompt.trim() ||
          originalPrompt.length > 1500 || !Array.isArray(outputFormats) ||
          !outputFormats.length || !['en-IN', 'hi-IN', 'mr-IN'].includes(language)) {
        throw new Error('Enter a valid prompt, supported language and output formats')
      }
      return request('POST', shopId, 'improve-prompt', {
        original_prompt: originalPrompt, output_formats: outputFormats, language,
      })
    },
    getRecommendations: (shopId) => request('GET', shopId, 'trend-recommendations'),
    listDrafts: (shopId) => request('GET', shopId, 'content-drafts'),
    createDraft: (shopId, trendId, campaign, submissionId = null) => {
      if (!/^[a-f0-9]{32}$/.test(trendId || '') ||
          !campaign || typeof campaign !== 'object' || campaign.shop_id !== shopId ||
          (submissionId !== null && !UUID.test(submissionId))) {
        throw new Error('Choose a verified trend, authorized shop and submission ID')
      }
      return request('POST', shopId, 'content-drafts', {
        trend_id: trendId, campaign,
        ...(submissionId === null ? {} : { submission_id: submissionId }),
      })
    },
  }
}
