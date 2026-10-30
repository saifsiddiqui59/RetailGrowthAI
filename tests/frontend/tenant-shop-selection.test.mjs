import test from 'node:test'
import assert from 'node:assert/strict'
import { selectionKey, readShopPreference, authorizedShopId, saveShopPreference } from '../../frontend/src/features/dashboard/tenant-shop-selection.mjs'

const OWNER = 'a9000000-0000-4000-8000-000000000001'
const OTHER_USER = 'a9000000-0000-4000-8000-000000000002'
const SHOP_A = 'a1000000-0000-4000-8000-000000000001'
const SHOP_B = 'a1000000-0000-4000-8000-000000000002'
const list = [
  { id: SHOP_A, membership:{ active: true, role: 'OWNER' }},
  { id: SHOP_B, membership:{ active: true, role: 'VIEWER' }},
]
test('session preference is isolated by principal, never by an account email', () => {
  const stored = new Map()
  const storage = { getItem:k=>stored.get(k) || null, setItem:(k,v)=>stored.set(k,v) }
  assert.ok(selectionKey(OWNER).includes(OWNER))
  assert.equal(selectionKey('anything-else'),'')
  assert.equal(saveShopPreference(OWNER,list,SHOP_B,storage),true)
  assert.equal(readShopPreference(OWNER,storage),SHOP_B)
  assert.equal(readShopPreference(OTHER_USER,storage),'')
})
test('unverified, inactive, removed, and forged selections always fall back to RLS list', () => {
  assert.equal(authorizedShopId(list,SHOP_B), SHOP_B)
  assert.equal(authorizedShopId(list,'a1000000-0000-4000-8000-000000000003'),SHOP_A)
  assert.equal(authorizedShopId([],SHOP_B),'')
  assert.equal(authorizedShopId(null,SHOP_B),'')
  const revoked=list.map(row=>({...row,membership:{active:false,role:'OWNER'}}))
  assert.equal(authorizedShopId(revoked,SHOP_A),'')
  const rogue={...list[0], membership:{ active:true, role:'PLATFORM_ADMIN' }}
  assert.equal(authorizedShopId([rogue],SHOP_A),'')
  const bad={getItem:()=>SHOP_B,setItem:()=>{throw Error('storage disabled')}}
  assert.equal(readShopPreference(OWNER,bad),SHOP_B)
  assert.equal(saveShopPreference(OWNER,list,SHOP_A,bad),true)
  assert.equal(saveShopPreference(OWNER,list,'invalid',bad),false)
  assert.equal(saveShopPreference(OWNER,[list[0]],SHOP_B,bad),false)
})
test('storage failures do not block a valid selection', () => {
  assert.equal(readShopPreference(OWNER,{getItem(){throw Error('blocked')}}),'')
  assert.equal(saveShopPreference(OWNER,list,SHOP_B,{setItem(){throw Error('blocked')}}),true)
})
