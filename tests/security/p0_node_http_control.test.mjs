import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {routeControl} from "../../experiments/wineshop-node-http-control/src/routes.mjs";

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
  assert.equal(routeControl("GET",path,"Bearer invalid").status,401);
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
