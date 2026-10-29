import test from 'node:test'
import assert from 'node:assert/strict'
import {randomUUID} from 'node:crypto'
import {readFileSync} from 'node:fs'
import {createFeature3GeneratedBlobScope} from '../../frontend/src/features/creative/feature3-generated-blob-scope.mjs'

const SHOP=randomUUID(), OTHER=randomUUID(), JOB=randomUUID(), MEDIA=randomUUID()
const png=new Blob([new Uint8Array(160).fill(8)],{type:'image/png'})
const RECEIPT=Object.freeze({shopId:SHOP,jobId:JOB,mediaAssetId:MEDIA,
  imageSha256:'a'.repeat(64),blob:png,private:true,
  publishApproved:false,approvedModel:false})

function fixture(){
  const opened=[],revoked=[]
  const scope=createFeature3GeneratedBlobScope({
    createURL:()=>{const url='blob:https://fixture.test/'+randomUUID();opened.push(url);return url},
    revokeURL:url=>revoked.push(url),
  })
  return {scope,opened,revoked}
}
test('strict local Blob owner scope and revoke on account switch',()=>{
  const {scope,opened,revoked}=fixture()
  scope.selectScope(SHOP)
  const url=scope.install(SHOP,JOB,RECEIPT)
  assert.equal(opened.length,1)
  assert.equal(scope.view(SHOP,JOB),url)
  assert.equal(scope.view(OTHER,JOB),null)
  assert.equal(scope.view(SHOP,randomUUID()),null)
  scope.selectScope(OTHER)
  assert.deepEqual(revoked,[url])
  assert.equal(scope.view(SHOP,JOB),null)
  scope.clear()
  assert.equal(revoked.length,1)
})
test('replacing or clearing private image releases prior browser URL only once',()=>{
  const {scope,opened,revoked}=fixture()
  scope.selectScope(SHOP)
  const first=scope.install(SHOP,JOB,RECEIPT)
  const second=scope.install(SHOP,JOB,RECEIPT)
  assert.notEqual(first,second)
  assert.deepEqual(revoked,[first])
  scope.clear()
  scope.clear()
  assert.deepEqual(revoked,[first,second])
  assert.equal(scope.view(SHOP,JOB),null)
  assert.equal(opened.length,2)
})
test('foreign, forged publish status, signed Storage URL and stale scope never allocate Blob',()=>{
  const {scope,opened}=fixture()
  scope.selectScope(SHOP)
  const bad=[
    {...RECEIPT,shopId:OTHER},
    {...RECEIPT,jobId:randomUUID()},
    {...RECEIPT,mediaAssetId:'../foreign'},
    {...RECEIPT,imageSha256:'not-sha'},
    {...RECEIPT,publishApproved:true},
    {...RECEIPT,approvedModel:true},
    {...RECEIPT,private:false},
    {...RECEIPT,blob:new Blob(['hello'],{type:'text/html'})},
    {...RECEIPT,url:'https://fake-signed.invalid/'},
    {...RECEIPT,signedURL:'https://fake-signed.invalid/'},
    {...RECEIPT,objectPath:'other-shop/secret.png'},
  ]
  for(const x of bad) assert.throws(()=>scope.install(SHOP,JOB,x))
  scope.selectScope(OTHER)
  assert.throws(()=>scope.install(SHOP,JOB,RECEIPT))
  assert.equal(opened.length,0)
  assert.equal(scope.view(SHOP,JOB),null)
})
test('malicious external URL returned by URL factory never displays',()=>{
  const scope=createFeature3GeneratedBlobScope({
    createURL:()=> 'https://evil.example/storage/object',
    revokeURL:()=>{throw Error('must not revoke unrelated external URL')},
  })
  scope.selectScope(SHOP)
  assert.throws(()=>scope.install(SHOP,JOB,RECEIPT))
  assert.equal(scope.view(SHOP,JOB),null)
})
test('generated preview remains OFF by default until independent binary gate',()=>{
  const host=readFileSync(
    new URL('../../frontend/src/features/creative/Feature3PosterHost.jsx',import.meta.url),'utf8')
  const history=readFileSync(
    new URL('../../frontend/src/features/creative/Feature3GeneratedHistory.jsx',import.meta.url),'utf8')
  assert.match(host,/VITE_FEATURE3_PRIVATE_BINARY_ENABLED.*==='true'/)
  assert.match(history,/job\.status==='SUCCEEDED'/)
  assert.match(history,/Preview privately/)
  assert.match(history,/Clear private preview/)
  assert.match(history,/registry\.current\.clear\(\)/)
  assert.doesNotMatch(history,/getGeneratedImageDownload\(/)
})
