#!/usr/bin/env node
/* Import verified Pexels *original bytes* for a local, cross-feature clothing
 * media test. Never upload to Supabase or pretend stock is the shop's product.
 * Uses actual pexels/pexels-javascript official SDK API, NOT a scraper.
 *
 * node import-official-pexels.mjs --plan      No network/key; prints queue.
 * PEXELS_API_KEY=... node import-official-pexels.mjs --import
 * Requires npm install pexels@1.2.1 in a local test environment.
 */
import { readFile, writeFile, mkdir, rename, rm } from 'node:fs/promises'
import { createWriteStream } from 'node:fs'
import { createHash } from 'node:crypto'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createRequire } from 'node:module'
import { pipeline } from 'node:stream/promises'
import { Readable, Transform } from 'node:stream'

const root = dirname(fileURLToPath(import.meta.url))
const assets = JSON.parse(await readFile(join(root, 'manifest.json'), 'utf8'))
const downloads = join(root, 'downloaded-private-review-required')
const rows = assets.source_media
const ids = new Set(rows.map(row => row.candidate_id))
if (ids.size !== 4 || rows.length !== 4 || rows.some(r => !/^https:\/\/www\.pexels\.com\//.test(r.source_page))) {
  throw new Error('Unexpected clothing media discovery catalog')
}
if (process.argv.length !== 3 || !['--plan', '--import'].includes(process.argv[2])) {
  throw new Error('Usage: node import-official-pexels.mjs --plan|--import')
}
if (process.argv[2] === '--plan') {
  process.stdout.write(JSON.stringify({
    shop: assets.shop.display_name, kind: 'DISCOVERY_PLAN_NOT_MEDIA',
    items: rows.map(({ candidate_id, source_page, media_type }) =>
      ({ candidate_id, source_page, media_type, imported: false })),
    can_publish: false, original_media_downloaded: false,
  }, null, 2) + '\n')
  process.exit(0)
}
if (!process.env.PEXELS_API_KEY || process.env.PEXELS_API_KEY.length < 15) {
  throw new Error('An operator-provided PEXELS_API_KEY is required; no scraping or anonymous API calls')
}
const require = createRequire(import.meta.url)
let sdk
try { sdk = require('pexels') }
catch { throw new Error('Install the official pinned Pexels SDK locally: npm install pexels@1.2.1') }
if (typeof sdk.createClient !== 'function') throw new Error('Pexels official SDK missing createClient')
const client = sdk.createClient(process.env.PEXELS_API_KEY)
await mkdir(downloads, { recursive: true })

const isPexelsMediaUrl = (url, kind) => {
  try {
    const parsed = new URL(url)
    return parsed.protocol === 'https:' && !parsed.username && !parsed.password &&
      parsed.port === '' && parsed.hostname ===
      (kind === 'IMAGE' ? 'images.pexels.com' : 'videos.pexels.com')
  } catch { return false }
}

async function fetchVerified(url, kind, target, limit) {
  if (!isPexelsMediaUrl(url, kind)) throw new Error('Unapproved source media host')
  // Redirects are deliberately rejected so API keys and downloads never
  // jump to unreviewed CDN origins. Missing/outdated links fail closed.
  const response = await fetch(url, { redirect: 'error',
    signal: AbortSignal.timeout(60000) })
  const mime = (response.headers.get('content-type') || '').split(';')[0].toLowerCase()
  if (!response.ok || (kind === 'IMAGE' ? !['image/jpeg','image/png'].includes(mime) :
    mime !== 'video/mp4')) throw new Error('Pexels file is missing or wrong MIME')
  const indicated = Number(response.headers.get('content-length') || 0)
  if (indicated > limit || !response.body) throw new Error('Source media exceeds limit')
  const hash = createHash('sha256')
  let bytes = 0
  const part = target + '.tmp'
  const checker = new Transform({ transform(chunk, _, done) {
    bytes += chunk.length
    if (bytes > limit) return done(new Error('Media exceeds bounded import limit'))
    hash.update(chunk)
    done(null, chunk)
  } })
  try {
    await pipeline(Readable.fromWeb(response.body), checker, createWriteStream(part, { flags: 'wx' }))
    const signature = await readFile(part).then(data => data.subarray(0, 12))
    if (kind === 'IMAGE' && !(signature[0] === 255 && signature[1] === 216 &&
        signature[2] === 255) && !(signature.subarray(0,8).equals(
        Buffer.from([137,80,78,71,13,10,26,10])))) {
      throw new Error('Invalid photo signature')
    }
    if (kind === 'VIDEO' && signature.subarray(4,8).toString('ascii') !== 'ftyp') {
      throw new Error('Invalid video signature')
    }
    await rename(part, target)
    return { bytes, sha256: hash.digest('hex'), mime }
  } catch (error) {
    await rm(part, {force:true})
    throw error
  }
}

const receipt = { fixture_version: assets.fixture_version,
  created_at: new Date().toISOString(), media: [], can_publish: false,
  rights_review_status: 'REVIEW_REQUIRED_BEFORE_PRIVATE_SHOP_IMPORT',
  tenant_uploaded: false, people_model_release_verified: false,
  business_product_identity_verified: false,
}
for (const row of rows) {
  const id = Number(row.candidate_id.match(/(\d+)$/)?.[1])
  if (!Number.isSafeInteger(id)) throw new Error('Unknown media identifier')
  const media = row.media_type === 'IMAGE'
    ? await client.photos.show({id}) : await client.videos.show({id})
  if (media.error || media.id !== id) throw new Error('Provider returned incorrect Pexels media ID')
  const url = row.media_type === 'IMAGE'
    ? media.src?.original
    : media.video_files?.filter(file => file.file_type === 'video/mp4' &&
        isPexelsMediaUrl(file.link, 'VIDEO') &&
        Number.isInteger(file.width) && Number.isInteger(file.height) &&
        (row.orientation === 'portrait' ? file.height > file.width :
          file.width > file.height) &&
        file.width >= (row.orientation === 'portrait' ? 1080 : 1920) &&
        file.height >= (row.orientation === 'portrait' ? 1920 : 1080))
      // Modified from MIT MoneyPrinterTurbo material.py: smallest
      // adequate rendition, rather than downloading huge 4K sources.
      .sort((a,b) => a.width * a.height - b.width * b.height)[0]?.link
  if (!isPexelsMediaUrl(url, row.media_type)) throw new Error('No vetted Pexels original file URL')
  const ext = row.media_type === 'IMAGE' ? '.jpg' : '.mp4'
  const target = join(downloads, row.candidate_id + ext)
  const meta = await fetchVerified(url, row.media_type, target,
    row.media_type === 'IMAGE' ? 12000000 : 60000000)
  receipt.media.push({ candidate_id: row.candidate_id, local_filename: row.candidate_id + ext,
    original_sha256: meta.sha256, bytes: meta.bytes, mime: meta.mime,
    provider: 'Pexels', source_page: row.source_page, license_page: row.license_page,
    source_review_status: 'ORIGINAL_BYTES_FETCHED_RIGHTS_STILL_UNREVIEWED',
    can_publish: false })
}
await writeFile(join(downloads, 'receipt.json'), JSON.stringify(receipt,null,2)+'\n',
  {flag:'w',mode:0o600})
process.stdout.write('Fetched '+receipt.media.length+
  ' Pexels originals into local fixture; review rights and import with a real shop owner before use.\n')
