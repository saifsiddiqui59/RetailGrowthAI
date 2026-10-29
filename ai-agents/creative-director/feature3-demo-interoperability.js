'use strict';
// Feature2 source-only F3 OpenVTO original byte pins -> F4/F5 editorial test.
// Real F3 rights and private worker auth are NEVER replaced.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {exportFixture}=require('./export-feature4-feature5-fixture');
const REV='10140178cdb198ff17ad7b226c432bd63d732fc2';
const PINS={
  'model_posture.jpg':['72a86a60280976ce5c73db9525d9648b54d1126a',103914,'image/jpeg'],
  'model_avatar.png':['fc88e5d07282009a14b0bd58fbdd58bc2f89ace0',1207867,'image/png'],
  'garment_front.jpg':['878fde8857f58862723f85d7f8bd723c65a8e498',32633,'image/jpeg']
};
const fail=()=>{throw Error('FEATURE2_F3_DEMO_INPUT_INVALID')};
const hex=(kind,buf)=>crypto.createHash(kind).update(buf).digest('hex');
const equal=(a,b)=>typeof a==='string'&&typeof b==='string'&&a.length===b.length&&
 crypto.timingSafeEqual(Buffer.from(a),Buffer.from(b));
function recheck(dir,manifest,pins){
  if(!manifest||manifest.schema!=='retailgrowth.feature3.demo-input-package.v1'||
    manifest.source_repository!=='Prompt-Haus/OpenVTO'||manifest.source_commit!==REV||
    manifest.license!=='MIT-demo-assets'||
    manifest.license_scope!=='testing-and-demonstration-only'||
    manifest.tenant_private!==false||
    manifest.rights_approved_for_customer_publishing!==false||
    manifest.virtual_tryon_generated_by_retailgrowth!==false||
    manifest.feature4?.first_frame!=='model_posture.jpg'||
    manifest.feature4?.garment!=='garment_front.jpg'||
    manifest.feature4?.private_client_publish_allowed!==false||
    manifest.feature5?.first_frame!=='model_posture.jpg'||
    manifest.feature5?.garment!=='garment_front.jpg'||
    manifest.feature5?.provider_call_authorized!==false||
    manifest.feature5?.cost_reservation_authorized!==false||
    !Array.isArray(manifest.files)||manifest.files.length!==3||
    new Set(manifest.files.map(x=>x?.file)).size!==3)fail();
  const checked={};
  for(const row of manifest.files){
    const pin=pins[row.file];
    if(!pin||row.size_bytes!==pin[1]||row.mime_type!==pin[2]||
      !equal(row.git_blob_sha1,pin[0])||
      typeof row.sha256!=='string'||!/^[a-f0-9]{64}$/.test(row.sha256)||
      !Array.isArray(row.dimensions)||row.dimensions.length!==2||
      !row.dimensions.every(x=>Number.isInteger(x)&&x>=1&&x<=8192)||
      row.dimensions[0]*row.dimensions[1]>24_000_000)fail();
    const pathname=path.join(dir,row.file);
    const stat=fs.lstatSync(pathname);
    if(!stat.isFile()||stat.isSymbolicLink()||stat.size!==pin[1]||
      stat.size>3*1024*1024)fail();
    const bytes=fs.readFileSync(pathname);
    const signature=pin[2]==='image/png'
      ? bytes.subarray(0,8).equals(Buffer.from('89504e470d0a1a0a','hex'))
      : bytes.subarray(0,3).equals(Buffer.from('ffd8ff','hex'))&&
        bytes.subarray(-2).equals(Buffer.from('ffd9','hex'));
    const git=hex('sha1',Buffer.concat([Buffer.from('blob '+bytes.length+'\0'),bytes]));
    if(!signature||!equal(git,pin[0])||!equal(hex('sha256',bytes),row.sha256))fail();
    checked[row.file]={filename:row.file,sha256:row.sha256,
      git_blob_sha1:pin[0],size_bytes:bytes.length,mime_type:pin[2],
      demo_only:true,tenant_private:false,customer_publish_approved:false};
  }
  if(Object.keys(checked).length!==3)fail();
  return checked;
}
function linkDemo(duration,folder){
  if(![15,30,60].includes(duration)||typeof folder!=='string'||!folder||
    folder.length>1000)fail();
  let root,manifest;
  try{
    const stat=fs.lstatSync(folder);
    if(!stat.isDirectory()||stat.isSymbolicLink())fail();
    root=fs.realpathSync(folder);
    const file=path.join(root,'verified_manifest.json');
    const st=fs.lstatSync(file);
    if(!st.isFile()||st.isSymbolicLink()||st.size>25000)fail();
    manifest=JSON.parse(fs.readFileSync(file,'utf8'));
  }catch(_){fail()}
  const originals=recheck(root,manifest,PINS);
  const fixture=exportFixture(duration);
  if(fixture.review.can_publish!==false||
     fixture.feature5.can_run_paid_motion!==false||
     fixture.source_media.approved_feature3_frame_present!==false)fail();
  return {
    schema:'retailgrowth.feature2-f3-feature45-demo.v1',
    source_plan_sha256:fixture.source_plan_sha256,
    duration_seconds:duration,
    feature3:{source_commit:REV,original_bytes_rechecked:true,
      rights:'MIT_TEST_DEMO_ONLY',approved_private_tenant_assets:false,
      has_actual_retailgrowth_virtual_tryon:false,
      garment_worn_by_model_verified:false,assets:originals},
    feature4:{timeline:fixture.feature4.timeline,
      output:fixture.feature4.target,
      local_demo_frames:['model_posture.jpg','garment_front.jpg'],
      approved_render_request:null,render_approved:false},
    feature5:{clip_requests:fixture.feature5.clip_requests,
      demo_first_frame_file:'model_posture.jpg',
      demo_first_frame_sha256:originals['model_posture.jpg'].sha256,
      actual_private_first_frame_id:null,
      gpu_enabled:false,provider_call_permitted:false,cost_reserved:false},
    audio:{voiceover_script:fixture.audio.voiceover_script,
      real_voiceover_bytes:false,licensed_music_bytes:false},
    approval:{state:'DEMO_ONLY',customer_publish_approved:false,
      live_membership_checked:false,model_likeness_released:false,
      original_product_rights_approved:false,paid_provider_calls:0}
  };
}
if(require.main===module){
  if(process.argv.length!==4||!/^(15|30|60)$/.test(process.argv[2]))fail();
  try{process.stdout.write(JSON.stringify(linkDemo(+process.argv[2],process.argv[3]),null,2)+'\n')}
  catch(_){process.stderr.write('FEATURE2_F3_DEMO_INPUT_INVALID\n');process.exitCode=2}
}
module.exports={linkDemo,recheck};
