// RetailGrowthAI-only lightweight Supabase Auth v1 + PostgREST client.
// No service-role keys, no client-side authorization assumptions.
// Use a publishable key and let PostgreSQL RLS enforce every tenant boundary.
const STORAGE_KEY = 'retailgrowthai-auth-v1'
const ALLOWED_TABLES = new Set(['shops', 'shop_memberships', 'business_profiles', 'media_assets'])

export function createRetailClient({
  url = import.meta.env?.VITE_SUPABASE_URL,
  key = import.meta.env?.VITE_SUPABASE_PUBLISHABLE_KEY,
  storage = typeof window === 'undefined' ? null : window.sessionStorage,
  fetchImpl = (...args) => fetch(...args),
  clock = () => Date.now(),
} = {}) {
  const configured = Boolean(url && key && /^https:\/\//.test(url))
  const origin = configured ? url.replace(/\/+$/, '') : ''
  let session = null
  try {
    session = JSON.parse(storage?.getItem(STORAGE_KEY) || 'null')
  } catch { storage?.removeItem(STORAGE_KEY) }
  let refreshing = null

  function ensureConfigured() {
    if (!configured) throw new Error('RetailGrowthAI Supabase URL and publishable key are not configured')
  }
  function setSession(value) {
    session = value?.access_token && value?.refresh_token
      ? {
          access_token: value.access_token,
          refresh_token: value.refresh_token,
          expires_at: value.expires_at || Math.floor(clock() / 1000) + (value.expires_in || 3600),
        }
      : null
    if (session) storage?.setItem(STORAGE_KEY, JSON.stringify(session))
    else storage?.removeItem(STORAGE_KEY)
  }
  async function send(path, { method = 'GET', body, token, query, headers = {} } = {}) {
    ensureConfigured()
    const target = new URL(origin + path)
    if (query) for (const [name, value] of Object.entries(query)) {
      if (value !== undefined && value !== null) target.searchParams.set(name, String(value))
    }
    const response = await fetchImpl(target.toString(), {
      method,
      headers: {
        apikey: key,
        ...(token ? { Authorization: 'Bearer ' + token } : {}),
        ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        ...headers,
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    })
    const result = response.status === 204 ? null : await response.json().catch(() => null)
    if (!response.ok) {
      const message = result?.msg || result?.error_description || result?.message || result?.error || 'Supabase request failed'
      const error = new Error(message)
      error.status = response.status
      throw error
    }
    return result
  }
  function requireSession() {
    if (!session?.access_token) throw new Error('Sign in before accessing shop data')
    return session
  }
  async function refresh() {
    requireSession()
    if (!refreshing) {
      const oldToken = session.refresh_token
      refreshing = send('/auth/v1/token', {
        method: 'POST', query: { grant_type: 'refresh_token' }, body: { refresh_token: oldToken },
      }).then((data) => {
        // An in-flight refresh must not restore a deliberately cleared session.
        if (session?.refresh_token !== oldToken) throw new Error('Session changed')
        setSession(data)
        return session.access_token
      }).catch((error) => {
        if (session?.refresh_token === oldToken) setSession(null)
        throw error
      }).finally(() => { refreshing = null })
    }
    return refreshing
  }
  async function accessToken() {
    const current = requireSession()
    if (current.expires_at * 1000 - clock() <= 60_000) return refresh()
    return current.access_token
  }
  async function authRequest(path, opts = {}) {
    return send('/auth/v1/' + path, opts)
  }
  async function signIn(email, password) {
    const data = await authRequest('token', {
      method: 'POST', query: { grant_type: 'password' }, body: { email, password },
    })
    setSession(data)
    if (!session) throw new Error('Sign-in did not return a valid session')
    return data.user
  }
  async function signUp(email, password) {
    const data = await authRequest('signup', { method: 'POST', body: { email, password } })
    if (data?.access_token) setSession(data)
    return data
  }
  async function getUser() {
    return authRequest('user', { token: await accessToken() })
  }
  async function signOut() {
    const token = session?.access_token
    // Local session is always destroyed even if network revocation fails.
    setSession(null)
    if (token) {
      try { await authRequest('logout', { method: 'POST', token }) }
      catch { /* Access token will expire; never rehydrate the local session. */ }
    }
  }
  async function table(name, { method = 'GET', query = {}, body } = {}) {
    if (!ALLOWED_TABLES.has(name)) throw new Error('Table is not exposed by RetailGrowthAI foundation client')
    return send('/rest/v1/' + name, {
      method, query, body, token: await accessToken(),
      headers: method === 'POST' ? { Prefer: 'return=representation' }
        : method === 'PATCH' ? { Prefer: 'return=representation' } : {},
    })
  }
  async function listShops() {
    // Membership and shop lists are separately enforced by RLS, never by a supplied user_id.
    const memberships = await table('shop_memberships', {
      query: { select: 'shop_id,role,active', active: 'eq.true' },
    })
    const shops = await table('shops', { query: { select: 'id,name,slug,timezone,owner_user_id' } })
    return shops.map((shop) => ({ ...shop, membership: memberships.find((m) => m.shop_id === shop.id) || null }))
      .filter((shop) => shop.membership?.active)
  }
  async function createShop({ name, slug, timezone = 'Asia/Kolkata' }) {
    if (!name?.trim() || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug || '')) {
      throw new Error('Enter a business name and a lowercase hyphenated shop slug')
    }
    const user = await getUser()
    const rows = await table('shops', {
      method: 'POST', body: { owner_user_id: user.id, name: name.trim(), slug, timezone },
      query: { select: 'id,name,slug,timezone' },
    })
    return rows[0]
  }
  async function getBusinessProfile(shopId) {
    const rows = await table('business_profiles', {
      query: { select: '*', shop_id: 'eq.' + shopId, limit: '1' },
    })
    return rows[0] || null
  }
  async function updateBusinessProfile(shopId, values) {
    const editable = ['business_name', 'category', 'description', 'brand_voice', 'city', 'website_url', 'contact_email']
    const body = Object.fromEntries(editable.filter((field) => Object.hasOwn(values, field)).map((field) => [field, values[field]]))
    if (!Object.keys(body).length) throw new Error('No editable fields provided')
    body.updated_at = new Date(clock()).toISOString()
    const rows = await table('business_profiles', {
      method: 'PATCH', query: { shop_id: 'eq.' + shopId, select: '*' }, body,
    })
    // A zero-row update can indicate RLS denial (not always a thrown error).
    if (!rows?.length) throw new Error('Business profile not found or you do not have edit permission')
    return rows[0]
  }
  async function listMediaAssets(shopId) {
    if (!/^[0-9a-f]{8}-[0-9a-f-]{27,}$/.test(shopId || '')) throw new Error('Invalid shop ID')
    const rows = await table('media_assets', {
      query: { select: 'id,shop_id,source,license_name,mime_type',
        shop_id: 'eq.' + shopId, order: 'created_at.desc', limit: '100' },
    })
    return rows.filter(row => row.shop_id === shopId && row.license_name)
  }
  return {
    configured, getStoredSession: () => session, getAccessToken: accessToken,
    signIn, signUp, signOut, getUser,
    listShops, createShop, getBusinessProfile, updateBusinessProfile, listMediaAssets,
  }
}

// Lazy creation: unconfigured Vite/CI builds can still render their mock workspace.
let sharedClient
export function getRetailClient() {
  if (!sharedClient) sharedClient = createRetailClient()
  return sharedClient
}
