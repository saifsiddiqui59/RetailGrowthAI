import test from 'node:test'
import assert from 'node:assert/strict'
import { createRetailClient } from '../../frontend/src/lib/supabase.js'

const UUID = 'f1000000-0000-4000-8000-000000000011'
function fakeStorage() {
  const map = new Map()
  return { getItem: (key) => map.get(key) || null,
    setItem: (key, val) => map.set(key, val), removeItem: (key) => map.delete(key) }
}
function response(data, status = 200) {
  return { ok: status < 400, status,
    json: async () => data }
}

test('regular login JWT is reused to check platform privileges, never a service key', async () => {
  const calls = []
  const client = createRetailClient({
    url: 'https://retailgrowth.example.test', key: 'sb_publishable_key',
    storage: fakeStorage(), clock: () => 1700000000000,
    fetchImpl: async (url, options) => {
      const req = new URL(url)
      calls.push({ req, options })
      if (req.pathname === '/auth/v1/token') return response({
        access_token: 'user-jwt', refresh_token: 'refresh', expires_in: 3600,
      })
      if (req.pathname === '/auth/v1/user') return response({ id: UUID, email: 'root@example.invalid' })
      if (req.pathname === '/rest/v1/rpc/retail_platform_me') return response(true)
      if (req.pathname === '/rest/v1/rpc/retail_platform_summary') return response({
        retailers: 3, campaigns: 5,
      })
      if (req.pathname === '/rest/v1/rpc/retail_platform_shops') return response({
        total: 0, shops: [],
      })
      if (req.pathname === '/rest/v1/rpc/retail_platform_set_subscription') return response({
        shop_id: UUID, plan_code: 'STARTER', status: 'ACTIVE',
      })
      throw new Error('unexpected fetch ' + req.pathname)
    },
  })
  await client.signIn('root@example.invalid', 'offline-only-password')
  assert.equal((await client.getUser()).email, 'root@example.invalid')
  assert.equal(await client.isPlatformAdmin(), true)
  assert.equal((await client.getPlatformSummary()).retailers, 3)
  assert.equal((await client.listPlatformShops(10, 0)).total, 0)
  assert.equal((await client.setPlatformSubscription({
    shopId: UUID, planCode: 'STARTER', status: 'ACTIVE',
    validUntil: '2027-01-01', reason: 'Approved manually by provider',
  })).plan_code, 'STARTER')
  const privileged = calls.filter(x => x.req.pathname.startsWith('/rest/v1/rpc/'))
  assert.equal(privileged.length, 4)
  assert.ok(privileged.every(x =>
    x.options.headers.Authorization === 'Bearer user-jwt' &&
    x.options.headers.apikey === 'sb_publishable_key' &&
    x.options.method === 'POST'
  ))
  assert.ok(privileged.every(x => !JSON.stringify(x.options).includes('service_role')))
  const body = JSON.parse(privileged.at(-1).options.body)
  assert.equal(body.p_shop_id, UUID)
  assert.equal(body.p_reason, 'Approved manually by provider')
})

test('ordinary shop login is valid but platform actions are rejected and cannot self-upgrade', async () => {
  const client = createRetailClient({
    url: 'https://retailgrowth.example.test', key: 'pub',
    storage: fakeStorage(), clock: () => 1700000000000,
    fetchImpl: async (url) => {
      if (url.includes('/auth/v1/token')) return response({
        access_token: 'owner-jwt', refresh_token: 'r', expires_in: 3600,
      })
      if (url.includes('/rest/v1/rpc/retail_platform_me')) return response(false)
      if (url.includes('/rest/v1/rpc/retail_platform_summary')) return response({
        code: '42501', message: 'PLATFORM_ADMIN_REQUIRED',
      }, 403)
      throw new Error('unexpected path ' + url)
    },
  })
  await client.signIn('owner@example.invalid', 'offline-password')
  assert.equal(await client.isPlatformAdmin(), false)
  await assert.rejects(client.getPlatformSummary(), /PLATFORM_ADMIN_REQUIRED/)
  await assert.rejects(client.setPlatformSubscription({
    shopId: UUID, planCode: 'TRIAL', status: 'ACTIVE',
    validUntil: '2027-01-01', reason: 'owner attempted upgrade',
  }), /Invalid privileged/)
  await assert.rejects(client.listPlatformShops(500, 0), /page size/)
})

test('invalid email-password login cannot invoke admin RPC with a session', async () => {
  let platformRequests = 0
  const client = createRetailClient({
    url: 'https://retailgrowth.example.test', key: 'pub',
    storage: fakeStorage(),
    fetchImpl: async (url) => {
      if (url.includes('/auth/v1/token')) return response({
        error_description: 'Invalid login credentials',
      }, 400)
      platformRequests++
      throw new Error('privileged path attempted')
    },
  })
  await assert.rejects(client.signIn('unknown@example.invalid', 'wrong'), /Invalid login/)
  await assert.rejects(client.isPlatformAdmin(), /Sign in before/)
  assert.equal(platformRequests, 0)
})
