import test from "node:test";
import assert from "node:assert/strict";
import { ReelIntentWriter,createReelIntentGateway } from "../../experiments/secure-node-http/src/reel-intent.mjs";
import { createPosterWriteGateway } from "../../experiments/secure-node-http/src/poster-writes.mjs";
import { createSecureHttpDispatcher } from "../../experiments/secure-node-http/src/secure-api-dispatch.mjs";

const SHOP="11111111-1111-4111-8111-111111111111";
const USER="22222222-2222-4222-8222-222222222222";
const CAMPAIGN="33333333-3333-4333-8333-333333333333";
const POSTER="44444444-4444-4444-8444-444444444444";
const MISSING="55555555-5555-4555-8555-555555555555";
const JOB="66666666-6666-4666-8666-666666666666";
const PREVIEW="https://purple-dune-06b5da200-p0249writes.eastasia.2.azurestaticapps.net";
const JWT="test-only-header-jwt-verified-by-injected-verifier-123";

function composition({posterExists=true,role="OWNER",rpcThrows=false}={}){
  const calls=[];
  const fetchImpl=async (url,opts)=>{
    const target=new URL(url);
    calls.push({target,method:opts.method});
    if(target.pathname.endsWith("/rest/v1/poster_drafts")){
      return {ok:true,status:200,json:async()=>posterExists
        ?[{id:POSTER,shop_id:SHOP,status:"DRAFT",source_asset_id:MISSING,output_asset_id:null}]:[]};
    }
    if(target.pathname.endsWith("/rest/v1/shop_memberships")){
      return {ok:true,status:200,json:async()=>role==="INACTIVE"?[]
        :[{shop_id:SHOP,user_id:USER,active:true,role}]};
    }
    if(target.pathname.endsWith("/rest/v1/rpc/request_poster_job")){
      if(rpcThrows)throw new Error("lost HTTP acknowledgement");
      return {ok:true,status:200,json:async()=>JOB};
    }
    throw new Error("unexpected external fetch");
  };
  const writer=new ReelIntentWriter({origin:"https://retail-test.supabase.co",
    publishableKey:"sb_publishable_test",fetchImpl});
  const verifyJwt=async jwt=>{
    assert.equal(jwt,JWT);
    return USER;
  };
  const gateway=createSecureHttpDispatcher({
    readGateway:async()=>({status:501,jsonBody:{error:"NOT_TESTED"}}),
    posterGateway:createPosterWriteGateway({verifyJwt,writer}),
    reelGateway:createReelIntentGateway({verifyJwt,writer}),
    campaignGateway:async()=>({status:501,jsonBody:{error:"NOT_TESTED"}}),
    writesEnabled:true,renderWritesEnabled:true,allowedOrigin:PREVIEW,
  });
  const dispatch=(path,body={})=>gateway(new Request(PREVIEW+path,{
    method:"POST",headers:{
      "Content-Type":"application/json",
      "x-rgai-supabase-jwt":JWT,
      "Origin":PREVIEW,
      "Sec-Fetch-Site":"same-origin",
    },body:JSON.stringify(body),
  }));
  return {writer,calls,dispatch};
}

test("shared ReelIntentWriter keeps distinct poster and Reel rendering entrypoints",async()=>{
  const {writer,calls,dispatch}=composition({posterExists:false});
  assert.equal(typeof writer.requestPosterRender,"function");
  assert.equal(typeof writer.requestRender,"function");
  assert.notEqual(writer.requestPosterRender,writer.requestRender);
  const result=await dispatch("/api/poster-drafts/"+MISSING+"/renders",{});
  assert.deepEqual({status:result.status,error:result.jsonBody?.error},
    {status:404,error:"NOT_FOUND"});
  assert.equal(calls.filter(c=>c.method==="POST").length,0);
  assert.equal(calls.filter(c=>c.target.pathname.endsWith("/poster_drafts")).length,1);
});

test("actual shared writer posts exactly one poster quota/outbox RPC, NOT a Reel RPC",async()=>{
  const {calls,dispatch}=composition();
  const result=await dispatch("/api/poster-drafts/"+POSTER+"/renders",{});
  assert.deepEqual({status:result.status,body:result.jsonBody},
    {status:202,body:{job_id:JOB,status:"QUEUED"}});
  const rpc=calls.filter(c=>c.method==="POST");
  assert.equal(rpc.length,1);
  assert.ok(rpc[0].target.pathname.endsWith("/rest/v1/rpc/request_poster_job"));
  assert.equal(calls.filter(c=>c.target.pathname.includes("request_reel_render_job")).length,0);
});

test("independent Reel HTTP route still requires its own {day_id,preset} contract",async()=>{
  const {calls,dispatch}=composition();
  const result=await dispatch("/api/campaigns/"+CAMPAIGN+"/renders",{});
  assert.equal(result.status,400);
  assert.equal(result.jsonBody?.error,"INVALID_REQUEST");
  assert.equal(calls.length,0);
});

test("poster mutation retains strict body, OWNER/EDITOR, and ambiguous ACK failure semantics",async()=>{
  {
    const {calls,dispatch}=composition();
    const r=await dispatch("/api/poster-drafts/"+POSTER+"/renders",
      {day_id:MISSING,preset:"instagram_reel_30s"});
    assert.equal(r.status,400);
    assert.equal(r.jsonBody?.error,"INVALID_REQUEST");
    assert.equal(calls.length,0);
  }
  for(const role of ["VIEWER","INACTIVE"]){
    const {calls,dispatch}=composition({role});
    const r=await dispatch("/api/poster-drafts/"+POSTER+"/renders",{});
    assert.ok([403,404].includes(r.status));
    assert.equal(calls.filter(c=>c.method==="POST").length,0);
  }
  {
    const {calls,dispatch}=composition({rpcThrows:true});
    const r=await dispatch("/api/poster-drafts/"+POSTER+"/renders",{});
    assert.equal(r.status,503);
    assert.equal(r.jsonBody?.error,"SERVICE_UNAVAILABLE");
    assert.equal(calls.filter(c=>c.method==="POST").length,1);
  }
});
