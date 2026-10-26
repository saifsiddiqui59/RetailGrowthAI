import test from "node:test";
import assert from "node:assert/strict";
import { PosterRpcWriter,createPosterWriteGateway } from "../../experiments/secure-node-http/src/poster-writes.mjs";
import { AuthDenied } from "../../experiments/secure-node-http/src/security.mjs";

const ORIGIN="https://retail-test.supabase.co";
const SHOP="11111111-1111-4111-8111-111111111111";
const USER="22222222-2222-4222-8222-222222222222";
const CAMP="33333333-3333-4333-8333-333333333333";
const DAY="44444444-4444-4444-8444-444444444444";
const SOURCE="55555555-5555-4555-8555-555555555555";
const POSTER="66666666-6666-4666-8666-666666666666";
const JOB="77777777-7777-4777-8777-777777777777";
const ROLE="OWNER";
const token="Bearer test-jwt-signature-verified-by-injected-verifier";
const draftBody=()=>({
  day_id:DAY,source_asset_id:SOURCE,template:"editorial",format:"portrait",
  business_name:"Boutique",accent_color:"#123456",background_color:"#abcdef",
});
const savedInstagram=()=>({caption:"new caption",banner_asset_id:null,reel:{duration_seconds:30}});

function harness({role=ROLE,stale=false,quota=null,invalidSign=false,wrongShop=false,
                  campaignState="DRAFT",dayState="DRAFT",posterState="READY"}={}){
  const calls=[];
  const fetchImpl=async(raw,init)=>{
    const url=new URL(raw);
    calls.push({url,init});
    if(url.pathname.includes("/rest/v1/rpc/")){
      if(quota) return {ok:false,status:quota==="RG002"?429:402,json:async()=>({code:quota})};
      const name=url.pathname.split("/").at(-1);
      return {ok:true,status:200,json:async()=>name==="create_poster_draft"?POSTER:
        name==="request_poster_job"?JOB:!stale};
    }
    let rows=[];
    switch(url.pathname.split("/").at(-1)){
      case "campaigns":
        rows=[{id:CAMP,shop_id:wrongShop?"99999999-9999-4999-8999-999999999999":SHOP,status:campaignState}];
        break;
      case "campaign_days":
        rows=[{id:DAY,shop_id:SHOP,campaign_id:CAMP,review_status:dayState,
          instagram:{reel:{storyboard:[{asset_id:SOURCE}]}}}];
        break;
      case "shop_memberships":
        rows=role==="INACTIVE"?[]:[{shop_id:SHOP,user_id:USER,active:true,role}];
        break;
      case "media_assets":
        rows=[{id:SOURCE,shop_id:SHOP,storage_bucket:"retailgrowth-media",
          object_path:SHOP+"/uploads/retail.png",mime_type:"image/png"}];
        break;
      case "poster_drafts":
        rows=[{id:POSTER,shop_id:SHOP,status:posterState,output_asset_id:SOURCE}];
        break;
    }
    return {ok:true,status:200,json:async()=>rows};
  };
  const writer=new PosterRpcWriter({origin:ORIGIN,publishableKey:"sb_publishable_test",fetchImpl});
  return {writer,calls,handle:createPosterWriteGateway({verifyJwt:async()=>USER,writer})};
}
test("poster draft POST uses exactly user-JWT RLS-rights-gated SQL RPC, no queue enqueue",async()=>{
  const {handle,calls}=harness();
  const result=await handle("POST","/api/campaigns/"+CAMP+"/posters",token,draftBody());
  assert.deepEqual({status:result.status,body:result.jsonBody},{
    status:201,body:{poster_id:POSTER,status:"DRAFT"}});
  const rpc=calls.find(c=>c.url.pathname.endsWith("/rpc/create_poster_draft"));
  assert.ok(rpc);
  assert.equal(rpc.init.method,"POST");
  assert.equal(rpc.init.headers.Authorization,"Bearer "+token.slice(7));
  assert.equal(rpc.init.headers.apikey,"sb_publishable_test");
  assert.equal(rpc.init.redirect,"error");
  assert.equal(JSON.parse(rpc.init.body).p_shop_id,SHOP);
  assert.equal(JSON.parse(rpc.init.body).p_source_asset_id,SOURCE);
  assert.equal(calls.filter(c=>c.init.method==="POST").length,1);
});
test("VIEWER and inactive users cannot create poster draft or reserve render quota",async()=>{
  for(const role of ["VIEWER","INACTIVE"]){
    const {handle,calls}=harness({role});
    const result=await handle("POST","/api/campaigns/"+CAMP+"/posters",token,draftBody());
    assert.ok([403,404].includes(result.status));
    assert.equal(calls.filter(c=>c.init.method==="POST").length,0);
    const render=await handle("POST","/api/poster-drafts/"+POSTER+"/renders",token,{});
    assert.ok([403,404].includes(render.status));
    assert.equal(calls.filter(c=>c.init.method==="POST").length,0);
  }
});
test("poster render POST delegates exactly once to atomic SQL job+outbox RPC",async()=>{
  const {handle,calls}=harness();
  const response=await handle("POST","/api/poster-drafts/"+POSTER+"/renders",token,{});
  assert.deepEqual({status:response.status,body:response.jsonBody},
    {status:202,body:{job_id:JOB,status:"QUEUED"}});
  const rpc=calls.filter(c=>c.url.pathname.includes("/rpc/"));
  assert.equal(rpc.length,1);
  assert.ok(rpc[0].url.pathname.endsWith("/rpc/request_poster_job"));
  assert.deepEqual(JSON.parse(rpc[0].init.body),{p_poster_id:POSTER});
});
test("poster selection uses expected full Instagram CAS, fails closed when stale",async()=>{
  const body={expected_instagram:savedInstagram()};
  const {handle,calls}=harness();
  const response=await handle("POST","/api/poster-drafts/"+POSTER+"/select",token,body);
  assert.equal(response.status,200);
  assert.deepEqual(response.jsonBody,{poster_id:POSTER,banner_asset_id:SOURCE});
  const rpc=calls.find(c=>c.url.pathname.endsWith("/rpc/select_poster_banner"));
  assert.deepEqual(JSON.parse(rpc.init.body),{p_poster_id:POSTER,p_expected_instagram:body.expected_instagram});
  const notCurrent=harness({stale:true});
  const conflict=await notCurrent.handle("POST","/api/poster-drafts/"+POSTER+"/select",token,body);
  assert.equal(conflict.status,409);
  assert.equal(conflict.jsonBody.error,"POSTER_SELECTION_STALE_OR_DENIED");
});
test("malformed fields and unready poster fail without any SQL RPC",async()=>{
  const bad=[
    {...draftBody(),unknown:"forged"},
    {...draftBody(),accent_color:"<script>"},
    {...draftBody(),business_name:""},
    {...draftBody(),source_asset_id:"../another"},
    {...draftBody(),offer_text:"\u0000control"},
  ];
  for(const body of bad){
    const {handle,calls}=harness();
    const response=await handle("POST","/api/campaigns/"+CAMP+"/posters",token,body);
    assert.equal(response.status,400);
    assert.ok(!calls.some(c=>c.url.pathname.includes("/rpc/")));
  }
  const {handle,calls}=harness({posterState:"DRAFT"});
  const response=await handle("POST","/api/poster-drafts/"+POSTER+"/select",token,
    {expected_instagram:savedInstagram()});
  assert.equal(response.status,409);
  assert.ok(!calls.some(c=>c.url.pathname.includes("/rpc/")));
});
test("non-draft campaign/day and forged cross-shop lineage stop before RPC",async()=>{
  for(const options of [{campaignState:"PLANNING"},{dayState:"APPROVED"},{wrongShop:true}]){
    const {handle,calls}=harness(options);
    const response=await handle("POST","/api/campaigns/"+CAMP+"/posters",token,draftBody());
    assert.ok([404,409,503].includes(response.status));
    assert.ok(!calls.some(c=>c.url.pathname.includes("/rpc/")));
  }
});
test("SQL-authored subscription quota and expiry errors preserve v1 429/402",async()=>{
  for(const [code,status,error] of [["RG002",429,"QUOTA_EXCEEDED"],["RG001",402,"SUBSCRIPTION_REQUIRED"]]){
    const {handle}=harness({quota:code});
    const response=await handle("POST","/api/poster-drafts/"+POSTER+"/renders",token,{});
    assert.equal(response.status,status);
    assert.equal(response.jsonBody.error,error);
  }
});
test("lost RPC network acknowledgement is 503 and NEVER retried automatically",async()=>{
  let count=0;
  const base=harness();
  base.writer.fetchImpl=async(url,opts)=>{
    if(String(url).includes("/rpc/")){count++;throw Error("network lost after DB possibly committed");}
    return harness().writer.fetchImpl(url,opts);
  };
  const r=await base.handle("POST","/api/poster-drafts/"+POSTER+"/renders",token,{});
  assert.equal(r.status,503);
  assert.equal(count,1);
});
test("unsigned, forged, irrelevant and mutating routes are denied",async()=>{
  const {handle,calls}=harness();
  assert.equal((await handle("POST","/api/poster-drafts/"+POSTER+"/renders","",{})).status,401);
  assert.equal((await handle("PATCH","/api/poster-drafts/"+POSTER+"/renders",token,{})).status,405);
  assert.equal((await handle("POST","/api/render-jobs/"+JOB,token,{})).status,404);
  assert.equal((await handle("POST","/api/poster-drafts/"+POSTER+"/select",token,{expected_instagram:{caption:""} })).status,400);
  assert.equal(calls.length,0);
  const denied=createPosterWriteGateway({verifyJwt:async()=>{throw new AuthDenied()},writer:harness().writer});
  assert.equal((await denied("POST","/api/poster-drafts/"+POSTER+"/renders",token,{})).status,401);
});
test("writer cannot invoke arbitrary database RPC name",async()=>{
  const {writer,calls}=harness();
  await assert.rejects(()=>writer.rpc("token","dangerous_arbitrary_rpc",{p_shop_id:SHOP}),TypeError);
  assert.equal(calls.length,0);
});
