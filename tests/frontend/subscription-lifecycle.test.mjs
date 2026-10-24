import test from 'node:test'
import assert from 'node:assert/strict'
import { presentSubscription, subscriptionNotice } from '../../frontend/src/features/subscription/plan-display.mjs'

const NOW = Date.parse('2026-10-24T12:00:00Z')
const record = {
  plan_code: 'TRIAL', status: 'TRIAL',
  valid_from: '2026-10-23T00:00:00Z', valid_until: '2026-10-30T00:00:00Z',
  period_start: '2026-10-23T00:00:00Z', period_end: '2026-10-30T00:00:00Z',
}
function notice(details = record, usage = { campaign: 0, render: 0 }, now = NOW) {
  return subscriptionNotice(presentSubscription(details, usage, now))
}

test('healthy trial does not advertise renewal or fabricated upgrade', () => {
  assert.equal(notice(), null)
})
test('expiring in 48h shows notice and no payment CTA', () => {
  const found = notice(record, { campaign: 0, render: 0 }, Date.parse('2026-10-29T06:00:00Z'))
  assert.equal(found.code, 'EXPIRING_SOON')
  assert.match(found.text, /No automatic renewal/)
})
test('exact expiration and suspended entitlements are not labeled active', () => {
  for (const details of [record, { ...record, status: 'SUSPENDED' }]) {
    const found = notice(details, { campaign: 0, render: 0 }, Date.parse('2026-10-30T00:00:00Z'))
    assert.equal(found.code, 'ACCESS_EXPIRED')
  }
})
test('limits are shown without granting quota or self-upgrade', () => {
  const found = notice(record, { campaign: 2, render: 0 })
  assert.equal(found.code, 'PERIOD_LIMIT_REACHED')
  assert.match(found.text, /server-authorized/)
})
test('unverified summary is never considered healthy', () => {
  assert.throws(() => subscriptionNotice({ active: true }), /Verified/)
})
