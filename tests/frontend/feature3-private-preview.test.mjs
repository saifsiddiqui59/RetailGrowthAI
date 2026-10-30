import test from 'node:test'
import assert from 'node:assert/strict'
import {scopedFeature3Preview, discardFailedPrivateModelPreview} from '../../frontend/src/features/creative/feature3-private-preview.mjs'

const one='a1000000-0000-4000-8000-000000000001'
const two='b1000000-0000-4000-8000-000000000002'
test('Feature3 current tenant retains its own private decoded pixels', () => {
  const original={scope:one,models:[{model_id:'model-1'}],
    imageMap:{'asset-1':{secret:true}},busy:true,message:'shop one'}
  assert.strictEqual(scopedFeature3Preview(original,one),original)
})
test('shop switch hides all previous model media synchronously before effect cleanup', () => {
  const previous={scope:one,models:[{model_id:'model-1'}],
    imageMap:{'asset-1':{secret:true}},busy:true,message:'shop one'}
  const next=scopedFeature3Preview(previous,two)
  assert.deepEqual(next,{models:[],imageMap:{},busy:false,message:''})
  assert.notStrictEqual(next.models,previous.models)
  assert.notStrictEqual(next.imageMap,previous.imageMap)
})
test('fail-closed on invalid or unscoped async preview state',()=>{
  for (const bad of [null,{},[],{scope:one,models:null,imageMap:{}},
                    {scope:one,models:[],imageMap:null}]) {
    assert.deepEqual(scopedFeature3Preview(bad,one),
      {models:[],imageMap:{},busy:false,message:''})
  }
})

test('failed private image decoder immediately revokes only failed Blob and prevents later double revoke',()=>{
  const first='blob:https://fixture.test/private-one'
  const valid='blob:https://fixture.test/private-two'
  const opened=[first,valid]
  const revoked=[]
  assert.equal(discardFailedPrivateModelPreview(opened,first,u=>revoked.push(u)),true)
  assert.deepEqual(opened,[valid])
  assert.deepEqual(revoked,[first])
  assert.equal(discardFailedPrivateModelPreview(opened,first,u=>revoked.push(u)),false)
  assert.deepEqual(revoked,[first])
  assert.deepEqual(opened,[valid])
})
test('never use external or unowned image URLs as private preview cleanup input',()=>{
  const valid='blob:https://fixture.test/valid'
  const opened=[valid]
  const revoked=[]
  for (const bad of ['https://evil.example/asset','/storage/private/key',null]) {
    assert.throws(()=>discardFailedPrivateModelPreview(opened,bad,u=>revoked.push(u)))
  }
  assert.equal(discardFailedPrivateModelPreview(opened,'blob:https://other.example/unknown',u=>revoked.push(u)),false)
  assert.deepEqual(opened,[valid])
  assert.deepEqual(revoked,[])
})

test('F3-10 failed Blob revocation retains ownership for later cleanup retry',()=>{
  const privateURL='blob:https://fixture.test/retry-private'
  const opened=[privateURL]
  assert.throws(()=>discardFailedPrivateModelPreview(opened,privateURL,()=>{
    throw Error('Browser revoke unavailable')
  }),/Browser revoke unavailable/)
  assert.deepEqual(opened,[privateURL],
    'failed revoke must not discard the only tracked private URL')
  const revoked=[]
  assert.equal(discardFailedPrivateModelPreview(opened,privateURL,url=>revoked.push(url)),true)
  assert.deepEqual(revoked,[privateURL])
  assert.deepEqual(opened,[])
})
