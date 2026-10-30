import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {routeControl, syntheticJwtTransport} from "../../experiments/wineshop-node-http-control/src/routes.mjs";

const root = new URL("../../experiments/wineshop-node-http-control/", import.meta.url);
test("control package discovers Node v4 Functions main entrypoint", () => {
  const config = JSON.parse(readFileSync(new URL("package.json", root), "utf8"));
  assert.equal(config.main, "src/index.mjs");
  assert.ok(config.dependencies["@azure/functions"]);
  assert.equal(Object.keys(config.dependencies).length, 1);
});
test("protected reads deny anonymous and nonvalidated bearer tokens", () => {
  const path="/api/campaigns/not-a-customer-id";
  assert.equal(routeControl("GET",path).status,401);
  assert.equal(routeControl("GET",path,"Bearer invalid").status,503);
});
test("no customer write path and expected benign control responses", () => {
  assert.equal(routeControl("POST","/api/campaigns/test").status,405);
  assert.equal(routeControl("GET","/api/p0-health-lite").status,200);
  assert.equal(routeControl("GET","/api/nonexistent").status,404);
});
test("control source cannot ship a service role or real tenant backend", () => {
  const source=readFileSync(new URL("src/routes.mjs", root),"utf8");
  assert.doesNotMatch(source, /RETAIL_SUPABASE_SERVICE_ROLE_KEY|createClient|send_message|new QueueClient/);
});

test("synthetic SWA JWT header proof cannot be confused with a real Supabase token", () => {
  assert.equal(syntheticJwtTransport().status, 401);
  assert.equal(syntheticJwtTransport("Bearer p0249-public-synthetic-header-proof").status,401);
  assert.equal(syntheticJwtTransport("real.jwt.token").status,401);
  const result=syntheticJwtTransport("p0249-public-synthetic-header-proof");
  assert.equal(result.status,200);
  assert.deepEqual(result.jsonBody,{transport:"CUSTOM_HEADER_DELIVERED_SYNTHETIC_ONLY"});
  assert.doesNotMatch(JSON.stringify(result),/p0249-public-synthetic-header-proof/);
});
