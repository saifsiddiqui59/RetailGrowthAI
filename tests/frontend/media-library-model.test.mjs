import test from 'node:test'
import assert from 'node:assert/strict'
import { filterAssets, mediaLabel, mediaPreviewAccess, paginateVerifiedAssets } from '../../frontend/src/features/dashboard/media-library-model.mjs'

const OWN='a1000000-0000-4000-8000-000000000001'
const OTHER='a1000000-0000-4000-8000-000000000002'
const ID='a1000000-0000-4000-8000-000000000010'
const items=[
  { id:ID, shop_id:OWN, license_name:'owned', source:'UPLOAD', mime_type:'image/png' },
  { id:'a1000000-0000-4000-8000-000000000011', shop_id:OTHER, license_name:'owned', source:'UPLOAD', mime_type:'image/jpeg' },
  { id:'invalid',shop_id:OWN, license_name:'owned', source:'UPLOAD', mime_type:'image/png' },
  { id:'a1000000-0000-4000-8000-000000000012', shop_id:OWN, license_name:null, source:'UPLOAD', mime_type:'image/png' },
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

test('paging is bounded to the already tenant-filtered capped collection',()=>{
  const ownRows=Array.from({length:27},(_,i)=>({
    id:'a1000000-0000-4000-8000-'+String(i+100).padStart(12,'0'),
    shop_id:OWN, license_name:'owned', source:'UPLOAD', mime_type:'image/png'
  }))
  const filtered=filterAssets([...ownRows,items[1]],OWN)
  const first=paginateVerifiedAssets(filtered,1)
  const second=paginateVerifiedAssets(filtered,2)
  const last=paginateVerifiedAssets(filtered,3)
  assert.deepEqual([first.pages,first.first,first.last,first.items.length],[3,1,12,12])
  assert.deepEqual([second.first,second.last,second.items.length],[13,24,12])
  assert.deepEqual([last.first,last.last,last.items.length],[25,27,3])
  assert.equal(paginateVerifiedAssets(filtered,999).page,3)
  assert.equal(paginateVerifiedAssets(filtered,-1).page,1)
  assert.equal(paginateVerifiedAssets(filtered,2,100).items.length,12)
  assert.deepEqual(paginateVerifiedAssets([],2),{
    page:1,pages:1,total:0,first:0,last:0,items:[]
  })
  assert.ok(first.items.every(a=>a.shop_id===OWN))
  assert.equal(filtered.some(a=>a.shop_id===OTHER),false)
})


test('media preview adapter rejects STOCK/GENERATED, foreign tenant and invalid MIME',()=>{
 const own={id:ID,shop_id:OWN,license_name:'owner-declared',source:'UPLOAD',mime_type:'image/png'}
 assert.deepEqual(mediaPreviewAccess(own,OWN),{allowed:true,reason:'private-upload-only'})
 for(const source of ['STOCK','GENERATED']){
  assert.deepEqual(mediaPreviewAccess({...own,source},OWN),
   {allowed:false,reason:'rights-and-private-access-required'})
 }
 for(const asset of [
  {...own,shop_id:OTHER},{...own,source:'UNKNOWN'},
  {...own,mime_type:'image/svg+xml'},{...own,mime_type:'text/html'},
  {...own,license_name:' '},{...own,id:'invalid'}
 ])assert.equal(mediaPreviewAccess(asset,OWN).allowed,false)
 assert.equal(mediaPreviewAccess(own,OTHER).allowed,false)
 const records=[own,{...own,id:'a1000000-0000-4000-8000-000000000050',source:'STOCK'},
  {...own,id:'a1000000-0000-4000-8000-000000000051',source:'GENERATED'},
  {...own,id:'a1000000-0000-4000-8000-000000000052',mime_type:'text/html'},
  {...own,id:'a1000000-0000-4000-8000-000000000053',source:'UNKNOWN'}]
 assert.deepEqual(filterAssets(records,OWN).map(x=>x.source),['UPLOAD','STOCK','GENERATED'])
 assert.equal(filterAssets(records,OTHER).length,0)
})
