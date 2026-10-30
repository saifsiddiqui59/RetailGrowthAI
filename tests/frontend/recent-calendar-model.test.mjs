import test from 'node:test'
import assert from 'node:assert/strict'
import { recentCampaignHint, verifiedCampaignDays, verifiedDraftMonths, draftMonthCells } from '../../frontend/src/features/dashboard/recent-calendar-model.mjs'

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

test('calendar rejects impossible dates instead of normalizing to another month',()=>{
  const base={id:D,campaign_id:C,shop_id:S,scheduled_date:'2026-02-28',
    day_index:1,topic:'Winter styling',review_status:'DRAFT'}
  const campaign={id:C,shop_id:S,status:'DRAFT',days:[
    base,
    {...base,id:'d1000000-0000-4000-8000-000000000004',scheduled_date:'2026-02-31'},
    {...base,id:'d1000000-0000-4000-8000-000000000005',scheduled_date:'2026-02-29'}
  ]}
  assert.deepEqual(verifiedCampaignDays(campaign,S),[base])
  assert.equal(verifiedCampaignDays({...campaign,days:[{...base,scheduled_date:'2028-02-29'}]},S).length,1)
})

test('UTC Monday-first month grid groups only verified dates across month boundaries',()=>{
  const valid=[
    {scheduled_date:'2026-11-30'},
    {scheduled_date:'2026-12-01'},
    {scheduled_date:'2026-12-01'},
  ]
  assert.deepEqual(verifiedDraftMonths(valid),['2026-11','2026-12'])
  const cells=draftMonthCells(valid,'2026-12')
  assert.equal(cells.length,35)
  assert.deepEqual(cells[0],{date:'2026-11-30',day:30,inMonth:false,drafts:0})
  assert.deepEqual(cells[1],{date:'2026-12-01',day:1,inMonth:true,drafts:2})
  assert.equal(cells.at(-1).date,'2027-01-03')
  assert.equal(draftMonthCells(valid,'2026-13').length,0)
  assert.equal(draftMonthCells(valid,'bad').length,0)
  assert.deepEqual(verifiedDraftMonths([{scheduled_date:'2026-02-30'},null]),[])
})
