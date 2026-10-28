import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { createFeature3Api } from '../../frontend/src/features/creative/feature3-api.mjs'

const sid='a1000000-0000-4000-8000-000000000001'
const jid='a1000000-0000-4000-8000-000000000004'
const aid='a1000000-0000-4000-8000-000000000005'
const store='https://dev.supabase.co'
const signed=store+'/storage/v1/object/sign/retailgrowth-media/'+sid+
  '/feature3/gpu/'+jid+'/'+'a'.repeat(64)+'.png?token=short-lived-secret'
function setup(response,options={}) {
  const calls=[]
  const api=createFeature3Api({
    baseUrl:'https://campaign.invalid',signedStorageOrigin:store,
    tokenProvider:async()=> 'valid-user',
    fetchImpl:async(url,request)=>{
      calls.push({url,request})
      return {ok:true,status:200,json:async()=>response}
    },...options,
  })
  return {api,calls}
}
test('JWT-scoped history is only read and cannot activate GPU',async()=>{
  const {api,calls}=setup({shop_id:sid,gpu_submission_enabled:false,
    jobs:[{id:jid,shop_id:sid,status:'SUCCEEDED'}]})
  assert.equal((await api.listGeneratedJobs(sid))[0].id,jid)
  assert.equal(calls.length,1)
  assert.equal(calls[0].request.method,'GET')
  assert.equal(calls[0].request.headers.Authorization,'Bearer valid-user')
  assert.ok(!('body' in calls[0].request))
  await assert.rejects(api.listGeneratedJobs('bogus'))
})
test('download requires exact 60-second same-shop signed image path',async()=>{
  const receipt={job_id:jid,media_asset_id:aid,expires_in_seconds:60,
    approved_model:false,url:signed}
  const {api,calls}=setup(receipt)
  const link=await api.getGeneratedImageDownload(sid,jid)
  assert.equal(link.mediaAssetId,aid)
  assert.equal(link.url,signed)
  assert.equal(link.approvedModel,false)
  assert.equal(calls.length,1)
  assert.match(calls[0].url,/feature3-gpu-jobs/)
})
test('reject forged foreign origin, job path, query, status and publisher approval',async()=>{
  const original={job_id:jid,media_asset_id:aid,expires_in_seconds:60,
    approved_model:false,url:signed}
  for (const change of [
    {url:signed.replace(store,'https://attacker.invalid')},
    {url:signed.replace(jid,'a1000000-0000-4000-8000-000000000099')},
    {url:signed+'&public=true'},
    {url:signed.replace('/feature3/gpu/','/public/gpu/')},
    {expires_in_seconds:3600},
    {approved_model:true},
    {media_asset_id:'foreign'},
  ]) {
    const {api,calls}=setup({...original,...change})
    await assert.rejects(api.getGeneratedImageDownload(sid,jid),/Untrusted/)
    assert.equal(calls.length,1)
  }
})
test('no download request without explicit secure Storage origin',async()=>{
  const {api,calls}=setup({}, {signedStorageOrigin:null})
  await assert.rejects(api.getGeneratedImageDownload(sid,jid),
                       /Storage origin required/)
  assert.equal(calls.length,0)
})
test('the v2 UI compiles and displays private success-only download controls',async()=>{
  const req=createRequire(new URL('../../frontend/package.json',import.meta.url))
  const {transformWithEsbuild}=await import(req.resolve('vite'))
  const uri=new URL('../../frontend/src/features/creative/Feature3SecureDraftWorkspace.jsx',
                    import.meta.url)
  const contents=await readFile(uri,'utf8')
  await transformWithEsbuild(contents,'Feature3SecureDraftWorkspace.jsx',{loader:'jsx'})
  assert.match(contents,/listGeneratedJobs\(shopId\)/)
  assert.match(contents,/provider[.]getGeneratedImageDownload\(scope,jobId\)/)
  assert.match(contents,/job.status==='SUCCEEDED'/)
  assert.match(contents,/not approved for publishing/)
})

test('short-lived private URL disappears on shop, day, revision or expiration mismatch',async()=>{
  const {scopedFeature3GeneratedLink,SAFE_CLIENT_LIFETIME_MS}=await import(
    '../../frontend/src/features/creative/feature3-signed-link-scope.mjs')
  const now=1000000, requestKey=sid+'|campaign|day'
  const item={scope:sid,requestKey,jobId:jid,mediaAssetId:aid,url:signed,
    createdAt:now,expiresInSeconds:60,approvedModel:false}
  assert.equal(scopedFeature3GeneratedLink(item,sid,now,requestKey),item)
  assert.equal(scopedFeature3GeneratedLink(item,'b1000000-0000-4000-8000-000000000001',now,requestKey),null)
  assert.equal(scopedFeature3GeneratedLink(item,sid,now,requestKey+'-other'),null)
  assert.equal(scopedFeature3GeneratedLink(item,sid,now+SAFE_CLIENT_LIFETIME_MS,requestKey),null)
  assert.equal(scopedFeature3GeneratedLink({...item,approvedModel:true},sid,now,requestKey),null)
  assert.equal(scopedFeature3GeneratedLink({...item,expiresInSeconds:3600},sid,now,requestKey),null)
  assert.equal(scopedFeature3GeneratedLink({...item,createdAt:now+100},sid,now,requestKey),null)
})
test('Creative Studio refuses to display stale signed URL during render or delayed JWT response',async()=>{
  const file=new URL('../../frontend/src/features/creative/Feature3SecureDraftWorkspace.jsx',import.meta.url)
  const contents=await readFile(file,'utf8')
  assert.match(contents,/visibleGeneratedLink && <a/)
  assert.match(contents,/pendingDownload.current/)
  assert.match(contents,/activeScope.current.shopId===scope/)
  assert.match(contents,/scopedFeature3GeneratedLink\(/)
  const req=createRequire(new URL('../../frontend/package.json',import.meta.url))
  const {transformWithEsbuild}=await import(req.resolve('vite'))
  await transformWithEsbuild(contents,'Feature3SecureDraftWorkspace.jsx',{loader:'jsx'})
})
