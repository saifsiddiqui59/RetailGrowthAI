// Synthetic WineShopPOS-style Node v4 HTTP control. No retailer data or writes.
// Must NEVER be deployed over the existing Python Function App.
import { app } from "@azure/functions";
import { routeControl, syntheticJwtTransport } from "./routes.mjs";

const MARKER = Object.freeze({
  "X-P0-Control": "node-v4",
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff",
});

function respond(method, path, bearer = "") {
  const response = routeControl(method, path, bearer);
  return { ...response, headers: MARKER };
}

app.http("healthLite", {
  methods: ["GET"], authLevel: "anonymous", route: "p0-health-lite",
  handler: async () => respond("GET", "/api/p0-health-lite"),
});

app.http("campaignReadControl", {
  methods: ["GET"], authLevel: "anonymous", route: "campaigns/{campaignId}",
  handler: async (req) => respond(
    "GET", "/api/campaigns/" + req.params.campaignId,
    "" // Ignore platform/proxy Authorization in tenantless test control
  ),
});

app.http("unknownRouteControl", {
  methods: ["GET"], authLevel: "anonymous", route: "p0-249-missing",
  handler: async () => respond("GET", "/api/p0-249-missing"),
});

// Named Free SWA preview only. No Supabase credentials or signatures are used.
// Never echo the incoming header: emit only deterministic proof/not-proven.
app.http("syntheticJwtTransportControl", {
  methods: ["GET"], authLevel: "anonymous", route: "p0-jwt-transport-lite",
  handler: async (req) => ({
    ...syntheticJwtTransport(req.headers.get("x-rgai-supabase-jwt") || ""),
    headers: MARKER,
  }),
});
