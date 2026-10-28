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
