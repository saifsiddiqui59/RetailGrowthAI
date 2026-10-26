import test from "node:test";
import assert from "node:assert/strict";
import {routeControl} from "../src/routes.mjs";
test("synthetic anonymous protected read returns 401",()=>{
 assert.deepEqual(routeControl("GET","/api/campaigns/fake"),{status:401,jsonBody:{error:"AUTH_REQUIRED"}});
});
test("bearer cannot retrieve user/shop data",()=>{
 assert.deepEqual(routeControl("GET","/api/campaigns/fake","Bearer fake"),{status:503,jsonBody:{error:"CONTROL_NO_TENANT_IMPLEMENTATION"}});
});
test("lightweight health and unknown routes are bounded and deterministic",()=>{
 assert.equal(routeControl("GET","/api/p0-health-lite").status,200);
 assert.equal(routeControl("GET","/api/nonexistent").status,404);
 assert.equal(routeControl("POST","/api/campaigns/fake").status,405);
});
