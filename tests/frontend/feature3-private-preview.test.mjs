import test from 'node:test'
import assert from 'node:assert/strict'
import {scopedFeature3Preview} from '../../frontend/src/features/creative/feature3-private-preview.mjs'

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
