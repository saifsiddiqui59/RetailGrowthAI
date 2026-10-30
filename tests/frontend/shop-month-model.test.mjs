import test from 'node:test'
import assert from 'node:assert/strict'
import {checkedMonth, verifiedShopMonthRows} from '../../frontend/src/features/dashboard/shop-month-model.mjs'

const SHOP='a1000000-0000-4000-8000-000000000001'
const OTHER='a1000000-0000-4000-8000-000000000002'
const C1='c1000000-0000-4000-8000-000000000001'
const C2='c1000000-0000-4000-8000-000000000002'
const first={id:'d1000000-0000-4000-8000-000000000001',campaign_id:C1,
  shop_id:SHOP,scheduled_date:'2026-10-02',topic:'New arrivals',review_status:'DRAFT'}
const second={...first,id:'d1000000-0000-4000-8000-000000000002',
  campaign_id:C2,scheduled_date:'2026-10-01',topic:'Weekend sale',review_status:'APPROVED'}

test('month range is UTC bounded with December and leap rollover',()=>{
  assert.deepEqual(checkedMonth('2026-12'),{start:'2026-12-01',end:'2027-01-01'})
  assert.deepEqual(checkedMonth('2028-02'),{start:'2028-02-01',end:'2028-03-01'})
  for (const m of ['bad','2026-00','2026-13','1999-12','2100-01','2026-2'])
    assert.throws(()=>checkedMonth(m))
})
test('two same-tenant campaigns sort and preserve distinct reviewed-but-unpublished status',()=>{
  const rows=verifiedShopMonthRows([first,second],SHOP,'2026-10')
  assert.deepEqual(rows.map(x=>x.campaign_id),[C2,C1])
  assert.deepEqual(rows.map(x=>x.review_status),['APPROVED','DRAFT'])
})
test('fail closed on cross-business, missing scope, invalid dates, invalid statuses and overflow',()=>{
  const bad=[
    {...first,shop_id:OTHER},{...first,scheduled_date:'2026-11-01'},
    {...first,scheduled_date:'2026-10-99'},{...first,scheduled_date:'2026-10-00'},
    {...first,scheduled_date:'2026-10-32'},
    {...first,topic:''},{...first,review_status:'PUBLISHED'},
    {...first,id:'unsafe'}
  ]
  for(const row of bad) assert.throws(()=>verifiedShopMonthRows([first,row],SHOP,'2026-10'))
  assert.throws(()=>verifiedShopMonthRows([first],'not-a-shop','2026-10'))
  assert.throws(()=>verifiedShopMonthRows(Array(201).fill(first),SHOP,'2026-10'))
})
