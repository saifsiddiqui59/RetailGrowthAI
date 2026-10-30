import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {createSecureHttpDispatcher} from "../../experiments/secure-node-http/src/secure-api-dispatch.mjs";

const root=new URL("../../experiments/secure-node-http/src/",import.meta.url);
const preview=readFileSync(new URL("dev-write-preview-index.mjs",root),"utf8");
const canonical=readFileSync(new URL("index.mjs",root),"utf8");
const readOnly=readFileSync(new URL("dev-preview-index.mjs",root),"utf8");
const host="https://purple-dune-06b5da200-p0249writes.eastasia.2.azurestaticapps.net";
const token="testing.fixture.signed-by-verifier";
const id="11111111-1111-4111-8111-111111111111";
const req=(method,path,headers={},body='{"day_id":"'+id+'","preset":"instagram_reel_30s"}')=>({
 method,url:host+path,
 headers:new Headers({...(method!=="GET"?{"Content-Type":"application/json"}:{}),...headers}),
 async text(){return body;},
});

test("preview alone owns exact DEV JWT/RLS write routes, never production source",()=>{
 assert.match(preview,/https:\/\/jeearzffnjbvghwjjjrf[.]supabase[.]co/);
 assert.match(preview,/p0249writes[.]eastasia[.]2[.]azurestaticapps[.]net/);
 assert.match(preview,/createSupabaseVerifier/);
 assert.match(preview,/createReelIntentGateway/);
 assert.match(preview,/createPosterWriteGateway/);
 assert.match(preview,/createCampaignDayGateway/);
 assert.match(preview,/createReadOnlyGateway/);
 assert.match(preview,/writesEnabled: true/);
 assert.match(preview,/renderWritesEnabled: true/);
 assert.match(readOnly,/writesEnabled: false/);
 assert.match(readOnly,/renderWritesEnabled: false/);
 assert.match(canonical,/secureReadCampaign/);
 assert.doesNotMatch(canonical,/previewCampaignCreate|previewReelSubmit/);
 assert.equal((preview.match(/publicRoute\("/g)||[]).length,13);
 assert.equal((preview.match(/\["POST"\]/g)||[]).length,5);
 assert.equal((preview.match(/\["PATCH"\]/g)||[]).length,1);
 assert.match(preview,/authLevel: "anonymous", handler: api/);
 assert.doesNotMatch(preview,/sb_secret_|RETAIL_SUPABASE_SERVICE_ROLE_KEY|QueueClient|createClient\(/);
 assert.doesNotMatch(preview,/VITE_CAMPAIGN_API_BASE_URL|wineshop|wine-shop/i);
});
test("untrusted origin, missing JWT and bogus mutation paths fail without calling a backend",async()=>{
 const calls=[];
 const gate=async(...args)=>{calls.push(args);return {status:202,jsonBody:{ok:true}};};
 const dispatch=createSecureHttpDispatcher({
  readGateway:gate,campaignGateway:gate,posterGateway:gate,reelGateway:gate,
  writesEnabled:true,renderWritesEnabled:true,allowedOrigin:host
 });
 const base="/api/campaigns/"+id;
 for(const path of ["/api/campaigns",base+"/renders",base+"/posters","/api/poster-drafts/"+id+"/renders","/api/poster-drafts/"+id+"/select"]){
  assert.equal((await dispatch(req("POST",path))).status,401);
 }
 assert.equal((await dispatch(req("PATCH",base+"/days/"+id))).status,401);
 assert.equal((await dispatch(req("POST",base+"/renders",{"Origin":"https://attacker.example","x-rgai-supabase-jwt":token}))).status,403);
 assert.equal((await dispatch(req("POST",base+"/renders",{"Sec-Fetch-Site":"cross-site","x-rgai-supabase-jwt":token}))).status,403);
 assert.equal((await dispatch(req("POST","/api/unknown",{"x-rgai-supabase-jwt":token}))).status,404);
 assert.equal((await dispatch(req("DELETE",base+"/renders",{"x-rgai-supabase-jwt":token}))).status,405);
 assert.equal(calls.length,0);
});
test("expected six safe route handlers dispatch with original JWT only; no blind replay",async()=>{
 const calls=[];
 const mock=(kind)=>async(...args)=>{calls.push({kind,args});return {status:202,jsonBody:{status:"QUEUED"}};};
 const dispatch=createSecureHttpDispatcher({
  readGateway:mock("read"),campaignGateway:mock("campaign"),posterGateway:mock("poster"),
  reelGateway:mock("reel"),writesEnabled:true,renderWritesEnabled:true,allowedOrigin:host
 });
 const values=[
  ["POST","/api/campaigns","campaign"],
  ["PATCH","/api/campaigns/"+id+"/days/"+id,"campaign"],
  ["POST","/api/campaigns/"+id+"/posters","poster"],
  ["POST","/api/poster-drafts/"+id+"/renders","poster"],
  ["POST","/api/poster-drafts/"+id+"/select","poster"],
  ["POST","/api/campaigns/"+id+"/renders","reel"],
 ];
 for(const [method,path,kind] of values){
  let result=await dispatch(req(method,path,{"Origin":host,"Sec-Fetch-Site":"same-origin","x-rgai-supabase-jwt":token}));
  assert.equal(result.status,202);
  assert.equal(calls.at(-1).kind,kind);
  assert.equal(calls.at(-1).args[2],"Bearer "+token);
 }
 assert.equal(calls.length,6);
});
