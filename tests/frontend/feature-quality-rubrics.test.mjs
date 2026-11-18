import test from 'node:test'
import assert from 'node:assert/strict'
import {QUALITY_RUBRICS,dimensionsFor,acceptedDimension,dimensionAdvice}
 from '../../frontend/src/features/testing/quality-rubrics.mjs'

test('only real creative features have explicit human dimensions',()=>{
 assert.deepEqual(Object.keys(QUALITY_RUBRICS).sort(),['F2','F3','F4','F5','F7'])
 assert.deepEqual(dimensionsFor('F1'),[])
 assert.ok(dimensionsFor('F4').some(x=>x.id==='audio'))
})
test('each feature has unique dimension choices and usable next-check advice',()=>{
 for(const [feature,values] of Object.entries(QUALITY_RUBRICS)){
   assert.ok(values.length >= 3,feature)
   assert.equal(new Set(values.map(x=>x.id)).size,values.length)
   assert.ok(values.every(x=>x.label.length>=5&&x.next_check.length>=30))
   assert.equal(values[0].id,'overall')
   for(const row of values){
     assert.equal(acceptedDimension(feature,row.id),row)
     assert.equal(dimensionAdvice(feature,row.id),row.next_check)
   }
 }
})
test('unsupported dimension or feature cannot fabricate an improvement classification',()=>{
 assert.equal(acceptedDimension('F4','unauthorized'),null)
 assert.equal(dimensionAdvice('F4','model_accuracy'),null)
 assert.equal(dimensionAdvice('F1','overall'),null)
})
