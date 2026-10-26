import test from 'node:test'
import assert from 'node:assert/strict'
import { recentCampaignHint, verifiedCampaignDays } from '../../frontend/src/features/dashboard/recent-calendar-model.mjs'

const S='a1000000-0000-4000-8000-000000000001'
const O='a1000000-0000-4000-8000-000000000002'
const U='a9000000-0000-4000-8000-000000000001'
const C='c1000000-0000-4000-8000-000000000001'
const D='d1000000-0000-4000-8000-000000000001'
test('session hint is scoped to verified tenant and user UUIDs',()=>{
  const storage={getItem:k=>k==='retailgrowthai-last-campaign:'+U+':'+S?C:null}
  assert.equal(recentCampaignHint(storage,U,S),C)
  assert.equal(recentCampaignHint(storage,U,O),'')
  assert.equal(recentCampaignHint(storage,'bad',S),'')
  assert.equal(recentCampaignHint({getItem(){throw Error('disabled')}},U,S),'')
})
test('calendar excludes foreign and invalid campaign days',()=>{
  const day={id:D,campaign_id:C,shop_id:S,scheduled_date:'2026-11-04',day_index:1,topic:'Festive styles',review_status:'DRAFT'}
  const c={id:C,shop_id:S,status:'DRAFT',days:[day,{...day,id:'d1000000-0000-4000-8000-000000000002',shop_id:O},{...day,id:'d1000000-0000-4000-8000-000000000003',topic:''}]}
  assert.deepEqual(verifiedCampaignDays(c,S),[day])
  assert.deepEqual(verifiedCampaignDays(c,O),[])
  assert.deepEqual(verifiedCampaignDays({...c,status:'PLANNING'},S),[])
})
