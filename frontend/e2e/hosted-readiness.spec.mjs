import { test, expect } from '@playwright/test'
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { hostedConfig, checkExpiredJwt, signedDownloadUrl, pollHosted } from './hosted-support.mjs'

function fixture() {
  const dir = mkdtempSync(join(tmpdir(), 'rg-dev-e2e-'))
  const photo = join(dir, 'owned.png')
  writeFileSync(photo, Buffer.from('89504e470d0a1a0a00000000', 'hex'))
  const supabase = 'https://jeearzffnjbvghwjjjrf.supabase.co'
  const jwt = 'header.' + Buffer.from(JSON.stringify({ iss: supabase + '/auth/v1', aud: 'authenticated',
    exp: Math.floor(Date.now() / 1000) - 600 })).toString('base64url') + '.signature'
  const env = { RG_E2E_APPROVAL: 'I_APPROVE_RETAILGROWTHAI_DEV_E2E', RG_E2E_TARGET: 'dev',
    RG_E2E_FRONTEND_URL: 'https://retailgrowth-dev.example.test',
    RG_E2E_API_URL: 'https://api-dev.example.test', RG_E2E_SUPABASE_URL: supabase,
    RG_E2E_ALLOWED_ORIGINS: 'https://retailgrowth-dev.example.test,https://api-dev.example.test,' + supabase,
    RG_E2E_SHOP_A_ID: 'a1000000-0000-4000-8000-000000000001',
    RG_E2E_SHOP_B_ID: 'a2000000-0000-4000-8000-000000000001',
    RG_E2E_USER_A_EMAIL: 'a@example.test', RG_E2E_USER_A_PASSWORD: 'some-A-password',
    RG_E2E_USER_B_EMAIL: 'b@example.test', RG_E2E_USER_B_PASSWORD: 'some-B-password',
    RG_E2E_RIGHTS_ATTESTED: 'yes', RG_E2E_IMAGE_PATH: photo,
    RG_E2E_IMAGE_EVIDENCE: 'Photo taken and owned by test shop',
    RG_E2E_EXPIRED_JWT: jwt, RG_E2E_SUPABASE_PUBLISHABLE_KEY: 'sb_publishable_test_only' }
  return { dir, env, supabase }
}
test('approval, origin pinning, tenant split and real file signature are mandatory', () => {
  const { dir, env } = fixture()
  try {
    expect(hostedConfig(env).image.mime).toBe('image/png')
    for (const changes of [
      { RG_E2E_APPROVAL: '' }, { RG_E2E_TARGET: 'prod' }, { GITHUB_ACTIONS: 'true' },
      { CI: 'true' }, { RG_E2E_SUPABASE_URL: 'https://untrusted.supabase.co' },
      { RG_E2E_FRONTEND_URL: 'http://retailgrowth-dev.example.test' },
      { RG_E2E_FRONTEND_URL: 'http://localhost:5173' },
      { RG_E2E_ALLOWED_ORIGINS: env.RG_E2E_ALLOWED_ORIGINS.replace('api-dev', 'api-prod') },
      { RG_E2E_SHOP_B_ID: env.RG_E2E_SHOP_A_ID }, { RG_E2E_RIGHTS_ATTESTED: 'no' },
      { RG_E2E_IMAGE_EVIDENCE: '' }, { RG_E2E_USER_B_EMAIL: env.RG_E2E_USER_A_EMAIL },
      { RG_E2E_SUPABASE_PUBLISHABLE_KEY: 'sb_secret_danger' }, { RG_E2E_POLL_TIMEOUT_MS: '99999999' },
      { RG_E2E_RECOVERY_JOB_ID: 'not-a-uuid' },
    ]) {
      expect(() => hostedConfig({ ...env, ...changes })).toThrow()
    }
    writeFileSync(env.RG_E2E_IMAGE_PATH, Buffer.from('not really a photo'))
    expect(() => hostedConfig(env)).toThrow(/Image bytes/)
  } finally { rmSync(dir, { recursive: true, force: true }) }
})
test('expired token requirements and signed URL origin/path reject cross-tenant redirects', () => {
  const { dir, env, supabase } = fixture()
  try {
    expect(checkExpiredJwt(env.RG_E2E_EXPIRED_JWT, supabase + '/auth/v1')).toBe(true)
    expect(() => checkExpiredJwt('not-jwt', supabase + '/auth/v1')).toThrow()
    const future = 'x.' + Buffer.from(JSON.stringify({ iss: supabase + '/auth/v1', aud: 'authenticated',
      exp: Date.now() / 1000 + 3600 })).toString('base64url') + '.x'
    expect(() => checkExpiredJwt(future, supabase + '/auth/v1')).toThrow()
    const good = supabase + '/storage/v1/object/sign/retailgrowth-media/a/uploads/out.mp4?token=opaque'
    expect(signedDownloadUrl(good, supabase)).toBe(good)
    for (const url of [good.replace(supabase, 'https://attacker.example'),
      good.replace('/object/sign/', '/object/public/'), good.split('?')[0], 'http://insecure.test/output.mp4']) {
      expect(() => signedDownloadUrl(url, supabase)).toThrow()
    }
  } finally { rmSync(dir, { recursive: true, force: true }) }
})
test('read-only polling survives short 503/429 and fails closed on denial or terminal failure', async () => {
  const transient = status => Object.assign(new Error('Temporary'), { status })
  let count = 0
  const states = [() => { throw transient(503) }, () => { throw transient(429) },
    () => ({ status: 'RUNNING' }), () => ({ status: 'SUCCEEDED', output_asset_id: 'asset' })]
  expect(await pollHosted(async () => states[count++](), {
    timeoutMs: 20, intervalMs: 1, sleep: async () => {},
  })).toMatchObject({ status: 'SUCCEEDED' })
  expect(count).toBe(4)
  await expect(pollHosted(async () => { throw Object.assign(new Error('Denied'), { status: 401 }) },
    { timeoutMs: 20 })).rejects.toThrow('Denied')
  await expect(pollHosted(async () => ({ status: 'FAILED' }), { timeoutMs: 20 }))
    .rejects.toThrow('unsuccessfully')
  let ticks = 0
  await expect(pollHosted(async () => ({ status: 'QUEUED' }), {
    timeoutMs: 3, intervalMs: 1, now: () => ticks++, sleep: async () => {},
  })).rejects.toThrow('Timed out')
})
test('hosted suites are excluded by the existing default offline browser suite', async () => {
  const { readFileSync } = await import('node:fs')
  const conf = readFileSync(new URL('./playwright.config.mjs', import.meta.url), 'utf8')
  expect(conf).toContain("testMatch: '**/*.spec.mjs'")
  expect('hosted-journey.hosted.mjs'.endsWith('.spec.mjs')).toBe(false)
  expect(readFileSync(new URL('./hosted.playwright.config.mjs', import.meta.url), 'utf8'))
    .not.toContain('webServer:')
})
