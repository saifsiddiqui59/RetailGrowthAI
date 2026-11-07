import test from 'node:test'
import assert from 'node:assert/strict'
import {readFile} from 'node:fs/promises'
import {createRequire} from 'node:module'
import {createFeature3ReviewSnapshot} from '../../frontend/src/features/creative/feature3-review-snapshot.mjs'

const shop='a1000000-0000-4000-8000-000000000001'
const campaign='a1000000-0000-4000-8000-000000000002'
const day='a1000000-0000-4000-8000-000000000003'
const design={
  schema:'retailgrowth.poster.v2',shop_id:shop,format:'portrait',
  template:'fashion',background:'#FFFFFF',
  layers:[
    {id:'headline',type:'text',x:.1,y:.08,w:.8,h:.15,
      text:'New arrivals',color:'#222222',font_size:32,bold:true},
    {id:'image-one',type:'image',x:.1,y:.35,w:.8,h:.48,asset_id:'owned-asset'},
  ],
}
const row={id:'a1000000-0000-4000-8000-000000000004',shop_id:shop,
  campaign_id:campaign,day_id:day,status:'APPROVED',revision:3,
  server_document_sha256:'a'.repeat(64),design,
}
const decoded={complete:true,naturalWidth:320,naturalHeight:480,
  src:'https://untrusted.invalid/SHOULD-NOT-APPEAR'}
const scope={shopId:shop,campaignId:campaign,dayId:day,imageMap:{'owned-asset':decoded}}
test('F3-09 review snapshot is immutable read-only structured data without media URLs',()=>{
  const snap=createFeature3ReviewSnapshot(row,scope)
  assert.equal(snap.status,'APPROVED')
  assert.equal(snap.publicationApproved,false)
  assert.equal(snap.commercialRightsVerified,false)
  assert.deepEqual([snap.width,snap.height],[1080,1350])
  assert.equal(Object.isFrozen(snap),true)
  assert.equal(Object.isFrozen(snap.layers),true)
  assert.ok(snap.layers.every(Object.isFrozen))
  assert.ok(JSON.stringify(snap).includes('New arrivals'))
  assert.ok(!JSON.stringify(snap).includes('untrusted.invalid'))
  assert.equal(snap.layers[1].mediaLabel,'Private registered asset owned-as')
  assert.equal('asset_id' in snap.layers[1],false)
  assert.equal('src' in snap.layers[1],false)
})
test('F3-09 two-shop, changed day, foreign image grant and forged schema fail closed',()=>{
  const foreign='b1000000-0000-4000-8000-000000000001'
  const bad=[
    [row,{...scope,shopId:foreign}],
    [row,{...scope,dayId:foreign}],
    [{...row,shop_id:foreign},scope],
    [{...row,revision:0},scope],
    [{...row,status:'PUBLISHED'},scope],
    [{...row,design:{...design,shop_id:foreign}},scope],
    [{...row,design:{...design,publishApproved:true}},scope],
    [{...row,design:{...design,layers:[{...design.layers[1],url:'https://attacker.invalid'}]}},scope],
    [row,{...scope,imageMap:{}}],
    [row,{...scope,imageMap:Object.create({'owned-asset':decoded})}],
  ]
  for(const [item,ctx] of bad){
    assert.throws(()=>createFeature3ReviewSnapshot(item,ctx))
  }
  assert.throws(()=>createFeature3ReviewSnapshot(null,scope))
  assert.throws(()=>createFeature3ReviewSnapshot(row,{}))
})
test('F3-09 text-only reviewed drafts render without private image grants',()=>{
  const textOnly={...row,status:'REJECTED',design:{...design,layers:[design.layers[0]]}}
  const snap=createFeature3ReviewSnapshot(textOnly,{...scope,imageMap:{}})
  assert.equal(snap.status,'REJECTED')
  assert.equal(snap.layers.length,1)
  assert.equal(snap.layers[0].text,'New arrivals')
})
test('F3-09 inspector mounts only as read-only snapshot and clears on history refresh',async()=>{
  const root='../../frontend/src/features/creative/'
  const workspace=await readFile(new URL(root+'Feature3SecureDraftWorkspace.jsx',import.meta.url),'utf8')
  const component=await readFile(new URL(root+'Feature3ReadOnlyReview.jsx',import.meta.url),'utf8')
  const req=createRequire(new URL('../../frontend/package.json',import.meta.url))
  const {transformWithEsbuild}=await import(req.resolve('vite'))
  await transformWithEsbuild(component,'Feature3ReadOnlyReview.jsx',{loader:'jsx'})
  await transformWithEsbuild(workspace,'Feature3SecureDraftWorkspace.jsx',{loader:'jsx'})
  assert.match(workspace,/createFeature3ReviewSnapshot\(entry,/)
  assert.match(workspace,/saved\.some\(row=>row===entry\)/)
  assert.match(workspace,/scopedFeature3WorkspaceValue\(reviewState,scopeKey,null,feature3Api\)/)
  assert.match(workspace,/setReviewState\(\{scope,provider,value:null\}\)/)
  assert.match(workspace,/Inspect read-only/)
  assert.match(workspace,/Feature3ReadOnlyReview snapshot=\{inspected\}/)
  assert.doesNotMatch(component,/fetch\(|\.src=|<img|onSave|onApprove|onPublish|href=/)
  assert.match(component,/image withheld/)
  assert.match(component,/no image download, commercial rights/)
})
