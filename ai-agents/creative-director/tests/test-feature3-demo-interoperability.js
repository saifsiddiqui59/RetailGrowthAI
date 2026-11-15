'use strict';
const assert=require('node:assert/strict');
const {mkdtempSync,writeFileSync,rmSync}=require('node:fs');
const path=require('node:path'),os=require('node:os'),crypto=require('node:crypto');
const {recheck,linkDemo}=require('../feature3-demo-interoperability');
const hash=(kind,b)=>crypto.createHash(kind).update(b).digest('hex');
const git=b=>hash('sha1',Buffer.concat([Buffer.from('blob '+b.length+'\0'),b]));
const png=Buffer.from('89504e470d0a1a0a0000000d494844520000000100000001080600000012345678','hex');
const jpg=Buffer.from('ffd8ffe000104a46494600010100000100010000ffd9','hex');
const data={'model_posture.jpg':jpg,'model_avatar.png':png,'garment_front.jpg':jpg};
const pins=Object.fromEntries(Object.entries(data).map(([k,b])=>[k,[git(b),b.length,k.endsWith('.png')?'image/png':'image/jpeg']]));
const manifest={
 schema:'retailgrowth.feature3.demo-input-package.v1',
 source_repository:'Prompt-Haus/OpenVTO',source_commit:'10140178cdb198ff17ad7b226c432bd63d732fc2',
 license:'MIT-demo-assets',license_scope:'testing-and-demonstration-only',
 tenant_private:false,rights_approved_for_customer_publishing:false,
 virtual_tryon_generated_by_retailgrowth:false,
 feature4:{first_frame:'model_posture.jpg',garment:'garment_front.jpg',private_client_publish_allowed:false},
 feature5:{first_frame:'model_posture.jpg',garment:'garment_front.jpg',provider_call_authorized:false,cost_reservation_authorized:false},
 files:Object.entries(data).map(([file,b])=>({file,size_bytes:b.length,git_blob_sha1:git(b),
 sha256:hash('sha256',b),mime_type:pins[file][2],dimensions:[1000,1000]})),
};
const folder=mkdtempSync(path.join(os.tmpdir(),'rgai-f2-f3-'));
try{
 for(const [name,b] of Object.entries(data))writeFileSync(path.join(folder,name),b);
 writeFileSync(path.join(folder,'verified_manifest.json'),JSON.stringify(manifest));
 assert.equal(Object.keys(recheck(folder,manifest,pins)).length,3);
 // Faked image hashes must NEVER bypass the real hard-coded original Git blob pins.
 assert.throws(()=>linkDemo(30,folder),/FEATURE2_F3_DEMO_INPUT_INVALID/);
 for(const [key,value] of [['rights_approved_for_customer_publishing',true],['license_scope','commercial'],['virtual_tryon_generated_by_retailgrowth',true]]){
  const bad=structuredClone(manifest);bad[key]=value;
  assert.throws(()=>recheck(folder,bad,pins),/FEATURE2_F3_DEMO_INPUT_INVALID/);
 }
 const bad=structuredClone(manifest);bad.files[0].sha256='0'.repeat(64);
 assert.throws(()=>recheck(folder,bad,pins),/FEATURE2_F3_DEMO_INPUT_INVALID/);
 const wrong=structuredClone(manifest);wrong.feature5.provider_call_authorized=true;
 assert.throws(()=>recheck(folder,wrong,pins),/FEATURE2_F3_DEMO_INPUT_INVALID/);
 writeFileSync(path.join(folder,'model_posture.jpg'),Buffer.concat([jpg,Buffer.from([1])]));
 assert.throws(()=>recheck(folder,manifest,pins),/FEATURE2_F3_DEMO_INPUT_INVALID/);
}finally{rmSync(folder,{recursive:true,force:true})}
console.log('F2 F3 original byte verification and fake authorization denial PASS');
