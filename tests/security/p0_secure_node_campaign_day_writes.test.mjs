import test from "node:test";
import assert from "node:assert/strict";
import { validateCampaignBrief,validateCampaign,ContractDenied } from "../../experiments/secure-node-http/src/v1-contract.mjs";
import { CampaignDayWriter,createCampaignDayGateway } from "../../experiments/secure-node-http/src/campaign-day-writes.mjs";
import { AuthDenied } from "../../experiments/secure-node-http/src/security.mjs";

const ORIGIN="https://retail-test.supabase.co";
const SHOP="11111111-1111-4111-8111-111111111111";
const USER="22222222-2222-4222-8222-222222222222";
const CAMP="33333333-3333-4333-8333-333333333333";
const DAY="44444444-4444-4444-8444-444444444444";
const ASSET="55555555-5555-4555-8555-555555555555";
const AUTH="Bearer original-user-jwt";
const brief=()=>({
  shop_id:SHOP,brief:"Festive boutique campaign",duration_days:1,
  start_date:"2026-10-26",timezone:"Asia/Kolkata",language:"en-IN",
  platforms:["linkedin","instagram"],media_asset_ids:[ASSET],offer:null,
});
const day=()=>({
  id:DAY,campaign_id:CAMP,shop_id:SHOP,day_index:1,scheduled_date:"2026-10-26",
  topic:"Festive shopping",linkedin:{post_text:"Shop styles today",hashtags:["#Retail"]},
  instagram:{caption:"Shop our styles",banner_asset_id:null,
    reel:{duration_seconds:30,aspect_ratio:"9:16",
      storyboard:[{start_seconds:0,duration_seconds:30,asset_id:ASSET,overlay_text:"Style"}],
      music_asset_id:null,cta:"Visit our store"}},
  review_status:"DRAFT",
});
const edit=()=>({topic:"Curated Diwali styles",linkedin:{post_text:"See the new collection",hashtags:["#Fashion"]},
  instagram:{...day().instagram,caption:"Available in store"}});
function setup({role="OWNER",badShop=false,stale=false,status="DRAFT",
                badAsset=false,failMutation=false,quota=null}={}) {
  const calls=[];
  let persisted=day();
  const fetchImpl=async(raw,req)=>{
    const url=new URL(raw);
    calls.push({url,req});
    if(req.method==="POST"){
      if(failMutation)throw new Error("ack lost");
      if(quota)return {ok:false,status:429,json:async()=>({code:quota})};
      const data=JSON.parse(req.body);
      if(url.pathname.endsWith("/campaigns"))return {ok:true,status:201,
        json:async()=>[{id:data.id,shop_id:data.shop_id,status:"PLANNING"}]};
      if(url.pathname.endsWith("/rpc/save_campaign_day")){
        if(!stale)persisted={...persisted,...data.p_changes};
        return {ok:true,status:200,json:async()=>!stale};
      }
      throw new Error("unexpected POST "+url.pathname);
    }
    let rows=[];
    switch(url.pathname.split("/").at(-1)){
      case "campaigns": rows=[{id:CAMP,shop_id:badShop?"99999999-9999-4999-8999-999999999999":SHOP,status}];break;
      case "shop_memberships": rows=role==="INACTIVE"?[]:
        [{shop_id:SHOP,user_id:USER,active:true,role}];break;
      case "campaign_days": rows=[persisted];break;
      case "media_assets": rows=badAsset?[]:[{id:ASSET,shop_id:SHOP,
        storage_bucket:"retailgrowth-media",object_path:SHOP+"/uploads/test.png",mime_type:"image/png"}];
        break;
    }
    return {ok:true,status:200,json:async()=>rows};
  };
  const writer=new CampaignDayWriter({origin:ORIGIN,publishableKey:"sb_publishable_test",fetchImpl});
  return {writer,calls,handle:createCampaignDayGateway({verifyJwt:async()=>USER,writer})};
}
test("brief rejects forged shop IDs, duplicate assets, unknown platforms, dates, zones and offers",()=>{
  const wrong=[
    {...brief(),unknown:"hidden"},
    {...brief(),shop_id:"../"},
    {...brief(),duration_days:8},
    {...brief(),duration_days:true},
    {...brief(),start_date:"2026-02-30"},
    {...brief(),timezone:"Invalid/Mars"},
    {...brief(),language:"en-US"},
    {...brief(),platforms:["instagram","instagram"]},
    {...brief(),media_asset_ids:[ASSET,ASSET]},
    {...brief(),offer:{description:"Valid",valid_until:"2020-01-01"}},
  ];
  for(const b of wrong)assert.throws(()=>validateCampaignBrief(b),ContractDenied);
  assert.equal(validateCampaignBrief(brief()).shop_id,SHOP);
});
test("complete v1 storyboard requires exactly 30 gapless seconds and canonical tenant linkage",()=>{
  const campaign={id:CAMP,shop_id:SHOP,status:"DRAFT",days:[day()]};
  assert.equal(validateCampaign(campaign),campaign);
  for(const d of [
    {...day(),instagram:{...day().instagram,reel:{...day().instagram.reel,
      storyboard:[{start_seconds:1,duration_seconds:30,asset_id:ASSET,overlay_text:"x"}]}}},
    {...day(),instagram:{...day().instagram,reel:{...day().instagram.reel,
      storyboard:[{start_seconds:0,duration_seconds:29,asset_id:ASSET,overlay_text:"x"}]}}},
    {...day(),shop_id:"99999999-9999-4999-8999-999999999999"},
    {...day(),review_status:"APPROVED"},
  ])assert.throws(()=>validateCampaign({...campaign,days:[d]}),ContractDenied);
});
test("campaign creation persists through one user-RLS INSERT; DB trigger owns outbox",async()=>{
  const {handle,calls}=setup();
  const r=await handle("POST","/api/campaigns",AUTH,brief());
  assert.equal(r.status,202);
  assert.match(r.jsonBody.campaign_id,/^[0-9a-f-]{36}$/);
  assert.equal(r.jsonBody.status,"PLANNING");
  const writes=calls.filter(c=>c.req.method==="POST");
  assert.equal(writes.length,1);
  const row=JSON.parse(writes[0].req.body);
  assert.equal(row.shop_id,SHOP);
  assert.equal(row.created_by,USER);
  assert.equal(row.status,"PLANNING");
  assert.equal(writes[0].req.headers.Authorization,"Bearer "+AUTH.slice(7));
  assert.equal(writes[0].req.headers.apikey,"sb_publishable_test");
  assert.ok(writes[0].url.pathname.endsWith("/rest/v1/campaigns"));
});
test("VIEWER, inactive or cross-shop create cannot persist or bill work",async()=>{
  for(const opts of [{role:"VIEWER"},{role:"INACTIVE"},{badAsset:true}]){
    const {handle,calls}=setup(opts);
    const r=await handle("POST","/api/campaigns",AUTH,brief());
    assert.equal(r.status,403);
    assert.equal(calls.filter(x=>x.req.method==="POST").length,0);
  }
});
test("day PATCH uses one atomic CAS RPC with old current fields and rereads save",async()=>{
  const {handle,calls}=setup();
  const r=await handle("PATCH","/api/campaigns/"+CAMP+"/days/"+DAY,AUTH,edit());
  assert.equal(r.status,200);
  assert.equal(r.jsonBody.day.topic,"Curated Diwali styles");
  const writes=calls.filter(x=>x.req.method==="POST");
  assert.equal(writes.length,1);
  assert.ok(writes[0].url.pathname.endsWith("/rpc/save_campaign_day"));
  const args=JSON.parse(writes[0].req.body);
  assert.equal(args.p_shop_id,SHOP);
  assert.equal(args.p_campaign_id,CAMP);
  assert.equal(args.p_day_id,DAY);
  assert.equal(args.p_expected.topic,"Festive shopping");
  assert.equal(args.p_changes.topic,"Curated Diwali styles");
});
test("CAS conflict, rejected editor role, non-DRAFT campaign block mutation",async()=>{
  for(const [opts,want] of [[{stale:true},409],[{role:"VIEWER"},403],
       [{status:"PLANNING"},409],[{role:"INACTIVE"},404],[{badAsset:true},403]]){
    const {handle,calls}=setup(opts);
    const r=await handle("PATCH","/api/campaigns/"+CAMP+"/days/"+DAY,AUTH,edit());
    assert.equal(r.status,want);
    assert.equal(calls.filter(x=>x.req.method==="POST").length,opts.stale?1:0);
  }
});
test("invalid edited storyboard, forged body, and day ID fail before SQL RPC",async()=>{
  for(const body of [
    {...edit(),admin_override:true},
    {...edit(),instagram:{...edit().instagram,reel:{...edit().instagram.reel,
      storyboard:[{start_seconds:0,duration_seconds:35,asset_id:ASSET,overlay_text:"bad"}]}}},
    {...edit(),linkedin:{post_text:"Hi",hashtags:[]}},
  ]){
    const {handle,calls}=setup();
    const r=await handle("PATCH","/api/campaigns/"+CAMP+"/days/"+DAY,AUTH,body);
    assert.equal(r.status,400);
    assert.equal(calls.filter(x=>x.req.method==="POST").length,0);
  }
  const {handle}=setup();
  assert.equal((await handle("PATCH","/api/campaigns/"+CAMP+"/days/"+SHOP,AUTH,edit())).status,404);
});
test("SQL quota denial maps to 429 without replay; ambiguous ACK terminates 503",async()=>{
  const denied=setup({quota:"RG002"});
  const r=await denied.handle("POST","/api/campaigns",AUTH,brief());
  assert.equal(r.status,429);
  assert.equal(r.jsonBody.error,"QUOTA_EXCEEDED");
  assert.equal(denied.calls.filter(x=>x.req.method==="POST").length,1);
  for(const [method,path,body] of [["POST","/api/campaigns",brief()],
    ["PATCH","/api/campaigns/"+CAMP+"/days/"+DAY,edit()]]){
    const lost=setup({failMutation:true});
    const res=await lost.handle(method,path,AUTH,body);
    assert.equal(res.status,503);
    assert.equal(lost.calls.filter(x=>x.req.method==="POST").length,1);
  }
});
test("missing JWT, forged JWT, unsupported method and path cause no database writes",async()=>{
  const {handle,calls}=setup();
  assert.equal((await handle("POST","/api/campaigns","",brief())).status,401);
  assert.equal((await handle("GET","/api/campaigns",AUTH,brief())).status,404);
  assert.equal((await handle("POST","/api/render-jobs/"+CAMP,AUTH,brief())).status,404);
  assert.equal(calls.length,0);
  const gate=createCampaignDayGateway({verifyJwt:async()=>{throw new AuthDenied()},writer:setup().writer});
  assert.equal((await gate("POST","/api/campaigns",AUTH,brief())).status,401);
});
