import test from "node:test";
import assert from "node:assert/strict";
import { createSecureHttpDispatcher } from "../../experiments/secure-node-http/src/secure-api-dispatch.mjs";

const SITE = "https://purple-dune-06b5da200.2.azurestaticapps.net";
const TOKEN = "signed.synthetic.supabase";
const api = (path) => SITE + "/api/" + path;
const calls = [];
const mkGateway = (kind) => async (...args) => {
  calls.push({ kind, args });
  return { status: kind === "read" ? 200 : 202, jsonBody: { kind } };
};
const readGateway = mkGateway("read");
const campaignGateway = mkGateway("campaign");
const posterGateway = mkGateway("poster");
const reelGateway = mkGateway("reel");
function req(method, url, opts = {}) {
  return {
    method, url,
    headers: new Headers({
      "x-rgai-supabase-jwt": TOKEN,
      ...(method !== "GET" ? { "content-type": "application/json" } : {}),
      ...(opts.headers || {}),
    }),
    async text() { return opts.body ?? '{"day_id":"11111111-1111-4111-8111-111111111111","preset":"instagram_reel_30s"}'; },
  };
}
function gateway(opts = {}) {
  calls.length = 0;
  return createSecureHttpDispatcher({
    readGateway, campaignGateway, posterGateway, reelGateway,
    allowedOrigin: SITE, ...opts,
  });
}

test("source-only default forwards verified-transport candidate only to existing GET JWT gateway", async () => {
  const dispatch = gateway();
  const value = await dispatch(req("GET", api("campaigns/11111111-1111-4111-8111-111111111111")));
  assert.equal(value.status, 200);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].kind, "read");
  assert.equal(calls[0].args[2], "Bearer " + TOKEN);
  const denied = await dispatch(req("POST", api("campaigns")));
  assert.deepEqual(denied.jsonBody, {error: "SECURE_WRITE_NOT_ENABLED"});
  assert.equal(calls.length, 1);
});

test("SWA Authorization principal/header alone cannot substitute for original Supabase JWT", async () => {
  const dispatch = gateway();
  const request = req("GET", api("render-jobs/11111111-1111-4111-8111-111111111111"));
  request.headers.delete("x-rgai-supabase-jwt");
  request.headers.set("authorization", "Bearer fake-SWA-principal");
  assert.equal((await dispatch(request)).status, 401);
  assert.equal(calls.length, 0);
  request.headers.set("x-rgai-supabase-jwt", "attacker,other");
  assert.equal((await dispatch(request)).status, 401);
  request.headers.set("x-rgai-supabase-jwt", "ab");
  assert.equal((await dispatch(request)).status, 401);
  request.headers.set("x-rgai-supabase-jwt", "x".repeat(8193));
  assert.equal((await dispatch(request)).status, 401);
});

test("same-origin browser only, no reflected CORS for hostile Origin or fetch site", async () => {
  const dispatch = gateway({ writesEnabled: true });
  const foreign = req("POST", api("campaigns"), { headers: {
    origin: "https://attacker.example", "sec-fetch-site": "cross-site",
  }});
  const response = await dispatch(foreign);
  assert.equal(response.status, 403);
  assert.equal(response.headers["Access-Control-Allow-Origin"], undefined);
  assert.equal(calls.length, 0);
  const sameSiteButDifferentOrigin = req("GET", api("campaigns/11111111-1111-4111-8111-111111111111"),
    {headers:{origin:"https://somethingelse.azurestaticapps.net","sec-fetch-site":"same-site"}});
  assert.equal((await dispatch(sameSiteButDifferentOrigin)).status, 403);
  const same = req("POST", api("campaigns"), { headers:{
    origin: SITE, "sec-fetch-site": "same-origin",
  }});
  assert.equal((await dispatch(same)).status, 202);
  assert.equal(calls.length, 1);
});

test("fail closed for unknown writes, methods, non-HTTPS and query-bearing paths", async () => {
  const dispatch = gateway({writesEnabled:true,renderWritesEnabled:true});
  assert.equal((await dispatch(req("POST",api("unknown")))).status,404);
  assert.equal((await dispatch(req("PUT",api("campaigns")))).status,405);
  assert.equal((await dispatch(req("POST","http://insecure.example/api/campaigns"))).status,400);
  assert.equal((await dispatch(req("POST",api("campaigns") + "?override=1"))).status,400);
  assert.equal(calls.length,0);
});

test("write routes dispatch to existing campaign/poster/Reel gateways, never a queue", async () => {
  const dispatch = gateway({writesEnabled:true,renderWritesEnabled:true});
  const m = [
    ["POST","campaigns","campaign"],
    ["PATCH","campaigns/11111111-1111-4111-8111-111111111111/days/22222222-2222-4222-8222-222222222222","campaign"],
    ["POST","campaigns/11111111-1111-4111-8111-111111111111/posters","poster"],
    ["POST","poster-drafts/11111111-1111-4111-8111-111111111111/renders","poster"],
    ["POST","poster-drafts/11111111-1111-4111-8111-111111111111/select","poster"],
    ["POST","campaigns/11111111-1111-4111-8111-111111111111/renders","reel"],
  ];
  for(const [method,path,kind] of m) {
    assert.equal((await dispatch(req(method,api(path)))).status,202);
    assert.equal(calls.at(-1).kind,kind);
    assert.equal(calls.at(-1).args[2],"Bearer "+TOKEN);
  }
  assert.equal(calls.length,m.length);
});

test("Reel render intent remains independently OFF when other DB-backed writes enabled", async () => {
  const dispatch = gateway({writesEnabled:true});
  const denied = await dispatch(req("POST",api("campaigns/11111111-1111-4111-8111-111111111111/renders")));
  assert.equal(denied.status,503);
  assert.equal(calls.length,0);
  await dispatch(req("POST",api("campaigns")));
  assert.equal(calls.length,1);
});

test("JSON body checks stop malformed/oversized/untrusted mutation before DB call", async () => {
  const dispatch = gateway({writesEnabled:true});
  const target = api("campaigns");
  for (const request of [
    req("POST",target,{body:"["}),
    req("POST",target,{body:"[1]"}),
    req("POST",target,{body:"null"}),
    req("POST",target,{body:"x".repeat(65537)}),
    req("POST",target,{headers:{"content-type":"text/plain"}}),
    req("POST",target,{headers:{"content-length":"65537"}}),
  ]) {
    const response=await dispatch(request);
    assert.equal(response.status,400);
  }
  assert.equal(calls.length,0);
});

test("lost acknowledgement remains unconfirmed, never automatically retries the writer",async()=>{
  let writerCalls=0;
  const dispatch = createSecureHttpDispatcher({
    readGateway,
    posterGateway,
    campaignGateway: async()=>{writerCalls++;throw new Error("upstream committed but response lost");},
    reelGateway,
    writesEnabled:true,
    allowedOrigin:SITE,
  });
  const response=await dispatch(req("POST",api("campaigns")));
  assert.equal(response.status,503);
  assert.deepEqual(response.jsonBody,{error:"SERVICE_UNAVAILABLE"});
  assert.equal(JSON.stringify(response).includes(TOKEN),false);
  assert.equal(writerCalls,1);
});

test("cannot enable write routes without exact trusted origin / DB writer dependencies",()=>{
  assert.throws(()=>createSecureHttpDispatcher({readGateway,writesEnabled:true,posterGateway,campaignGateway}),/MISSING_PINNED_ALLOWED_ORIGIN/);
  assert.throws(()=>createSecureHttpDispatcher({readGateway,writesEnabled:true,allowedOrigin:SITE}),/MISSING_WRITE_GATEWAYS/);
  assert.throws(()=>createSecureHttpDispatcher({readGateway,writesEnabled:true,posterGateway,campaignGateway,renderWritesEnabled:true,allowedOrigin:SITE}),/REEL_REQUIRES_APPROVED_WRITE_GATEWAY/);
});
