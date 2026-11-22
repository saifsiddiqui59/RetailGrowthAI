/**
 * Static frontend source review: mounted local editor does not leak data.
 * Actual authenticated browser flow remains covered by Vite/Playwright.
 */
import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const source = file => readFileSync(new URL(file, import.meta.url), 'utf8')
test('Creative Studio mounts only current-shop local editor; hosted v2 remains OFF', () => {
  const launch = source('../../frontend/src/features/dashboard/CreativeLaunchpad.jsx')
  const connected = source('../../frontend/src/features/video/VideoStudioConnected.jsx')
  assert.match(launch, /<VideoStudioConnected key=\{shopId\} shopId=\{shopId\}/)
  assert.match(launch, /enabled=\{false\}/)
  assert.match(launch, /configured && user && Boolean\(shopId\)/)
  assert.match(connected, /client\.getAccessToken\(\)/)
  assert.doesNotMatch(connected, /client\.accessToken\(\)/)
  assert.doesNotMatch(launch, /service_role|sb_secret_|VITE_FEATURE4_RENDER_ENABLED/)
})
