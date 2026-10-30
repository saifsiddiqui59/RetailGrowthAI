/**
 * P0 #249 REAL SUPABASE JWT FREE SWA PREVIEW ONLY.
 *
 * The target is the EXISTING RetailGrowthAI Free SWA named preview
 * `p0249secure`, never the live customer site. Every route uses asymmetric
 * Supabase JWKS verification and caller-token PostgREST RLS.
 * ALL MUTATIONS ARE OFF. No service_role, secrets, queues, or billed provider.
 * DO NOT use this as proof of actual signed-in retailer E2E yet.
 */
import { app } from "@azure/functions";
import { createSupabaseVerifier } from "./security.mjs";
import { ReelIntentWriter } from "./reel-intent.mjs";
import { createReadOnlyGateway } from "./routes.mjs";
import { createCampaignDayGateway } from "./campaign-day-writes.mjs";
import { createPosterWriteGateway } from "./poster-writes.mjs";
import { createReelIntentGateway } from "./reel-intent.mjs";
import { createSecureHttpDispatcher } from "./secure-api-dispatch.mjs";

// Publishable key: first-party verified *public* DEV-only Supabase API key.
// Never load the service role/secret key, and never read other project config.
const DEV_SUPABASE_URL = "https://jeearzffnjbvghwjjjrf.supabase.co";
const DEV_PUBLISHABLE_KEY = "sb_publishable_tEqNinZfiLzrAyF4E1pAeQ_vZRvJYjq";
const DEV_PREVIEW_ORIGIN =
  "https://purple-dune-06b5da200-p0249secure.eastasia.2.azurestaticapps.net";
if ((process.env.RETAIL_SUPABASE_URL &&
     process.env.RETAIL_SUPABASE_URL !== DEV_SUPABASE_URL) ||
    (process.env.RETAIL_SUPABASE_PUBLISHABLE_KEY &&
     process.env.RETAIL_SUPABASE_PUBLISHABLE_KEY !== DEV_PUBLISHABLE_KEY)) {
  throw new Error("P0249_PREVIEW_WRONG_SUPABASE_PROJECT");
}
const verifyJwt = createSupabaseVerifier({ origin: DEV_SUPABASE_URL });
const writer = new ReelIntentWriter({
  origin: DEV_SUPABASE_URL,
  publishableKey: DEV_PUBLISHABLE_KEY,
});
const dispatch = createSecureHttpDispatcher({
  readGateway: createReadOnlyGateway({verifyJwt, reader: writer}),
  campaignGateway: createCampaignDayGateway({verifyJwt, writer}),
  posterGateway: createPosterWriteGateway({verifyJwt, writer}),
  reelGateway: createReelIntentGateway({verifyJwt, writer}),
  // Hard-coded disabled; an env setting must NEVER activate billable writes.
  writesEnabled: false,
  renderWritesEnabled: false,
  allowedOrigin: DEV_PREVIEW_ORIGIN,
});

function api(req) {
  return dispatch(req);
}
const publicRoute = (name, route, methods) => app.http(name, {
  route, methods, authLevel: "anonymous", handler: api,
});
publicRoute("previewReadCampaign", "campaigns/{id}", ["GET"]);
publicRoute("previewReadRenderJob", "render-jobs/{id}", ["GET"]);
publicRoute("previewRenderDownload", "render-jobs/{id}/download", ["GET"]);
publicRoute("previewPosterDraft", "poster-drafts/{id}", ["GET"]);
publicRoute("previewPosterList", "campaigns/{id}/days/{dayId}/posters", ["GET"]);
publicRoute("previewPosterJob", "poster-jobs/{id}", ["GET"]);
publicRoute("previewPosterDownload", "poster-jobs/{id}/download", ["GET"]);

app.http("previewSecureHealth", {
  route: "p0-secure-health",
  methods: ["GET"],
  authLevel: "anonymous",
  handler: async () => ({
    status: 200,
    headers: {
      "Cache-Control": "no-store",
      "X-P0249-Secure-Preview": "real-jwks-rls-readonly-v1",
      "X-Content-Type-Options": "nosniff",
    },
    jsonBody: {status: "READ_ONLY_PREVIEW"},
  }),
});
