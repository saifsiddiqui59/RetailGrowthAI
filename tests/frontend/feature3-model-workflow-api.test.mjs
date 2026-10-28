import test from 'node:test'
import assert from 'node:assert/strict'
import {randomUUID} from 'node:crypto'
import {createFeature3ModelWorkflowApi} from '../../frontend/src/features/creative/feature3-model-workflow-api.mjs'
const shop=randomUUID(),model=randomUUID(),media=randomUUID(),event=randomUUID()
const checks={adult_synthetic:true,likeness_and_consent:true,image_license:true,
 private_media_integrity:true,visual_quality:true,approved_uses:true}
const imported={shop_id:shop,model_id:model,media_asset_id:media,status:'PENDING_REVIEW',rights_revision:1,
 rights_verified:false,evidence_verified:false,gpu_authorized:false,generation_executed:false}
const newModel={model_id:model,media_asset_id:media,source_kind:'retailer_licensed',label:'Fictional studio model',
 image_sha256:'a'.repeat(64),license_id:'REVIEWED-COMMERCIAL',license_evidence_sha256:'b'.repeat(64),
 attribution:'Test-only fictional source',approved_uses:['poster','video_reference']}
const review={decision:'APPROVE',expected_revision:1,image_sha256:'a'.repeat(64),
 evidence_revision:1,checks,notes:'Human-reviewed fictional model source'}
function api(receipt,opts={}) {
 let calls=[]
 const client=createFeature3ModelWorkflowApi({baseUrl:'https://example.test',tokenProvider:opts.tokenProvider||(()=> 'test-jwt'),
  fetchImpl:async(url,options)=>{calls.push({url,options});if(opts.fail)throw Error('503 timeout')
   return {ok:opts.status===undefined,status:opts.status||200,json:async()=>receipt}
  }})
 return {client,calls}
}
test('pending-only signed import preserves no-GPU and exact payload',async()=>{
 const {client,calls}=api(imported);const result=await client.importPendingModel(shop,newModel)
 assert.equal(result.status,'PENDING_REVIEW');assert.equal(result.gpu_authorized,false)
 assert.equal(calls.length,1);assert.match(calls[0].url,/feature3-models\/import$/)
 assert.equal(calls[0].options.redirect,'error')
 assert.equal(calls[0].options.headers.Authorization,'Bearer test-jwt')
 assert.deepEqual(Object.keys(JSON.parse(calls[0].options.body)).sort(),Object.keys(newModel).sort())
})
test('import denied forged approval or raw Storage pointer before HTTP',async()=>{
 const {client,calls}=api(imported)
 await assert.rejects(client.importPendingModel(shop,{...newModel,status:'APPROVED'}))
 await assert.rejects(client.importPendingModel(shop,{...newModel,object_path:'foreign/shop.png'}))
 assert.equal(calls.length,0)
})
test('import receipt with approved flag denied',async()=>{
 const {client}=api({...imported,rights_verified:true})
 await assert.rejects(client.importPendingModel(shop,newModel),/Untrusted/)
})
test('signed six-check reviewer approval emits durable audit only',async()=>{
 const receipt={shop_id:shop,model_id:model,status:'APPROVED',rights_revision:2,
  review_event_id:event,audit_persisted:true,gpu_enabled:false,generation_executed:false}
 const {client,calls}=api(receipt);const result=await client.reviewModel(shop,model,review)
 assert.equal(result.rights_revision,2);assert.equal(result.gpu_enabled,false)
 assert.equal(calls.length,1);assert.match(calls[0].url,/review$/)
 assert.deepEqual(JSON.parse(calls[0].options.body).checks,checks)
})
test('unverified check cannot approve and cannot dispatch',async()=>{
 const {client,calls}=api(null)
 await assert.rejects(client.reviewModel(shop,model,{...review,checks:{...checks,image_license:false}}))
 await assert.rejects(client.reviewModel(shop,model,{...review,checks:{...checks,wrong:true}}))
 assert.equal(calls.length,0)
})
test('explicit rejection records failed check and no spend',async()=>{
 const receipt={shop_id:shop,model_id:model,status:'REJECTED',rights_revision:2,
  review_event_id:event,audit_persisted:true,gpu_enabled:false,generation_executed:false}
 const {client}=api(receipt)
 const result=await client.reviewModel(shop,model,{...review,decision:'REJECT',checks:{...checks,visual_quality:false}})
 assert.equal(result.status,'REJECTED')
})
test('revocation uses signed exact current revision and reason',async()=>{
 const receipt={shop_id:shop,model_id:model,status:'REVOKED',rights_revision:4,
  review_event_id:event,audit_persisted:true,gpu_enabled:false,generation_executed:false}
 const {client,calls}=api(receipt)
 const result=await client.revokeModel(shop,model,{expected_revision:3,image_sha256:'a'.repeat(64),
  reason:'Source commercial rights have been withdrawn'})
 assert.equal(result.status,'REVOKED');assert.match(calls[0].url,/revoke$/)
})
test('foreign or inconsistent durable review receipt denied',async()=>{
 const {client}=api({shop_id:randomUUID(),model_id:model,status:'APPROVED',rights_revision:2,
  review_event_id:event,audit_persisted:true,gpu_enabled:false,generation_executed:false})
 await assert.rejects(client.reviewModel(shop,model,review),/Untrusted/)
})
test('expired session denied before any HTTP call',async()=>{
 const {client,calls}=api(imported,{tokenProvider:()=>''})
 await assert.rejects(client.importPendingModel(shop,newModel),/sign in/)
 assert.equal(calls.length,0)
})
test('browser cannot substitute service or publishable project keys for signed user',async()=>{
 for(const key of ['sb_secret_fake','sb_publishable_fake']){
  const {client,calls}=api(imported,{tokenProvider:()=>key})
  await assert.rejects(client.importPendingModel(shop,newModel),/sign in/)
  assert.equal(calls.length,0)
 }
})
test('ambiguous 409 or 503 POST does not retry',async()=>{
 for(const opt of [{status:409},{fail:true}]) {
  const {client,calls}=api(null,opt)
  await assert.rejects(client.importPendingModel(shop,newModel))
  assert.equal(calls.length,1)
 }
})
test('untrusted base URLs cannot direct JWT to alternative origin',()=>{
 for(const baseUrl of ['http://example.test','https://example.test/path','https://user@example.test','https://example.test/?token=x']){
  assert.throws(()=>createFeature3ModelWorkflowApi({baseUrl,tokenProvider:()=> 'test'}))
 }
})

const sourceRegistration={model_id:model,image_sha256:'a'.repeat(64),
 license_name:'owned',license_url:null,attribution:'Fictional adult model generated by our own team'}
test('signed original media registration is unverified and never GPU-authorized',async()=>{
 const receipt={shop_id:shop,model_id:model,media_asset_id:media,
  image_sha256:'a'.repeat(64),registered:true,byte_sha_verified:false,
  license_verified:false,status:'SOURCE_REGISTERED_PENDING_EVIDENCE',gpu_authorized:false}
 const {client,calls}=api(receipt)
 const result=await client.registerModelOriginal(shop,sourceRegistration)
 assert.equal(result.registered,true); assert.equal(result.license_verified,false)
 assert.equal(calls.length,1)
 assert.match(calls[0].url,/feature3-model-originals\/register$/)
 assert.equal(calls[0].options.headers.Authorization,'Bearer test-jwt')
 assert.deepEqual(JSON.parse(calls[0].options.body),sourceRegistration)
})
test('original registration cannot self-certify rights, change shop or send raw object paths',async()=>{
 const receipt={shop_id:shop,model_id:model,media_asset_id:media,
  image_sha256:'a'.repeat(64),registered:true,byte_sha_verified:true,
  license_verified:true,status:'SOURCE_REGISTERED_PENDING_EVIDENCE',gpu_authorized:true}
 const {client,calls}=api(receipt)
 await assert.rejects(client.registerModelOriginal(shop,sourceRegistration),/Untrusted/)
 assert.equal(calls.length,1)
 for(const invalid of [
  {...sourceRegistration,object_path:'foreign/private'},
  {...sourceRegistration,license_name:'cc0',license_url:null},
  {...sourceRegistration,image_sha256:'bad'},
 ])await assert.rejects(client.registerModelOriginal(shop,invalid))
 assert.equal(calls.length,1)
})
