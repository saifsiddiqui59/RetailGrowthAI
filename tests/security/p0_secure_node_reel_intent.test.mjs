import test from "node:test";
import assert from "node:assert/strict";
import { ReelIntentWriter, createReelIntentGateway } from "../../experiments/secure-node-http/src/reel-intent.mjs";
import { AuthDenied } from "../../experiments/secure-node-http/src/security.mjs";

const API="https://retail-test.supabase.co";
const SHOP="11111111-1111-4111-8111-111111111111";
const OTHER="99999999-9999-4999-8999-999999999999";
const USER="22222222-2222-4222-8222-222222222222";
const CAMP="33333333-3333-4333-8333-333333333333";
const DAY="44444444-4444-4444-8444-444444444444";
const IMAGE="55555555-5555-4555-8555-555555555555";
const MUSIC="66666666-6666-4666-8666-666666666666";
const JOB="77777777-7777-4777-8777-777777777777";
const HEADER="Bearer fake-in-memory-verified-user";
const request=()=>({day_id:DAY,preset:"instagram_reel_30s"});
const reel=()=>({
  duration_seconds:30,aspect_ratio:"9:16",
  storyboard:[{start_seconds:0,duration_seconds:30,asset_id:IMAGE,overlay_text:"Diwali Sale"}],
  music_asset_id:null,cta:"Visit the store",
});
const day=()=>({
  id:DAY,campaign_id:CAMP,shop_id:SHOP,day_index:1,
  scheduled_date:"2026-10-26",topic:"Festive collection",
  linkedin:{post_text:"Check the collection",hashtags:["#Diwali"]},
  instagram:{caption:"Fashion sale",banner_asset_id:null,reel:reel()},
  review_status:"DRAFT",
});
const rights=(id,shop=SHOP)=>({
  id,shop_id:shop,storage_bucket:"retailgrowth-media",
  object_path:shop+"/uploads/"+id+".png",
  mime_type:id===MUSIC?"audio/mpeg":"image/png",
  license_name:"owned",license_url:null,attribution:"Created by the business owner",
});
function mock({
  role="OWNER",active=true,foreign=false,invalidLicense=false,
  status="DRAFT",dayRejected=false,invalidReel=false,
  music=false,quotaCode=null,lostAck=false,rpcResult={job_id:JOB,status:"QUEUED"},
  duplicateMedia=false,wrongOrigin=false,missingRpc=false,sameMediaForMusic=false,
}={}){
  const calls=[];
  const fetchImpl=async(raw,init)=>{
    const u=new URL(raw);calls.push({u,init});
    if(init.method==="POST"){
      if(lostAck)throw new Error("network lost after database commit maybe");
      if(missingRpc)return {ok:false,status:404,json:async()=>({code:"PGRST202"})};
      if(quotaCode)return {ok:false,status:429,json:async()=>({code:quotaCode})};
      return {ok:true,status:200,json:async()=>rpcResult};
    }
    const table=u.pathname.split("/").at(-1);
    let rows=[];
    if(table==="campaigns") rows=[{id:CAMP,shop_id:foreign?OTHER:SHOP,status}];
    if(table==="campaign_days"){
      const v=day();
      if(invalidReel)v.instagram.reel.storyboard[0].duration_seconds=29;
      if(dayRejected)v.review_status="REJECTED";
      if(music)v.instagram.reel.music_asset_id=MUSIC;
      if(sameMediaForMusic){
        v.instagram.reel.music_asset_id=MUSIC;
        v.instagram.reel.storyboard[0].asset_id=MUSIC;
      }
      rows=[v];
    }
    if(table==="shop_memberships")rows=active?
      [{shop_id:SHOP,user_id:USER,role,active:true}]:[];
    if(table==="media_assets"){
      const ids=(u.searchParams.get("id")||"").replace(/^in\.\(/,"").replace(/\)$/,"").split(",");
      rows=ids.map(id=>rights(id));
      if(invalidLicense)rows[0].license_name="unverified";
      if(wrongOrigin)rows[0].shop_id=OTHER;
      if(duplicateMedia)rows.push({...rows[0]});
    }
    return {ok:true,status:200,json:async()=>rows};
  };
  const writer=new ReelIntentWriter({origin:API,publishableKey:"sb_publishable_test",fetchImpl});
  const handler=createReelIntentGateway({verifyJwt:async()=>USER,writer});
  return {handler,calls,writer};
}
const postCalls=calls=>calls.filter(x=>x.init.method==="POST");
test("happy-path uses existing user JWT and *only* two IDs to proposed single SQL RPC", async()=>{
  const {handler,calls}=mock();
  const r=await handler("POST","/api/campaigns/"+CAMP+"/renders",HEADER,request());
  assert.deepEqual({status:r.status,body:r.jsonBody},{
    status:202,body:{job_id:JOB,status:"QUEUED"},
  });
  const posts=postCalls(calls);
  assert.equal(posts.length,1);
  const call=posts[0];
  assert.equal(call.u.origin,API);
  assert.equal(call.u.pathname,"/rest/v1/rpc/request_reel_render_job");
  assert.equal(call.init.headers.Authorization,"Bearer "+HEADER.slice(7));
  assert.equal(call.init.headers.apikey,"sb_publishable_test");
  assert.equal(call.init.redirect,"error");
  assert.deepEqual(JSON.parse(call.init.body),{p_campaign_id:CAMP,p_day_id:DAY});
  assert.ok(!JSON.stringify(call).includes("service_role"));
});
test("an existing SUCCEEDED same logical render is 200, not another backend enqueue", async()=>{
  const {handler,calls}=mock({rpcResult:{job_id:JOB,status:"SUCCEEDED"}});
  const r=await handler("POST","/api/campaigns/"+CAMP+"/renders",HEADER,request());
  assert.equal(r.status,200);
  assert.equal(r.jsonBody.job_id,JOB);
  assert.equal(postCalls(calls).length,1);
});
test("unsupported methods, unknown paths, missing/forged auth fail before DB",async()=>{
  const {handler,calls}=mock();
  assert.equal((await handler("GET","/api/campaigns/"+CAMP+"/renders",HEADER,request())).status,405);
  assert.equal((await handler("POST","/api/render-jobs/"+JOB,HEADER,request())).status,404);
  assert.equal((await handler("POST","/api/campaigns/"+CAMP+"/renders","",request())).status,401);
  assert.equal(calls.length,0);
  const denied=createReelIntentGateway({verifyJwt:async()=>{throw new AuthDenied();},writer:mock().writer});
  assert.equal((await denied("POST","/api/campaigns/"+CAMP+"/renders",HEADER,request())).status,401);
});
test("invalid preset, extra hidden fields, non-UUID day ID are rejected before RPC",async()=>{
  for(const bad of [
    {day_id:DAY,preset:"premium_video"},
    {...request(),shop_id:OTHER},
    {...request(),idempotency_key:"forged"},
    {day_id:"../tenant",preset:"instagram_reel_30s"},
    null,
  ]){
    const {handler,calls}=mock();
    const r=await handler("POST","/api/campaigns/"+CAMP+"/renders",HEADER,bad);
    assert.equal(r.status,400);
    assert.equal(postCalls(calls).length,0);
  }
});
test("VIEWER, revoked account, foreign shop block requests before RPC",async()=>{
  for(const options of [{role:"VIEWER"},{active:false},{foreign:true}]){
    const {handler,calls}=mock(options);
    const r=await handler("POST","/api/campaigns/"+CAMP+"/renders",HEADER,request());
    assert.notEqual(r.status,202);
    assert.equal(postCalls(calls).length,0);
  }
});
test("rejected, non-DRAFT campaign and malformed 30-second storyboard are denied",async()=>{
  for(const options of [{status:"PLANNING"},{dayRejected:true},{invalidReel:true}]){
    const {handler,calls}=mock(options);
    const r=await handler("POST","/api/campaigns/"+CAMP+"/renders",HEADER,request());
    assert.notEqual(r.status,202);
    assert.equal(postCalls(calls).length,0);
  }
});
test("unreviewed licence, foreign media or duplicated RLS rows never invoke quota RPC",async()=>{
  for(const options of [{invalidLicense:true},{wrongOrigin:true},{duplicateMedia:true}]){
    const {handler,calls}=mock(options);
    const r=await handler("POST","/api/campaigns/"+CAMP+"/renders",HEADER,request());
    assert.notEqual(r.status,202);
    assert.equal(postCalls(calls).length,0);
  }
});
test("validated music must be licensed audio not unlicensed or image payload",async()=>{
  const {handler,calls}=mock({music:true});
  const r=await handler("POST","/api/campaigns/"+CAMP+"/renders",HEADER,request());
  assert.equal(r.status,202);
  assert.equal(postCalls(calls).length,1);
  assert.equal(JSON.parse(postCalls(calls)[0].init.body).p_day_id,DAY);
});
test("missing proposed RPC correctly returns service unavailable instead of forging a render job",async()=>{
  const {handler,calls}=mock({missingRpc:true});
  const r=await handler("POST","/api/campaigns/"+CAMP+"/renders",HEADER,request());
  assert.deepEqual({status:r.status,body:r.jsonBody},
    {status:503,body:{error:"SERVICE_UNAVAILABLE"}});
  assert.equal(postCalls(calls).length,1);
});
test("SQL-authored subscription / quota errors distinguish 402 from 429 without retry",async()=>{
  for(const [code,status] of [["RG001",402],["RG002",429]]){
    const {handler,calls}=mock({quotaCode:code});
    const result=await handler("POST","/api/campaigns/"+CAMP+"/renders",HEADER,request());
    assert.equal(result.status,status);
    assert.equal(postCalls(calls).length,1);
  }
});
test("lost commit acknowledgment never retries possibly billable POST",async()=>{
  const {handler,calls}=mock({lostAck:true});
  const r=await handler("POST","/api/campaigns/"+CAMP+"/renders",HEADER,request());
  assert.equal(r.status,503);
  assert.equal(postCalls(calls).length,1);
});
test("malformed procedure response cannot masquerade as completed render job",async()=>{
  for(const rpcResult of [
    {job_id:"not-a-uuid",status:"QUEUED"},{job_id:JOB,status:"FREE"},
    {job_id:JOB,status:"QUEUED",shop_id:OTHER},
    [JOB],null,
  ]){
    const {handler,calls}=mock({rpcResult});
    const r=await handler("POST","/api/campaigns/"+CAMP+"/renders",HEADER,request());
    assert.equal(r.status,503);
    assert.equal(postCalls(calls).length,1);
  }
});

test("same owned audio file cannot double as Reel storyboard image AND music",async()=>{
  const {handler,calls}=mock({sameMediaForMusic:true});
  const response=await handler("POST","/api/campaigns/"+CAMP+"/renders",HEADER,request());
  assert.notEqual(response.status,202);
  assert.equal(postCalls(calls).length,0);
});
