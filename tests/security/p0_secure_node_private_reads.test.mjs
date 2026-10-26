import test from "node:test";
import assert from "node:assert/strict";
import { PrivateReader } from "../../experiments/secure-node-http/src/private-reads.mjs";
import { createReadOnlyGateway } from "../../experiments/secure-node-http/src/routes.mjs";
import { UpstreamUnavailable } from "../../experiments/secure-node-http/src/security.mjs";

const HOST = "https://retail-test.supabase.co";
const USER = "22222222-2222-4222-8222-222222222222";
const SHOP = "11111111-1111-4111-8111-111111111111";
const FOREIGN_SHOP = "99999999-9999-4999-8999-999999999999";
const CAMP = "33333333-3333-4333-8333-333333333333";
const DAY = "44444444-4444-4444-8444-444444444444";
const POSTER = "55555555-5555-4555-8555-555555555555";
const PJOB = "66666666-6666-4666-8666-666666666666";
const REELJOB = "77777777-7777-4777-8777-777777777777";
const OUTPUT = "88888888-8888-4888-8888-888888888888";

const draft = () => ({
  id:POSTER, shop_id: SHOP, campaign_id:CAMP, day_id:DAY, status:"READY",
  template:"editorial",format:"portrait",business_name:"Test Retail",
  accent_color:"#123456",background_color:"#abcdef",offer_text:null,
  source_asset_id: OUTPUT,output_asset_id:OUTPUT,revision:1,
});
function fixture({revoked=false,foreign=false,jobStatus="SUCCEEDED",
                   mime="video/mp4",objectPath,poisonedSigned=false,
                   fakePosters=false,duplicateJobs=false}={}) {
  const calls=[];
  const fetchImpl=async (raw,opts) => {
    const url=new URL(raw);
    calls.push({url,opts});
    if(url.pathname.includes("/storage/v1/object/sign/")) {
      const rel=url.pathname.replace("/storage/v1","");
      return {ok:true,status:200,json:async()=>({
        signedURL:poisonedSigned?"https://other.example/token":rel+"?token=test-private-signature"
      })};
    }
    let rows=[];
    const table=url.pathname.split("/").at(-1);
    if(table==="campaigns")rows=[{id:CAMP,shop_id:SHOP,status:"DRAFT"}];
    if(table==="campaign_days")rows=[{id:DAY,shop_id:SHOP,campaign_id:CAMP,review_status:"DRAFT"}];
    if(table==="shop_memberships")rows=revoked?[]:[{shop_id:SHOP,user_id:USER,role:"OWNER",active:true}];
    if(table==="poster_drafts")rows=fakePosters?[]:[draft()];
    if(table==="poster_jobs")rows=[{id:PJOB,shop_id:foreign?FOREIGN_SHOP:SHOP,
      poster_id:POSTER,status:jobStatus,output_asset_id:OUTPUT,error_code:null}];
    if(table==="render_jobs")rows=[{id:REELJOB,shop_id:SHOP,status:jobStatus,
      output_asset_id:OUTPUT,error_code:null}];
    if(table==="media_assets")rows=[{id:OUTPUT,shop_id:SHOP,storage_bucket:"retailgrowth-media",
      mime_type:mime,object_path:objectPath ?? SHOP+"/reels/"+REELJOB+"/v1.mp4"}];
    if(duplicateJobs&&table==="poster_jobs")rows=[rows[0],rows[0]];
    return {ok:true,status:200,json:async()=>rows};
  };
  const reader = new PrivateReader({
    origin:HOST,publishableKey:"sb_publishable_test",fetchImpl,
  });
  return {reader,calls,fetchImpl};
}
const handleFor = reader=>createReadOnlyGateway({verifyJwt:async()=>USER,reader});
const authenticated = "Bearer fixture-token";

test("poster draft GET returns only Python v1-safe response keys and verifies membership",async()=>{
  const {reader,calls}=fixture();
  const result=await handleFor(reader)("GET","/api/poster-drafts/"+POSTER,authenticated);
  assert.equal(result.status,200);
  assert.deepEqual(result.jsonBody,{
    poster_id:POSTER,status:"READY",campaign_id:CAMP,day_id:DAY,template:"editorial",
    format:"portrait",business_name:"Test Retail",accent_color:"#123456",
    background_color:"#abcdef",offer_text:null,source_asset_id:OUTPUT,output_asset_id:OUTPUT,
  });
  assert.equal(calls.length,2);
  assert.equal(calls[1].url.searchParams.get("user_id"),"eq."+USER);
  assert.equal(calls[1].url.searchParams.get("shop_id"),"eq."+SHOP);
  assert.equal(calls[1].url.searchParams.get("active"),"eq.true");
});
test("poster list is gated by campaign/day lineage and contains exact v1 poster fields",async()=>{
  const {reader,calls}=fixture();
  const result=await handleFor(reader)("GET",
    "/api/campaigns/"+CAMP+"/days/"+DAY+"/posters",authenticated);
  assert.equal(result.status,200);
  assert.equal(result.jsonBody.posters[0].poster_id,POSTER);
  assert.equal(result.jsonBody.posters[0].job_id,PJOB);
  assert.equal(result.jsonBody.posters[0].job_status,"SUCCEEDED");
  assert.equal(result.jsonBody.posters[0].revision,1);
  assert.deepEqual(Object.keys(result.jsonBody),["posters"]);
  assert.equal(calls.at(-1).url.searchParams.get("shop_id"),"eq."+SHOP);
  assert.equal(calls.at(-1).url.searchParams.get("poster_id"),"in.("+POSTER+")");
  assert.equal((await handleFor(reader)("GET",
    "/api/campaigns/"+CAMP+"/days/"+FOREIGN_SHOP+"/posters",authenticated)).status,404);
});
test("cross-shop poster drafts and revoked membership return indistinguishable 404",async()=>{
  for(const options of [{revoked:true},{foreign:true}]){
    const {reader}=fixture(options);
    const result=await handleFor(reader)("GET","/api/poster-jobs/"+PJOB,authenticated);
    if(options.revoked)assert.equal(result.status,404);
    else assert.equal(result.status,404,"foreign job must never be returned");
  }
});
test("poster job GET exposes status only after RLS membership",async()=>{
  const {reader}=fixture();
  const result=await handleFor(reader)("GET","/api/poster-jobs/"+PJOB,authenticated);
  assert.deepEqual(result.jsonBody,{job_id:PJOB,poster_id:POSTER,status:"SUCCEEDED",
      output_asset_id:OUTPUT,error_code:null});
  assert.equal(result.status,200);
});
test("video download signs only tenant-bound private MP4, 60-second expiry with user JWT",async()=>{
  const {reader,calls}=fixture();
  const result=await handleFor(reader)("GET","/api/render-jobs/"+REELJOB+"/download",authenticated);
  assert.equal(result.status,200);
  assert.match(result.jsonBody.url,/^https:\/\/retail-test\.supabase\.co\/storage\/v1\/object\/sign\/retailgrowth-media\/1111/);
  assert.ok(result.jsonBody.url.includes("?token="));
  const request=calls.at(-1);
  assert.equal(request.opts.method,"POST");
  assert.equal(request.opts.headers.Authorization,"Bearer fixture-token");
  assert.equal(request.opts.headers.apikey,"sb_publishable_test");
  assert.equal(JSON.parse(request.opts.body).expiresIn,60);
  assert.equal(request.url.host,"retail-test.supabase.co");
});
test("not-yet-rendered media fails 409 without signing",async()=>{
  const {reader,calls}=fixture({jobStatus:"RUNNING"});
  const result=await handleFor(reader)("GET","/api/render-jobs/"+REELJOB+"/download",authenticated);
  assert.deepEqual({status:result.status,body:result.jsonBody},
    {status:409,body:{error:"OUTPUT_NOT_READY"}});
  assert.ok(!calls.some(c=>c.url.pathname.includes("/object/sign/")));
});
test("PNG cannot be served as MP4, and storage path crossing shop is denied",async()=>{
  for(const options of [{mime:"image/png"},{objectPath:FOREIGN_SHOP+"/reels/"+REELJOB+"/x.mp4"},
    {objectPath:SHOP+"/../outside.mp4"},{objectPath:SHOP+"/folder\\escape.mp4"},
    {objectPath:SHOP+"/folder/%2e%2e/secret.mp4"}]){
    const {reader,calls}=fixture(options);
    const res=await handleFor(reader)("GET","/api/render-jobs/"+REELJOB+"/download",authenticated);
    assert.equal(res.status,404);
    assert.ok(!calls.some(c=>c.url.pathname.includes("/object/sign/")));
  }
});
test("malicious provider signed URL cannot escape trusted Supabase origin",async()=>{
  const {reader}=fixture({poisonedSigned:true});
  const res=await handleFor(reader)("GET","/api/render-jobs/"+REELJOB+"/download",authenticated);
  assert.equal(res.status,503);
  assert.equal(res.jsonBody.error,"SERVICE_UNAVAILABLE");
});
test("poster PNG path must be under the exact poster ID and have image/png MIME",async()=>{
  for(const options of [
    {objectPath:SHOP+"/posters/"+POSTER+"/rev01.png",mime:"image/png",want:200},
    {objectPath:SHOP+"/posters/"+DAY+"/rev01.png",mime:"image/png",want:404},
    {objectPath:SHOP+"/posters/"+POSTER+"/rev01.png",mime:"video/mp4",want:404},
  ]){
    const {reader}=fixture(options);
    const res=await handleFor(reader)("GET","/api/poster-jobs/"+PJOB+"/download",authenticated);
    assert.equal(res.status,options.want);
  }
});
test("duplicate poster jobs and injected foreign-shop records fail closed",async()=>{
  for(const options of [{duplicateJobs:true},{foreign:true}]){
    const {reader}=fixture(options);
    const res=await handleFor(reader)("GET",
      "/api/campaigns/"+CAMP+"/days/"+DAY+"/posters",authenticated);
    assert.equal(res.status,503);
  }
});
test("missing JWT and mutating requests are denied BEFORE private storage",async()=>{
  const {reader,calls}=fixture();
  const handler=handleFor(reader);
  assert.equal((await handler("GET","/api/poster-jobs/"+PJOB+"/download","")).status,401);
  assert.equal((await handler("POST","/api/poster-jobs/"+PJOB+"/download",authenticated)).status,405);
  assert.equal((await handler("PATCH","/api/campaigns/"+CAMP+"/days/"+DAY,authenticated)).status,405);
  assert.equal((await handler("GET","/api/poster-drafts/"+POSTER+"/select",authenticated)).status,404);
  assert.equal(calls.length,0);
});
