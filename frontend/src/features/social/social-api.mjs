// Part 2 social API gateway. No provider credentials belong in the browser.
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

function id(value) {
  if (typeof value !== 'string' || !UUID.test(value)) throw new Error('Invalid shop or job ID')
  return value
}

export function createSocialApi({ baseUrl, tokenProvider, fetchImpl = fetch }) {
  if (!baseUrl) return null
  const origin = new URL(baseUrl)
  if (origin.protocol !== 'https:' || origin.username || origin.password ||
      origin.search || origin.hash || origin.pathname !== '/') {
    throw new Error('Social API must use one HTTPS origin')
  }
  if (typeof tokenProvider !== 'function') throw new Error('Sign-in token provider required')
  async function request(method, path, payload) {
    const token = await tokenProvider()
    if (!token || typeof token !== 'string') throw new Error('Sign in again')
    const response = await fetchImpl(origin.origin + '/api/social' + path, {
      method, redirect: 'error', cache: 'no-store',
      headers: { Authorization: 'Bearer ' + token,
        ...(payload === undefined ? {} : { 'Content-Type': 'application/json' }) },
      ...(payload === undefined ? {} : { body: JSON.stringify(payload) }),
    })
    const result = await response.json().catch(() => null)
    if (!response.ok) {
      // Never display raw provider responses or token-containing error bodies.
      const message = {
        401: 'Please sign in again.',
        403: 'You do not have permission for this business.',
        404: 'Social publishing is not available on this server.',
        409: 'This publishing request has changed. Reload before trying again.',
        429: 'This business has reached its publishing quota.',
      }[response.status] || 'Social publishing is temporarily unavailable.'
      const error = new Error(message)
      error.status = response.status
      throw error
    }
    return result
  }
  return {
    listAccounts: shopId => request('GET', '/accounts?shop_id=' + id(shopId)),
    listJobs: shopId => request('GET', '/jobs?shop_id=' + id(shopId)),
    // Intentional: NO browser-side direct provider publishing or OAuth token handling.
  }
}
