// Part 2 social API gateway. No provider credentials belong in the browser.
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

function id(value) {
  if (typeof value !== 'string' || !UUID.test(value)) throw new Error('Invalid shop or job ID')
  return value
}

const PROVIDERS = new Set(['instagram', 'facebook', 'linkedin', 'youtube'])
function providerId(value) {
  if (!PROVIDERS.has(value)) throw new Error('Unsupported social provider')
  return value
}
function boundedSecret(value, max) {
  if (typeof value !== 'string' || !value || value.length > max) {
    throw new Error('Invalid OAuth callback')
  }
  return value
}

// Only our explicitly known official authorization hosts/paths may be opened.
export function trustedConsentUrl(value, provider) {
  providerId(provider)
  if (typeof value !== 'string' || value.length > 4000) throw new Error('Invalid consent URL')
  const url = new URL(value)
  const allowed = {
    youtube: url.hostname === 'accounts.google.com' && url.pathname === '/o/oauth2/v2/auth',
    linkedin: url.hostname === 'www.linkedin.com' && url.pathname === '/oauth/v2/authorization',
    facebook: url.hostname === 'www.facebook.com' && new RegExp('^/v[0-9]{1,2}[.][0-9]{1,2}/dialog/oauth
    instagram: url.hostname === 'www.facebook.com' && new RegExp('^/v[0-9]{1,2}[.][0-9]{1,2}/dialog/oauth
  }
  if (url.protocol !== 'https:' || url.username || url.password || url.hash ||
      url.port || !allowed[provider] || !url.searchParams.get('state') ||
      !url.searchParams.get('redirect_uri')) {
    throw new Error('Invalid consent URL')
  }
  return url.href
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
    startOAuth: (shopId, provider) => request('POST', '/oauth/start',
      {shop_id: id(shopId), provider: providerId(provider)}),
    completeOAuth: (shopId, provider, state, code) => request('POST', '/oauth/complete',
      {shop_id: id(shopId), provider: providerId(provider),
       state: boundedSecret(state, 256), code: boundedSecret(code, 4096)}),
    disconnectAccount: (shopId, accountId) => request('POST', '/oauth/disconnect',
      {shop_id: id(shopId), account_id: id(accountId)}),
    // Intentional: NO browser-side direct provider publishing or OAuth token handling.
  }
}
).test(url.pathname),
    instagram: url.hostname === 'www.facebook.com' && /^\\/v\\d{1,2}\\.\\d{1,2}\\/dialog\\/oauth$/.test(url.pathname),
  }
  if (url.protocol !== 'https:' || url.username || url.password || url.hash ||
      url.port || !allowed[provider] || !url.searchParams.get('state') ||
      !url.searchParams.get('redirect_uri')) {
    throw new Error('Invalid consent URL')
  }
  return url.href
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
    startOAuth: (shopId, provider) => request('POST', '/oauth/start',
      {shop_id: id(shopId), provider: providerId(provider)}),
    completeOAuth: (shopId, provider, state, code) => request('POST', '/oauth/complete',
      {shop_id: id(shopId), provider: providerId(provider),
       state: boundedSecret(state, 256), code: boundedSecret(code, 4096)}),
    disconnectAccount: (shopId, accountId) => request('POST', '/oauth/disconnect',
      {shop_id: id(shopId), account_id: id(accountId)}),
    // Intentional: NO browser-side direct provider publishing or OAuth token handling.
  }
}
).test(url.pathname),
  }
  if (url.protocol !== 'https:' || url.username || url.password || url.hash ||
      url.port || !allowed[provider] || !url.searchParams.get('state') ||
      !url.searchParams.get('redirect_uri')) {
    throw new Error('Invalid consent URL')
  }
  return url.href
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
    startOAuth: (shopId, provider) => request('POST', '/oauth/start',
      {shop_id: id(shopId), provider: providerId(provider)}),
    completeOAuth: (shopId, provider, state, code) => request('POST', '/oauth/complete',
      {shop_id: id(shopId), provider: providerId(provider),
       state: boundedSecret(state, 256), code: boundedSecret(code, 4096)}),
    disconnectAccount: (shopId, accountId) => request('POST', '/oauth/disconnect',
      {shop_id: id(shopId), account_id: id(accountId)}),
    // Intentional: NO browser-side direct provider publishing or OAuth token handling.
  }
}
).test(url.pathname),
    instagram: url.hostname === 'www.facebook.com' && /^\\/v\\d{1,2}\\.\\d{1,2}\\/dialog\\/oauth$/.test(url.pathname),
  }
  if (url.protocol !== 'https:' || url.username || url.password || url.hash ||
      url.port || !allowed[provider] || !url.searchParams.get('state') ||
      !url.searchParams.get('redirect_uri')) {
    throw new Error('Invalid consent URL')
  }
  return url.href
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
    startOAuth: (shopId, provider) => request('POST', '/oauth/start',
      {shop_id: id(shopId), provider: providerId(provider)}),
    completeOAuth: (shopId, provider, state, code) => request('POST', '/oauth/complete',
      {shop_id: id(shopId), provider: providerId(provider),
       state: boundedSecret(state, 256), code: boundedSecret(code, 4096)}),
    disconnectAccount: (shopId, accountId) => request('POST', '/oauth/disconnect',
      {shop_id: id(shopId), account_id: id(accountId)}),
    // Intentional: NO browser-side direct provider publishing or OAuth token handling.
  }
}
