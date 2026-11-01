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

test('duplicate URL factory result never revokes or displays a stale replacement',()=>{
  const existing='blob:https://fixture.test/same'
  const revoked=[]
  const scope=createFeature3GeneratedBlobScope({
    createURL:()=>existing,
    revokeURL:url=>revoked.push(url),
  })
  scope.selectScope(SHOP)
  assert.equal(scope.install(SHOP,JOB,RECEIPT),existing)
  assert.throws(()=>scope.install(SHOP,JOB,RECEIPT),/must be fresh/)
  assert.equal(scope.view(SHOP,JOB),existing)
  assert.deepEqual(revoked,[])
  scope.clear()
  assert.deepEqual(revoked,[existing])
})

test('failed old Blob revocation cannot publish or retain the new private preview',()=>{
  const allocated=[],revoked=[]
  const scope=createFeature3GeneratedBlobScope({
    createURL:()=>{
      const url='blob:https://fixture.test/'+randomUUID()
      allocated.push(url)
      return url
    },
    revokeURL:url=>{
      if(url===allocated[0]) throw Error('simulated browser revocation failure')
      revoked.push(url)
    },
  })
  scope.selectScope(SHOP)
  const first=scope.install(SHOP,JOB,RECEIPT)
  assert.equal(scope.view(SHOP,JOB),first)
  assert.throws(()=>scope.install(SHOP,JOB,RECEIPT),/replacement cleanup failed/)
  assert.equal(allocated.length,2)
  assert.deepEqual(revoked,[allocated[1]])
  assert.equal(scope.view(SHOP,JOB),null)
  // The failed old URL is hidden but remains owned for a bounded retry.
  assert.throws(()=>scope.clear(),/cleanup failed/)
  assert.deepEqual(revoked,[allocated[1]])
})

test('failed browser image decode discards only the precise current Blob and never an in-flight successor',()=>{
  const {scope,opened,revoked}=fixture()
  scope.selectScope(SHOP)
  const first=scope.install(SHOP,JOB,RECEIPT)
  assert.equal(scope.discardFailed(OTHER,JOB,first),false)
  assert.equal(scope.discardFailed(SHOP,randomUUID(),first),false)
  assert.equal(scope.discardFailed(SHOP,JOB,'blob:https://foreign.test/1'),false)
  assert.deepEqual(revoked,[])
  const second=scope.install(SHOP,JOB,RECEIPT)
  assert.deepEqual(revoked,[first])
  assert.equal(scope.discardFailed(SHOP,JOB,first),false)
  assert.equal(scope.view(SHOP,JOB),second)
  assert.equal(scope.discardFailed(SHOP,JOB,second),true)
  assert.equal(scope.discardFailed(SHOP,JOB,second),false)
  assert.deepEqual(revoked,[first,second])
  assert.equal(opened.length,2)
  assert.equal(scope.view(SHOP,JOB),null)
})
test('decode failure callback is bound to the exact private generated URL',()=>{
  const history=readFileSync(
    new URL('../../frontend/src/features/creative/Feature3GeneratedHistory.jsx',import.meta.url),'utf8')
  assert.match(history,/onError=\{\(\)=>\{/)
  assert.match(history,/registry\.current\.discardFailed\(displayed\.shopId,displayed\.jobId,displayed\.url\)/)
  assert.match(history,/setImage\(null\)/)
  assert.match(history,/Local image was discarded/)
  assert.doesNotMatch(history,/onError=\{clearImage\}/)
})

test('failed URL revocation retains hidden private URLs for cleanup after browser recovery',()=>{
  const issued=[],revoked=[],deny=new Set()
  const scope=createFeature3GeneratedBlobScope({
    createURL:()=>{
      const url='blob:https://fixture.test/'+randomUUID()
      issued.push(url)
      return url
    },
    revokeURL:url=>{
      if(deny.has(url))throw Error('browser revoke temporarily failed')
      revoked.push(url)
    },
  })
  scope.selectScope(SHOP)
  const first=scope.install(SHOP,JOB,RECEIPT)
  deny.add(first)
  assert.throws(()=>scope.selectScope(OTHER),/cleanup failed/)
  // Scope switches are denied until the hidden URL can be revoked.
  assert.equal(scope.view(SHOP,JOB),null)
  assert.equal(scope.view(OTHER,JOB),null)
  assert.throws(()=>scope.install(SHOP,JOB,RECEIPT))
  deny.delete(first)
  scope.selectScope(OTHER)
  assert.deepEqual(revoked,[first])
  assert.equal(scope.view(SHOP,JOB),null)
  scope.selectScope(SHOP)
  const second=scope.install(SHOP,JOB,RECEIPT)
  assert.notEqual(second,first)
  scope.clear()
  assert.deepEqual(revoked,[first,second])
})

test('two failed revocations from a replacement stay hidden until a later retry',()=>{
  const issued=[],revoked=[],deny=new Set()
  const scope=createFeature3GeneratedBlobScope({
    createURL:()=>{
      const url='blob:https://fixture.test/'+randomUUID()
      issued.push(url)
      return url
    },
    revokeURL:url=>{
      if(deny.has(url))throw Error('revoke temporary failure')
      revoked.push(url)
    },
  })
  scope.selectScope(SHOP)
  const first=scope.install(SHOP,JOB,RECEIPT)
  deny.add(first)
  // Fail revocation of the next allocated URL too, even on the error path.
  const issue=()=>{const url='blob:https://fixture.test/'+randomUUID();issued.push(url);deny.add(url);return url}
  // Fresh scope supports injectable factories; exercise both failures
  // in a separately scoped instance with the same failure mechanism.
  const other=createFeature3GeneratedBlobScope({createURL:issue,revokeURL:url=>{
    if(deny.has(url))throw Error('revoke temporary failure')
    revoked.push(url)
  }})
  other.selectScope(OTHER)
  const old=other.install(OTHER,JOB,{...RECEIPT,shopId:OTHER})
  assert.throws(()=>other.install(OTHER,JOB,{...RECEIPT,shopId:OTHER}),
    /replacement cleanup failed/)
  const failedNext=issued[issued.length-1]
  assert.equal(other.view(OTHER,JOB),null)
  assert.equal(revoked.includes(old),false)
  assert.equal(revoked.includes(failedNext),false)
  // A previously owned pending URL must not be reused as a fresh preview.
  deny.delete(old);deny.delete(failedNext)
  other.clear()
  assert.equal(revoked.filter(url=>url===old).length,1)
  assert.equal(revoked.filter(url=>url===failedNext).length,1)
  assert.equal(other.view(OTHER,JOB),null)
  deny.delete(first)
  scope.clear()
})
