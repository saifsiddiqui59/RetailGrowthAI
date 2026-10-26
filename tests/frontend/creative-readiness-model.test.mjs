import test from 'node:test'
import assert from 'node:assert/strict'
import { creativeReadiness, validatedCreativeProfile } from '../../frontend/src/features/dashboard/creative-readiness-model.mjs'

const SHOP='a1000000-0000-4000-8000-000000000001'
const OTHER='a1000000-0000-4000-8000-000000000002'
const baseline={shop_id:SHOP,business_name:'Dawn Boutique',category:'other',city:'',
 description:'',brand_voice:''}

test('profile readiness only includes verified own-shop profile and known fields',()=>{
 assert.equal(validatedCreativeProfile({...baseline,shop_id:OTHER},SHOP),null)
 assert.equal(creativeReadiness({...baseline,shop_id:OTHER},SHOP),null)
 assert.equal(creativeReadiness(baseline,OTHER),null)
 assert.equal(creativeReadiness(null,SHOP),null)
 assert.equal(creativeReadiness(baseline,'invalid'),null)
 const state=creativeReadiness(baseline,SHOP)
 assert.equal(state.completed,1)
 assert.equal(state.total,5)
 assert.deepEqual(state.checks.filter(c=>c.satisfied).map(c=>c.key),['name'])
})
test('marketing context checklist reacts only to recorded business fields',()=>{
 const state=creativeReadiness({...baseline,category:'Clothing',city:'Nagpur',
 description:'Contemporary ethnic wear for working adults',brand_voice:'Warm'},SHOP)
 assert.equal(state.completed,5)
 assert.equal(state.checks.every(c=>c.satisfied),true)
 assert.equal(creativeReadiness({...baseline,category:'UNKNOWN'},SHOP).completed,1)
 assert.equal(creativeReadiness({...baseline,city:{toString(){throw Error('malicious')}}},SHOP).completed,1)
})
