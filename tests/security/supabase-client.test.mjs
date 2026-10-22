import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createRetailClient } from '../../frontend/src/lib/supabase.js'

function storage() {
  const items = new Map()
  return {
    getItem: (k) => items.get(k) || null,
    setItem: (k, v) => items.set(k, v),
    removeItem: (k) => items.delete(k),
  }
}
const uid = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
function fixture(fetchImpl, clock = () => 1_000_000) {
  return createRetailClient({ url: 'https://retailgrowthai-dev.example.supabase.co',
    key: 'sb_publishable_example', storage: storage(), fetchImpl, clock })
}
function json(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

test('browser REST calls carry user bearer token and NEVER service-role credentials', async () => {
  const calls = []
  const api = fixture(async (url, options) => {
    calls.push({ url, options })
    if (url.includes('/auth/v1/token')) return json({ access_token: 'user-access', refresh_token: 'user-refresh', expires_in: 3600 })
    if (url.includes('/rest/v1/shop_memberships')) return json([{ shop_id: 's1', role: 'OWNER', active: true }])
    if (url.includes('/rest/v1/shops')) return json([{ id: 's1', name: 'Business A' }])
    throw Error('Unexpected request: ' + url)
  })
  await api.signIn('user@example.test', 'password123')
  const shops = await api.listShops()
  assert.equal(shops.length, 1)
  assert.equal(shops[0].membership.role, 'OWNER')
  for (const call of calls.filter((c) => c.url.includes('/rest/v1/'))) {
    assert.equal(call.options.headers.Authorization, 'Bearer user-access')
    assert.equal(call.options.headers.apikey, 'sb_publishable_example')
    assert.doesNotMatch(JSON.stringify(call), /service.role|service_role|secret_key/i)
  }
})
test('business profile PATCH ignores forged shop_id and rejects invisible zero-row update', async () => {
  let patch
  const api = fixture(async (url, options) => {
    if (url.includes('/auth/v1/token')) return json({ access_token: 'at', refresh_token: 'rt', expires_in: 3600 })
    if (url.includes('/rest/v1/business_profiles')) {
      patch = { url, options }
      return json([])
    }
    throw Error('unexpected')
  })
  await api.signIn('u@example.test', 'secret12')
  await assert.rejects(() => api.updateBusinessProfile('real-shop', {
    shop_id: 'forged-other-shop', business_name: 'Changed', owner_user_id: uid, role: 'OWNER',
  }), /not found or you do not have edit permission/)
  assert.equal(new URL(patch.url).searchParams.get('shop_id'), 'eq.real-shop')
  assert.equal(JSON.parse(patch.options.body).shop_id, undefined)
  assert.equal(JSON.parse(patch.options.body).role, undefined)
})
test('expires access tokens through one refresh and drops invalidated sessions', async () => {
  const calls = []
  let clock = 1_000_000
  const api = fixture(async (url) => {
    calls.push(url)
    if (url.includes('grant_type=password')) return json({ access_token: 'expired', refresh_token: 'refresh', expires_in: 1 })
    if (url.includes('grant_type=refresh_token')) return json({ access_token: 'fresh', refresh_token: 'refresh-new', expires_in: 3600 })
    if (url.includes('/auth/v1/user')) return json({ id: uid })
    throw Error('unexpected ' + url)
  }, () => clock)
  await api.signIn('u@example.test', 'secret12')
  clock += 2000
  assert.equal((await api.getUser()).id, uid)
  assert.equal(calls.filter((url) => url.includes('grant_type=refresh_token')).length, 1)
  assert.equal(api.getStoredSession().access_token, 'fresh')
  await api.signOut()
  assert.equal(api.getStoredSession(), null)
  await assert.rejects(() => api.getUser(), /Sign in before accessing shop data/)
})
test('unconfigured client refuses all network/auth requests', async () => {
  const api = createRetailClient({ url: '', key: '', storage: storage() })
  assert.equal(api.configured, false)
  await assert.rejects(() => api.signIn('a', 'b'), /not configured/)
})


const mediaShop = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
const uploadUuid = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'
const recordedMedia = 'cccccccc-cccc-4ccc-8ccc-cccccccccccc'
function pngFile() {
  const bytes = new Uint8Array(256)
  bytes.set([137, 80, 78, 71, 13, 10, 26, 10])
  return new Blob([bytes], { type: 'image/png' })
}

test('private upload verifies bytes, user JWT, tenant path and registration RPC', async () => {
  const requests = []
  const client = createRetailClient({
    url: 'https://rg.example.supabase.co', key: 'sb_publishable_demo',
    storage: storage(), uuidFactory: () => uploadUuid,
    fetchImpl: async (url, options) => {
      requests.push({ url, options })
      if (url.includes('/auth/v1/token')) {
        return json({ access_token: 'user-access', refresh_token: 'user-refresh', expires_in: 3600 })
      }
      if (url.includes('/storage/v1/object/')) return json({ Key: 'private' }, 201)
      if (url.includes('/rest/v1/rpc/register_uploaded_image')) return json(recordedMedia)
      throw Error('unexpected URL ' + url)
    },
  })
  await client.signIn('editor@example.test', 'password123')
  const media = await client.uploadImageAsset(mediaShop, {
    file: pngFile(), licenseName: 'owned',
    attribution: 'Original product photograph created by our own team',
    confirmedRights: true,
  })
  assert.equal(media.id, recordedMedia)
  const upload = requests.find(entry => entry.url.includes('/storage/v1/object/'))
  assert.equal(upload.url, 'https://rg.example.supabase.co/storage/v1/object/retailgrowth-media/' +
    mediaShop + '/uploads/' + uploadUuid + '.png')
  assert.equal(upload.options.method, 'POST')
  assert.equal(upload.options.redirect, 'error')
  assert.equal(upload.options.headers.Authorization, 'Bearer user-access')
  assert.equal(upload.options.headers['x-upsert'], 'false')
  assert.equal(upload.options.body.type, 'image/png')
  const rpc = requests.find(entry => entry.url.includes('/rest/v1/rpc/'))
  assert.equal(rpc.options.headers.Authorization, 'Bearer user-access')
  assert.deepEqual(JSON.parse(rpc.options.body), {
    p_shop_id: mediaShop,
    p_object_path: mediaShop + '/uploads/' + uploadUuid + '.png',
    p_license_name: 'owned', p_license_url: null,
    p_attribution: 'Original product photograph created by our own team',
  })
  assert.doesNotMatch(JSON.stringify(rpc), /service.role|service_role|sb_secret_/i)
})

test('invalid ownership assertion, file signature and license URL prevent upload', async () => {
  let calls = 0
  const client = createRetailClient({
    url: 'https://rg.example.supabase.co', key: 'sb_publishable_demo',
    storage: storage(), uuidFactory: () => uploadUuid,
    fetchImpl: async (url) => {
      calls++
      if (url.includes('/auth/v1/token')) {
        return json({ access_token: 'user-access', refresh_token: 'refresh', expires_in: 3600 })
      }
      throw new Error('unauthorized network call ' + url)
    },
  })
  await client.signIn('editor@example.test', 'password123')
  const originalCalls = calls
  const base = { file: pngFile(), licenseName: 'owned',
    attribution: 'Original image created and owned by us', confirmedRights: true }
  await assert.rejects(() => client.uploadImageAsset(mediaShop, { ...base, confirmedRights: false }), /confirm/)
  await assert.rejects(() => client.uploadImageAsset('not-a-shop-id', base), /business/)
  await assert.rejects(() => client.uploadImageAsset(mediaShop, {
    ...base, licenseName: 'commercial', licenseUrl: 'http://not-secure.test/evidence',
  }), /HTTPS/)
  const corrupted = new Blob([new Uint8Array(256)], { type: 'image/png' })
  await assert.rejects(() => client.uploadImageAsset(mediaShop, { ...base, file: corrupted }), /bytes/)
  assert.equal(calls, originalCalls)
})

test('server-denied metadata registration never claims upload success', async () => {
  const client = createRetailClient({
    url: 'https://rg.example.supabase.co', key: 'sb_publishable_demo',
    storage: storage(), uuidFactory: () => uploadUuid,
    fetchImpl: async (url) => {
      if (url.includes('/auth/v1/token')) {
        return json({ access_token: 'user-access', refresh_token: 'user-refresh', expires_in: 3600 })
      }
      if (url.includes('/storage/v1/object/')) return json({ Key: 'private' }, 201)
      if (url.includes('/rest/v1/rpc/')) return json(null)
      throw Error('unexpected')
    },
  })
  await client.signIn('editor@example.test', 'password123')
  await assert.rejects(() => client.uploadImageAsset(mediaShop, {
    file: pngFile(), licenseName: 'owned', confirmedRights: true,
    attribution: 'Created by the brand photography team',
  }), /registration was denied/)
})

