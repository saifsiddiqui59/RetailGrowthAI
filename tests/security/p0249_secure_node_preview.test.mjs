import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";

const root = new URL("../../experiments/secure-node-http/", import.meta.url);
const read = path => readFileSync(new URL(path,root),"utf8");
test("p0249secure deploy target reuses Free SWA Node22 and never a customer SPA",()=>{
  const config=JSON.parse(read("site/staticwebapp.config.json"));
  assert.equal(config.platform.apiRuntime,"node:22");
  assert.match(config.globalHeaders["X-Robots-Tag"],/noindex/);
  assert.match(read("site/index.html"),/Not a customer application/);
  assert.equal(JSON.parse(read("package.json")).main,"src/index.mjs");
  assert.equal(JSON.parse(read("host.json")).extensions.http.routePrefix,"api");
});
test("real JWT verifier is pinned to exact existing DEV project and signature boundary",()=>{
  const index=read("src/dev-preview-index.mjs"),security=read("src/security.mjs");
  assert.match(index,/https:\/\/jeearzffnjbvghwjjjrf[.]supabase[.]co/);
  assert.match(index,/sb_publishable_tEqNinZfiLzrAyF4E1pAeQ_vZRvJYjq/);
  assert.match(index,/createSupabaseVerifier/);
  assert.match(security,/cryptoVerify/);
  assert.match(security,/\.well-known\/jwks[.]json/);
  assert.match(security,/claims[.]iss !== issuer/);
  assert.match(security,/claims[.]role !== "authenticated"/);
  assert.match(index,/createReadOnlyGateway/);
  assert.match(index,/createSecureHttpDispatcher/);
  for(const source of [index,read("src/secure-api-dispatch.mjs")]){
    assert.doesNotMatch(source,/RETAIL_SUPABASE_SERVICE_ROLE_KEY|sb_secret_|createClient\(|QueueClient/);
  }
});
test("ALL real preview mutations remain hard-disabled and all registered APIs GET-only",()=>{
  const index=read("src/dev-preview-index.mjs");
  assert.match(index,/writesEnabled: false/);
  assert.match(index,/renderWritesEnabled: false/);
  assert.equal((index.match(/publicRoute\("/g)||[]).length,7);
  assert.equal((index.match(/\["GET"\]/g)||[]).length,8);
  assert.doesNotMatch(index,/publicRoute\(.+?\["POST"\]/);
  assert.doesNotMatch(index,/app.http\(.+?\["POST"\]/);
  assert.doesNotMatch(index,/process[.]env[.]RETAIL_P0_NODE_WRITES_ENABLED/);
  assert.match(index,/p0-secure-health/);
  assert.match(index,/real-jwks-rls-readonly-v1/);
});
test("No preview source can use WineShopPOS endpoints or real service-role secret",()=>{
  const index=read("src/dev-preview-index.mjs");
  assert.doesNotMatch(index,/WineShopPOS|https:\/\/.*?wineshop|azurewebsites[.]net/);
  assert.doesNotMatch(index,/process[.]env[.]RETAIL_SUPABASE_SERVICE_ROLE_KEY|sb_secret_/);
  const packageJson=JSON.parse(read("package.json"));
  assert.equal(Object.keys(packageJson.dependencies).length,1);
  assert.ok(packageJson.dependencies["@azure/functions"]);
});
