import test from "node:test";
import assert from "node:assert/strict";
import { generateKeyPairSync, sign } from "node:crypto";
import { readFileSync } from "node:fs";
import { createSupabaseVerifier, AuthDenied, UpstreamUnavailable, canonicalUuid } from "../../experiments/secure-node-http/src/security.mjs";
import { TenantReader } from "../../experiments/secure-node-http/src/tenant-read.mjs";
import { createReadOnlyGateway } from "../../experiments/secure-node-http/src/routes.mjs";

const SUPABASE = "https://test-retailgrowth.supabase.co";
const NOW = Date.parse("2026-10-26T09:00:00Z");
const SHOP = "11111111-1111-4111-8111-111111111111";
const USER = "22222222-2222-4222-8222-222222222222";
const CAMPAIGN = "33333333-3333-4333-8333-333333333333";
const JOB = "44444444-4444-4444-8444-444444444444";
const OTHER = "55555555-5555-4555-8555-555555555555";
const base64 = (object) => Buffer.from(JSON.stringify(object)).toString("base64url");
function jwtFixture(alg="ES256") {
  const keypair=alg==="ES256"
    ? generateKeyPairSync("ec",{namedCurve:"P-256"})
    : generateKeyPairSync("rsa",{modulusLength:2048});
  const jwk={...keypair.publicKey.export({format:"jwk"}), kid:"trusted-kid",alg,use:"sig"};
  const original={
    iss:SUPABASE+"/auth/v1", aud:"authenticated", role:"authenticated",
    iat:Math.floor(NOW/1000)-60, exp:Math.floor(NOW/1000)+600,sub:USER,
    is_anonymous:false,
  };
  function token(changes={},headerChanges={}) {
    const h={alg,kid:"trusted-kid",typ:"JWT",...headerChanges};
    const payload={...original,...changes};
    const signed=base64(h)+"."+base64(payload);
    const signature=sign("sha256",Buffer.from(signed),{
      key:keypair.privateKey,...(alg==="ES256"?{dsaEncoding:"ieee-p1363"}:{}),
    });
    return signed+"."+signature.toString("base64url");
  }
  return {jwk,token};
}
function jwksFetch(jwk) {
  const calls=[];
  async function fetchImpl(url,init) {
    calls.push({url,init});
    return {ok:true,text:async()=>JSON.stringify({keys:[jwk]})};
  }
  return {calls,fetchImpl};
}
test("ES256 pinned JWT verifies without relying on SWA native principal", async()=>{
  const {jwk,token}=jwtFixture();
  const network=jwksFetch(jwk);
  const v=createSupabaseVerifier({origin:SUPABASE,fetchImpl:network.fetchImpl,now:()=>NOW});
  assert.equal(await v(token()),USER);
  assert.equal(await v(token()),USER);
  assert.equal(network.calls.length,1,"JWKS response must be cached");
  assert.equal(network.calls[0].url,SUPABASE+"/auth/v1/.well-known/jwks.json");
  assert.equal(network.calls[0].init.method,"GET");
});
test("RS256 pinned JWT verifies without shared secret",async()=>{
  const {jwk,token}=jwtFixture("RS256");
  const v=createSupabaseVerifier({origin:SUPABASE,fetchImpl:jwksFetch(jwk).fetchImpl,now:()=>NOW});
  assert.equal(await v(token()),USER);
});
test("signed but invalid claims reject for wrong tenant, expired, future, non-user",async()=>{
  const {jwk,token}=jwtFixture();
  const v=createSupabaseVerifier({origin:SUPABASE,fetchImpl:jwksFetch(jwk).fetchImpl,now:()=>NOW});
  for(const bad of [
    {aud:"other"},{iss:"https://evil.test/auth/v1"},{role:"service_role"},
    {exp:Math.floor(NOW/1000)},{iat:Math.floor(NOW/1000)+60},
    {is_anonymous:true},{sub:"not-uuid"},{nbf:Math.floor(NOW/1000)+60},
  ]) await assert.rejects(()=>v(token(bad)),AuthDenied);
});
test("alg confusion, malicious JWKS header, corrupted signature and random kid all deny",async()=>{
  const {jwk,token}=jwtFixture();
  const v=createSupabaseVerifier({origin:SUPABASE,fetchImpl:jwksFetch(jwk).fetchImpl,now:()=>NOW});
  for(const bad of [
    token({}, {alg:"none"}),token({}, {alg:"HS256"}),token({}, {kid:"other"}),
    token({}, {jku:"https://evil.test/keys"}), token({}, {crit:["custom"]}),
    token().slice(0,-3)+"abc",
  ]) await assert.rejects(()=>v(bad),AuthDenied);
});
test("broken JWKS never falls back to accepting JWT",async()=>{
  const {token}=jwtFixture();
  const v=createSupabaseVerifier({origin:SUPABASE,now:()=>NOW,fetchImpl:async()=>{throw Error("offline")}});
  await assert.rejects(()=>v(token()),UpstreamUnavailable);
});
test("strict origin and canonical UUID rules",()=>{
  for(const origin of ["http://test.invalid","https://example.com/path","https://alice@example.com","https://example.com:8443"]) {
    assert.throws(()=>createSupabaseVerifier({origin}));
  }
  assert.equal(canonicalUuid(USER),USER);
  for(const bad of ["aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa".toUpperCase(),"../other","not-uuid","",null]) assert.throws(()=>canonicalUuid(bad));
});
function tenantFetch({rows={},rejectMembership=false,badCrossShop=false}={}){
  const calls=[];
  async function fetchImpl(url,init) {
    const u=new URL(url);
    calls.push({u,init});
    let data=[];
    switch(u.pathname.split("/").at(-1)){
      case "campaigns":
        data=[{id:CAMPAIGN,shop_id:SHOP,status:"DRAFT"}];break;
      case "shop_memberships":
        data=rejectMembership?[]:[{shop_id:SHOP,user_id:USER,role:"OWNER",active:true}];break;
      case "campaign_days":
        data=[{id:OTHER,shop_id:badCrossShop?OTHER:SHOP,campaign_id:CAMPAIGN,topic:"Demo"}];break;
      case "render_jobs":
        data=[{id:JOB,shop_id:SHOP,status:"SUCCEEDED",output_asset_id:null,error_code:null}];break;
    }
    return {ok:true,status:200,json:async()=>data};
  }
  return {calls,fetchImpl};
}
test("RLS campaign GET sends current user JWT + only public key, verifies membership and shop equality",async()=>{
  const net=tenantFetch();
  const reader=new TenantReader({origin:SUPABASE,publishableKey:"sb_publishable_safe",fetchImpl:net.fetchImpl});
  const response=await reader.campaign("private-user-token",USER,CAMPAIGN);
  assert.equal(response.id,CAMPAIGN);
  assert.equal(response.days.length,1);
  assert.equal(net.calls.length,3);
  for(const {u,init} of net.calls){
    assert.equal(u.origin,SUPABASE);
    assert.equal(init.method,"GET");
    assert.equal(init.headers.apikey,"sb_publishable_safe");
    assert.equal(init.headers.Authorization,"Bearer private-user-token");
    assert.equal(init.redirect,"error");
  }
  assert.equal(net.calls[1].u.searchParams.get("active"),"eq.true");
  assert.equal(net.calls[1].u.searchParams.get("user_id"),"eq."+USER);
  assert.equal(net.calls[2].u.searchParams.get("shop_id"),"eq."+SHOP);
});
test("cross-shop, revoked or inconsistent RLS data fail closed",async()=>{
  for(const opts of [{rejectMembership:true},{badCrossShop:true}]){
    const reader=new TenantReader({origin:SUPABASE,publishableKey:"sb_publishable_safe",fetchImpl:tenantFetch(opts).fetchImpl});
    if(opts.rejectMembership)assert.equal(await reader.campaign("token",USER,CAMPAIGN),null);
    else await assert.rejects(()=>reader.campaign("token",USER,CAMPAIGN),UpstreamUnavailable);
  }
});
test("read only secure API preserves 200/401/404/405/503 with no token, no mutations",async()=>{
  const reader=new TenantReader({origin:SUPABASE,publishableKey:"sb_publishable_safe",fetchImpl:tenantFetch().fetchImpl});
  const handler=createReadOnlyGateway({verifyJwt:async()=>USER,reader});
  assert.equal((await handler("GET","/api/campaigns/"+CAMPAIGN,"Bearer fixture")).status,200);
  assert.equal((await handler("GET","/api/render-jobs/"+JOB,"Bearer fixture")).status,200);
  assert.equal((await handler("GET","/api/campaigns/"+CAMPAIGN,"")).status,401);
  assert.equal((await handler("POST","/api/campaigns","Bearer fixture")).status,405);
  assert.equal((await handler("GET","/api/unknown","Bearer fixture")).status,404);
  assert.equal((await handler("GET","/api/campaigns/bad-id","Bearer fixture")).status,400);
  const denying=createReadOnlyGateway({verifyJwt:async()=>{throw new AuthDenied();},reader});
  assert.equal((await denying("GET","/api/campaigns/"+CAMPAIGN,"Bearer invalid")).status,401);
});
test("read-only adapter has no cross-tenant bypass or service-role credential",()=>{
  const code=["src/security.mjs","src/tenant-read.mjs","src/routes.mjs"].map(
    name=>readFileSync(new URL("../../experiments/secure-node-http/"+name,import.meta.url),"utf8")).join("\n");
  assert.doesNotMatch(code,/RETAIL_SUPABASE_SERVICE_ROLE_KEY|method:\s*["']POST["']/);
  assert.match(code,/startsWith\("sb_secret_"\)/, "privileged keys must be rejected");
  assert.match(code,/createPublicKey/);
  assert.match(code,/shop_memberships/);
});
