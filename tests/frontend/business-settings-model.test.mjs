import test from 'node:test'
import assert from 'node:assert/strict'
import { profileDraft, profilePatch } from '../../frontend/src/features/dashboard/business-settings-model.mjs'
const base = {shop_id:'a1000000-0000-4000-8000-000000000001',
 business_name:'Boutique',category:'Clothing',description:'Fashion',brand_voice:'',
 city:'Nagpur',website_url:null,contact_email:null,owner_user_id:'untrusted'}
test('profile form retains only editable fields and does not update unchanged profile',()=>{
  const draft=profileDraft(base)
  assert.equal('owner_user_id' in draft,false)
  assert.deepEqual(profilePatch(base,draft),{})
  draft.business_name='  New Boutique  '
  draft.description=' Fresh textiles '
  assert.deepEqual(profilePatch(base,draft),{business_name:'New Boutique',description:'Fresh textiles'})
})
test('invalid profile data cannot cause a PATCH',()=>{
  for (const update of [
    {business_name:''},{business_name:' '.repeat(2)},
    {business_name:'x'.repeat(141)},{contact_email:'broken'},
    {website_url:'http://insecure.test'}, {website_url:'https://user:pass@site.test'},
    {website_url:'javascript:alert(1)'}
  ]) {
    assert.throws(()=>profilePatch(base,{...profileDraft(base),...update}))
  }
})
test('empty optional fields become null and extra keys are ignored',()=>{
  const changed={...profileDraft(base),city:'  ',owner_user_id:'spoofed'}
  assert.deepEqual(profilePatch(base,changed),{city:''})
  assert.deepEqual(profilePatch({...base,contact_email:'shop@example.test'}, {...profileDraft(base),contact_email:''}),{contact_email:null})
})
