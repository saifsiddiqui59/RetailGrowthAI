import test from 'node:test'
import assert from 'node:assert/strict'
import { filterAssets, mediaLabel } from '../../frontend/src/features/dashboard/media-library-model.mjs'

const OWN='a1000000-0000-4000-8000-000000000001'
const OTHER='a1000000-0000-4000-8000-000000000002'
const ID='a1000000-0000-4000-8000-000000000010'
const items=[
  { id:ID, shop_id:OWN, license_name:'owned', mime_type:'image/png' },
  { id:'a1000000-0000-4000-8000-000000000011', shop_id:OTHER, license_name:'owned', mime_type:'image/jpeg' },
  { id:'invalid',shop_id:OWN, license_name:'owned', mime_type:'image/png' },
  { id:'a1000000-0000-4000-8000-000000000012', shop_id:OWN, license_name:null, mime_type:'image/png' },
]
test('media filtering never renders cross-tenant and unverified records',()=>{
  assert.deepEqual(filterAssets(items,OWN).map(row=>row.id),[ID])
  assert.deepEqual(filterAssets(items,OTHER).map(row=>row.id),[items[1].id])
  assert.deepEqual(filterAssets(items,OWN,'jpeg'),[])
  assert.deepEqual(filterAssets(items,OWN,'owned','image/jpeg'),[])
  assert.equal(filterAssets(items,'invalid').length,0)
  assert.equal(filterAssets(null,OWN).length,0)
  assert.match(mediaLabel(ID),/Image a1000000/)
  assert.equal(mediaLabel('bad'),'Image record')
})
