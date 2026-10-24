import test from 'node:test'
import assert from 'node:assert/strict'
import {classifySubscription,buildSubscriptionHealth,filterSubscriptionHealth} from '../../frontend/src/features/platform/subscription-health.mjs'
const now=Date.parse('2026-10-24T12:00:00Z')
const row=(id,name,status,end)=>({shop_id:id,name,slug:name.toLowerCase().replaceAll(' ','-'),plan_code:'STARTER',subscription_status:status,valid_until:end})
const rows=[
 row('one','Renew Soon','ACTIVE','2026-10-26T12:00:00Z'),
 row('two','Already Expired','ACTIVE','2026-10-20T12:00:00Z'),
 row('three','Frozen Store','SUSPENDED','2026-10-26T12:00:00Z'),
 row('four','Unknown Date','ACTIVE',null),
 row('five','Healthy Store','ACTIVE','2026-12-01T12:00:00Z'),
]
test('classifies and counts only the loaded page without making global totals',()=>{
 const h=buildSubscriptionHealth(rows,now)
 assert.deepEqual([h.expiring,h.expired,h.suspended,h.unknown],[1,1,1,1])
 assert.equal(h.rows.length,5)
 assert.equal(h.rows.find(x=>x.id==='five').status,'healthy')
 assert.equal(filterSubscriptionHealth(h.rows,'expiring').length,1)
 assert.equal(filterSubscriptionHealth(h.rows,'all','renew').length,1)
 assert.equal(filterSubscriptionHealth(h.rows,'all','no match').length,0)
})
test('suspended supersedes due-soon and missing dates are not guessed',()=>{
 assert.equal(classifySubscription(rows[2],now),'suspended')
 assert.equal(classifySubscription(rows[3],now),'unknown')
 assert.equal(classifySubscription({subscription_status:'EXPIRED'},now),'expired')
 assert.throws(()=>buildSubscriptionHealth(null,now))
})
