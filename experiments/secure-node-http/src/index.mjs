/**
 * SOURCE ONLY. Not wired to live RetailGrowthAI SWA or to p0249node preview.
 * A separately reviewed client must send its Supabase access token in this
 * custom header because managed SWA may handle Authorization internally.
 * The header is never trusted without asymmetric JWKS verification and RLS.
 */
import { app } from "@azure/functions";
import { createSupabaseVerifier } from "./security.mjs";
import { TenantReader } from "./tenant-read.mjs";
import { createReadOnlyGateway } from "./routes.mjs";

const origin = process.env.RETAIL_SUPABASE_URL;
const publishableKey = process.env.RETAIL_SUPABASE_PUBLISHABLE_KEY;
const handler = createReadOnlyGateway({
  verifyJwt: createSupabaseVerifier({ origin }),
  reader: new TenantReader({ origin, publishableKey }),
});

async function handle(req) {
  const rawToken = req.headers.get("x-rgai-supabase-jwt") || "";
  // Never echo the JWT, cookie, body, signed link or sensitive header to logs.
  return handler("GET", new URL(req.url).pathname, rawToken ? "Bearer " + rawToken : "");
}
app.http("secureReadCampaign", {
  route: "campaigns/{id}", methods: ["GET"], authLevel: "anonymous",
  handler: handle,
});
app.http("secureReadRenderJob", {
  route: "render-jobs/{id}", methods: ["GET"], authLevel: "anonymous",
  handler: handle,
});
