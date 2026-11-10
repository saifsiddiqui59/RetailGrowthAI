import test from 'node:test'
import assert from 'node:assert/strict'
import {normalizeSocialAccounts,normalizePublishingHistory,formatSchedule} from
 '../../frontend/src/features/dashboard/integration-read-model.mjs'
import {OFFLINE_SCENARIOS,offlineScenario} from
 '../../frontend/src/features/dashboard/feature1-offline-fixtures.mjs'

const shop=OFFLINE_SCENARIOS[0].id
const foreign=OFFLINE_SCENARIOS[1].id
const source=()=>offlineScenario(shop)

test('fully fictional apparel and grocery examples are tenant-scoped and clearly non-transport',()=>{
 for(const fixture of OFFLINE_SCENARIOS){
  const data=offlineScenario(fixture.id)
  const accounts=normalizeSocialAccounts(fixture.id,data.accounts)
  const receipts=normalizePublishingHistory(fixture.id,data.history)
  assert.ok(accounts.length>=3)
  assert.ok(receipts.length>=8)
  assert.ok(accounts.every(x=>!JSON.stringify(x).match(/access_token|refresh_token|client_secret/)))
  assert.ok(receipts.every(x=>x.receipt_id===null||x.receipt_id.startsWith('OFFLINE-RECEIPT-')))
  assert.ok(receipts.every(x=>x.status!=='PUBLISHED'||x.receipt_id))
  assert.ok(receipts.every(x=>x.status!=='FAILED'||x.failure_code))
 }
 assert.throws(()=>offlineScenario('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'),/Unknown offline/)
})
test('social account read fails closed on foreign tenant, credentials, unsupported status and forged scopes',()=>{
 const {accounts}=source()
 assert.equal(normalizeSocialAccounts(shop,accounts).length,4)
 for(const invalid of [
  [{...accounts[0],shop_id:foreign}],
  [{...accounts[0],access_token:'sensitive-should-not-render'}],
  [{...accounts[0],status:'FAKE_CONNECTED'}],
  [{...accounts[1],scopes:['publish_video']}],
  [accounts[0],accounts[0]],
  [{...accounts[0],verified_at:'not-an-instant'}]
 ])assert.throws(()=>normalizeSocialAccounts(shop,invalid),/could not be verified/)
 assert.throws(()=>normalizeSocialAccounts('bad',accounts),/could not be verified/)
 assert.throws(()=>normalizeSocialAccounts(shop,Array(21).fill(accounts[0])),/could not be verified/)
})
test('published receipts, timezone, states, status counts and bounded pages are not invented',()=>{
 const {history}=source()
 const parsed=normalizePublishingHistory(shop,history)
 assert.equal(parsed.length,26)
 assert.ok(parsed.every(x=>!x.receipt_id||x.status==='PUBLISHED'))
 assert.ok(parsed.every(x=>!x.failure_code||x.status==='FAILED'))
 assert.match(formatSchedule(history[0].scheduled_at,'Asia/Kolkata'),/Asia\/Kolkata/)
 assert.ok(parsed.every((x,i)=>i===0||x.scheduled_at<=parsed[i-1].scheduled_at))
 for(const forged of [
  [{...history[0],shop_id:foreign}],
  [{...history[0],provider:'unsupported'}],
  [{...history[0],timezone:'Mars/Phobos'}],
  [{...history[0],scheduled_at:'2026-10-28'}],
  [{...history[0],status:'PUBLISHED',receipt_id:null}],
  [{...history[0],receipt_id:'UNVERIFIED'}],
  [{...history[0],status:'FAILED',failure_code:null}],
  [{...history[0],attempts:-1}],
  [{...history[0],oauth_token:'blocked'}],
  [history[0],history[0]]
 ])assert.throws(()=>normalizePublishingHistory(shop,forged),/could not be verified/)
 assert.throws(()=>normalizePublishingHistory(shop,Array(101).fill(history[0])),/could not be verified/)
 assert.throws(()=>formatSchedule('wrong','Asia/Kolkata'),/could not be verified/)
})


test('invalid normalized UTC calendar dates, leap days and 24:00 are rejected for identities and receipts',()=>{
 const {accounts,history}=source()
 const malformed=[
  '2026-02-29T10:30:00Z','2026-02-31T10:30:00Z',
  '2026-04-31T10:30:00Z','2026-10-28T24:00:00Z',
  '2026-10-28T12:60:00Z','2026-10-28T12:30:60Z',
 ]
 for(const timestamp of malformed){
  assert.throws(()=>normalizeSocialAccounts(shop,[{...accounts[0],verified_at:timestamp}]),/could not be verified/)
  assert.throws(()=>normalizePublishingHistory(shop,[{...history[0],scheduled_at:timestamp}]),/could not be verified/)
  assert.throws(()=>formatSchedule(timestamp,'UTC'),/could not be verified/)
 }
 assert.equal(normalizeSocialAccounts(shop,[{...accounts[0],verified_at:'2028-02-29T10:30:00Z'}]).length,1)
 assert.equal(normalizePublishingHistory(shop,[{...history[0],scheduled_at:'2028-02-29T10:30:00.123Z'}]).length,1)
})

test('IANA DST overlap labels include actual UTC offset so two 01:30 events remain distinguishable',()=>{
 const first=formatSchedule('2026-11-01T05:30:00Z','America/New_York')
 const second=formatSchedule('2026-11-01T06:30:00Z','America/New_York')
 assert.match(first,/GMT-4/)
 assert.match(second,/GMT-5/)
 assert.ok(first.includes('America/New_York'))
 assert.ok(second.includes('America/New_York'))
 assert.notEqual(first,second)
 const springBefore=formatSchedule('2026-03-08T06:30:00Z','America/New_York')
 const springAfter=formatSchedule('2026-03-08T07:30:00Z','America/New_York')
 assert.match(springBefore,/GMT-5/)
 assert.match(springAfter,/GMT-4/)
})


test('third fictional restaurant covers disconnected accounts and all six post states without provider transport',()=>{
 const restaurant=OFFLINE_SCENARIOS.find(x=>x.name.includes('Bistro'))
 assert.ok(restaurant)
 const fixture=offlineScenario(restaurant.id)
 const identities=normalizeSocialAccounts(restaurant.id,fixture.accounts)
 const events=normalizePublishingHistory(restaurant.id,fixture.history)
 assert.equal(identities.length,5)
 assert.equal(identities.filter(x=>x.status==='DISCONNECTED').length,1)
 assert.deepEqual(identities.find(x=>x.status==='DISCONNECTED').scopes,[])
 assert.deepEqual(new Set(events.map(x=>x.status)),new Set([
  'SCHEDULED','QUEUED','PUBLISHING','PUBLISHED','FAILED','CANCELLED'
 ]))
 assert.ok(events.every(x=>x.status!=='PUBLISHED'||x.receipt_id?.startsWith('OFFLINE-RECEIPT-')))
 assert.ok(events.every(x=>x.status!=='PUBLISHING'||x.receipt_id===null))
 assert.throws(()=>normalizeSocialAccounts(shop,fixture.accounts),/could not be verified/)
 assert.throws(()=>normalizePublishingHistory(shop,fixture.history),/could not be verified/)
 assert.throws(()=>normalizeSocialAccounts(restaurant.id,[{
  ...fixture.accounts[4],scopes:['publish_video']
 }]),/could not be verified/)
})
