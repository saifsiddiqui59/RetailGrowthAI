import { app } from "@azure/functions";
import { routeControl } from "./routes.mjs";
// Isolated Node control app. Do NOT deploy to existing Python Functions app.
app.http("healthLite", {methods:["GET"],authLevel:"anonymous",route:"p0-health-lite",
 handler:async()=>routeControl("GET","/api/p0-health-lite")});
app.http("campaignReadControl", {methods:["GET"],authLevel:"anonymous",route:"campaigns/{campaignId}",
 handler:async req=>routeControl("GET","/api/campaigns/"+req.params.campaignId,req.headers.get("authorization")||"")});
