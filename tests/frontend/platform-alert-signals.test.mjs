import test from 'node:test'
import assert from 'node:assert/strict'
import { derivePlatformAlerts } from '../../frontend/src/features/platform/alert-signals.mjs'
const now = Date.parse('2026-10-24T12:00:00Z')
const summary = {retailers:30,expired_or_suspended:2}
const requests = [{status:'PENDING',user_id:'u1',email:'retailer@example.invalid',requested_at:'2026-10-23T12:00:00Z'}]
const listing = {total:27,shops:[
  {shop_id:'s1',name:'Soon Shop',subscription_status:'ACTIVE',valid_until:'2026-10-28T12:00:00Z'},
  {shop_id:'s2',name:'Future Shop',subscription_status:'ACTIVE',valid_until:'2026-12-28T12:00:00Z'},
  {shop_id:'s3',name:'Suspended',subscription_status:'SUSPENDED',valid_until:'2026-10-28T12:00:00Z'},
]}
test('root platform snapshots derive pending, global expiry, due soon and honest coverage', () => {
  const alerts = derivePlatformAlerts({summary,requests,listing,now})
  assert.equal(alerts.filter(a=>a.level==='action').length,2)
  assert.ok(alerts.some(a=>a.id==='signup:u1' && a.destination==='/platform-admin'))
  assert.ok(alerts.some(a=>a.id==='expiry:s1'))
  assert.ok(!alerts.some(a=>a.id==='expiry:s2'||a.id==='expiry:s3'))
  assert.ok(alerts.some(a=>a.id==='coverage:partial'))
  assert.ok(alerts.some(a=>a.id==='integration:pending'))
})
test('unavailable authorization/metrics fail closed; do not silently produce empty inbox', () => {
  assert.throws(()=>derivePlatformAlerts({summary:null,requests,listing,now}),/unavailable/)
  assert.throws(()=>derivePlatformAlerts({summary,requests:null,listing,now}),/unavailable/)
  assert.throws(()=>derivePlatformAlerts({summary,requests,listing:{total:0,shops:[{}]},now}),/unavailable/)
})
test('no bogus actionable alerts for zero, already-expired, malformed or missing data', () => {
  const items=derivePlatformAlerts({summary:{retailers:0,expired_or_suspended:0},requests:[],
    listing:{total:2,shops:[
      {shop_id:'old',name:'Old',subscription_status:'EXPIRED',valid_until:'2026-10-23T00:00:00Z'},
      {shop_id:'unknown',name:'Unknown',subscription_status:'ACTIVE',valid_until:null},
    ]},now})
  assert.equal(items.filter(x=>x.level==='action'||x.level==='attention').length,0)
})
