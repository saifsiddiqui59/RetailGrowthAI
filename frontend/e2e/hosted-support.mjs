// Hosted RetailGrowthAI DEV only. No default or CI path may contact a remote project.
import { readFileSync, statSync } from 'node:fs'
import { extname } from 'node:path'

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const DEV_REF = 'jeearzffnjbvghwjjjrf'
const APPROVAL = 'I_APPROVE_RETAILGROWTHAI_DEV_E2E'
const IMAGE_TYPES = { '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp' }

function required(env, name) {
  if (!env[name] || !String(env[name]).trim()) throw new Error('Missing hosted DEV setting: ' + name)
  return String(env[name]).trim()
}
function origin(value, name) {
  const parsed = new URL(value)
  if (parsed.protocol !== 'https:' || parsed.username || parsed.password ||
      parsed.pathname !== '/' || parsed.search || parsed.hash || !parsed.hostname.includes('.')) {
    throw new Error(name + ' must be a clean public HTTPS origin')
  }
  if (/^(localhost|127\.|10\.|192\.168\.|172\.)/.test(parsed.hostname)) {
    throw new Error(name + ' must not address a local or private host')
  }
  return parsed.origin
}
function imageFile(file) {
  const extension = extname(file).toLowerCase()
  const mime = IMAGE_TYPES[extension]
  if (!mime) throw new Error('Hosted asset must be PNG, JPEG or WebP')
  const size = statSync(file).size
  if (size < 100 || size > 25 * 1024 * 1024) throw new Error('Hosted asset must be between 1 byte and 25 MB')
  const head = readFileSync(file).subarray(0, 16)
  const png = Buffer.from('89504e470d0a1a0a', 'hex')
  const jpeg = Buffer.from('ffd8ff', 'hex')
  const webp = Buffer.from('WEBP')
  const good = mime === 'image/png' ? head.subarray(0, 8).equals(png)
    : mime === 'image/jpeg' ? head.subarray(0, 3).equals(jpeg)
    : head.toString('ascii', 0, 4) === 'RIFF' && head.subarray(8, 12).equals(webp)
  if (!good) throw new Error('Image bytes do not match declared type')
  return { mime, size }
}
export function checkExpiredJwt(jwt, expectedIssuer, now = Date.now()) {
  const parts = jwt.split('.')
  if (parts.length !== 3) throw new Error('Expired JWT must have three sections')
  let claims
  try { claims = JSON.parse(Buffer.from(parts[1], 'base64url').toString('utf8')) }
  catch { throw new Error('Expired JWT payload is invalid') }
  if (claims.iss !== expectedIssuer || !Number.isFinite(claims.exp) ||
      claims.exp > (now / 1000) - 60 || claims.aud !== 'authenticated') {
    throw new Error('Expired JWT must have matching DEV issuer/audience and be expired by >=60 seconds')
  }
  return true
}
export function hostedConfig(env = process.env) {
  // Explicitly disabled on any Actions runner, even when someone supplies credentials.
  if (env.CI || env.GITHUB_ACTIONS) throw new Error('Hosted E2E is prohibited in CI')
  if (env.RG_E2E_APPROVAL !== APPROVAL || env.RG_E2E_TARGET !== 'dev') {
    throw new Error('Hosted DEV E2E requires explicit human approval and dev target')
  }
  const frontend = origin(required(env, 'RG_E2E_FRONTEND_URL'), 'frontend')
  const api = origin(required(env, 'RG_E2E_API_URL'), 'API')
  const supabase = origin(required(env, 'RG_E2E_SUPABASE_URL'), 'Supabase')
  if (supabase !== 'https://' + DEV_REF + '.supabase.co') {
    throw new Error('Refusing an unknown, production or WineShopPOS Supabase project')
  }
  const allowlist = required(env, 'RG_E2E_ALLOWED_ORIGINS').split(',').map(x => x.trim())
  if (new Set(allowlist).size !== 3 || ![frontend, api, supabase].every(x => allowlist.includes(x)) ||
      allowlist.some(x => ![frontend, api, supabase].includes(x))) {
    throw new Error('All three DEV HTTPS origins must match the pinned allowlist exactly')
  }
  // Require DEV environment naming even when an operator incorrectly pins a PROD host.
  if (![frontend, api].every(value => new URL(value).hostname.toLowerCase().includes('dev'))) {
    throw new Error('Both frontend and API hosts must be explicitly DEV-named')
  }
  if (frontend === api || api === supabase || frontend === supabase) {
    throw new Error('Hosted DEV origins must be isolated')
  }
  const shopA = required(env, 'RG_E2E_SHOP_A_ID')
  const shopB = required(env, 'RG_E2E_SHOP_B_ID')
  if (!UUID.test(shopA) || !UUID.test(shopB) || shopA === shopB) {
    throw new Error('Two distinct UUID shops are required for tenant security tests')
  }
  const a = { email: required(env, 'RG_E2E_USER_A_EMAIL'), password: required(env, 'RG_E2E_USER_A_PASSWORD') }
  const b = { email: required(env, 'RG_E2E_USER_B_EMAIL'), password: required(env, 'RG_E2E_USER_B_PASSWORD') }
  if (a.email === b.email || a.password === b.password) {
    throw new Error('Use two independently provisioned DEV-only users')
  }
  if (required(env, 'RG_E2E_RIGHTS_ATTESTED') !== 'yes') {
    throw new Error('Image ownership must be explicitly attested before upload')
  }
  const evidence = required(env, 'RG_E2E_IMAGE_EVIDENCE')
  if (evidence.length < 10 || evidence.length > 500) throw new Error('Provide 10–500 characters of genuine image rights evidence')
  const imagePath = required(env, 'RG_E2E_IMAGE_PATH')
  const image = imageFile(imagePath)
  const expiredJwt = required(env, 'RG_E2E_EXPIRED_JWT')
  checkExpiredJwt(expiredJwt, supabase + '/auth/v1')
  const pollTimeout = Number(env.RG_E2E_POLL_TIMEOUT_MS || 1200000)
  if (!Number.isInteger(pollTimeout) || pollTimeout < 60000 || pollTimeout > 1800000) {
    throw new Error('DEV polling timeout must be between 1 and 30 minutes')
  }
  const recoveryJob = String(env.RG_E2E_RECOVERY_JOB_ID || '').trim()
  if (recoveryJob && !UUID.test(recoveryJob)) throw new Error('Invalid pre-faulted DEV recovery job UUID')
  const publishable = required(env, 'RG_E2E_SUPABASE_PUBLISHABLE_KEY')
  if (/^(sb_secret_|eyJ)/.test(publishable)) throw new Error('Never supply a service key to the browser harness')
  return { frontend, api, supabase, allowlist, shopA, shopB, a, b, imagePath,
    image, evidence, expiredJwt, publishable, pollTimeout, recoveryJob }
}

export function signedDownloadUrl(value, supabase) {
  const url = new URL(value)
  if (url.protocol !== 'https:' || url.origin !== supabase ||
      !url.pathname.startsWith('/storage/v1/object/sign/retailgrowth-media/') ||
      !url.searchParams.get('token')) throw new Error('Non-private or untrusted signed download URL')
  return url.toString()
}

// Bounded retry for intermittent transport/503/429 during async status polling;
// no re-submission of mutating POST/PATCH calls.
export async function pollHosted(read, { timeoutMs, intervalMs = 5000, sleep = ms => new Promise(r => setTimeout(r, ms)),
  now = () => Date.now() }) {
  const deadline = now() + timeoutMs
  let error
  while (now() < deadline) {
    try {
      const response = await read()
      if (response.status === 'DRAFT' || response.status === 'SUCCEEDED') return response
      if (response.status === 'FAILED' || response.status === 'CANCELLED') {
        throw new Error('Job finished unsuccessfully: ' + response.status)
      }
      if (!['PLANNING', 'QUEUED', 'RUNNING', 'RETRYING'].includes(response.status)) {
        throw new Error('Unexpected job status: ' + response.status)
      }
      error = null
    } catch (e) {
      if (/Job finished unsuccessfully|Unexpected job status/.test(e.message)) throw e
      if (![429, 502, 503, 504].includes(e.status) && !e.transient) throw e
      error = e
    }
    await sleep(Math.min(intervalMs, Math.max(0, deadline - now())))
  }
  throw new Error('Timed out polling DEV job' + (error ? ' after transient errors' : ''))
}
