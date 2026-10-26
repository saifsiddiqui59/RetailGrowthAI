import { AuthDenied, UpstreamUnavailable, canonicalUuid } from "./security.mjs";

function json(status, jsonBody) {
  return {
    status,
    jsonBody,
    headers: {
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
      "X-RGAI-Secure-Adapter": "read-only-v1",
    },
  };
}
function draftView(draft) {
  return {
    poster_id: draft.id, status: draft.status, campaign_id: draft.campaign_id,
    day_id: draft.day_id, template: draft.template, format: draft.format,
    business_name: draft.business_name, accent_color: draft.accent_color,
    background_color: draft.background_color, offer_text: draft.offer_text ?? null,
    source_asset_id: draft.source_asset_id,
    output_asset_id: draft.output_asset_id ?? null,
  };
}
function listView(rows) {
  return { posters: rows.map(row => ({
    poster_id: row.id, status: row.status, revision: row.revision,
    template: row.template, format: row.format,
    business_name: row.business_name, accent_color: row.accent_color,
    background_color: row.background_color, offer_text: row.offer_text ?? null,
    source_asset_id: row.source_asset_id, output_asset_id: row.output_asset_id ?? null,
    job_id: row.job_id ?? null, job_status: row.job_status ?? null,
  })) };
}
function matchRead(path) {
  if (typeof path !== "string" || path.length > 200) return null;
  const rules = [
    ["postersForDay", /^\/api\/campaigns\/([^/]+)\/days\/([^/]+)\/posters$/],
    ["videoDownload", /^\/api\/render-jobs\/([^/]+)\/download$/],
    ["posterDownload", /^\/api\/poster-jobs\/([^/]+)\/download$/],
    ["posterJob", /^\/api\/poster-jobs\/([^/]+)$/],
    ["posterDraft", /^\/api\/poster-drafts\/([^/]+)$/],
    ["campaign", /^\/api\/campaigns\/([^/]+)$/],
    ["renderJob", /^\/api\/render-jobs\/([^/]+)$/],
  ];
  for (const [name, rule] of rules) {
    const found = rule.exec(path);
    if (found) return [name, ...found.slice(1)];
  }
  return null;
}
export function createReadOnlyGateway({ verifyJwt, reader }) {
  if (typeof verifyJwt !== "function" || !reader) throw new TypeError("MISSING_DEPENDENCIES");
  return async function handle(method, path, authorization) {
    if (method !== "GET") return json(405, { error: "METHOD_NOT_ALLOWED" });
    const route = matchRead(path);
    if (!route) return json(404, { error: "NOT_FOUND" });
    try {
      const token = typeof authorization === "string" &&
        authorization.startsWith("Bearer ") ? authorization.slice(7) : null;
      if (!token) throw new AuthDenied();
      const user = await verifyJwt(token);
      const [name, id, secondId] = route;
      const first = canonicalUuid(id);
      const second = secondId ? canonicalUuid(secondId) : null;
      if (name === "videoDownload" || name === "posterDownload") {
        const result = name === "videoDownload"
          ? await reader.videoDownload(token, user, first)
          : await reader.posterDownload(token, user, first);
        return json(result.status, result.body);
      }
      if (name === "postersForDay") {
        const rows = await reader.postersForDay(token, user, first, second);
        return rows === null ? json(404, {error: "NOT_FOUND"}) : json(200, listView(rows));
      }
      if (name === "posterDraft") {
        const row = await reader.posterDraft(token, user, first);
        return row ? json(200, draftView(row)) : json(404, {error: "NOT_FOUND"});
      }
      if (name === "posterJob") {
        const row = await reader.posterJob(token, user, first);
        return row ? json(200, {
          job_id: first, poster_id: row.poster_id, status: row.status,
          output_asset_id: row.output_asset_id, error_code: row.error_code ?? null,
        }) : json(404, {error: "NOT_FOUND"});
      }
      const result = name === "campaign"
        ? await reader.campaign(token, user, first)
        : await reader.renderJob(token, user, first);
      return result ? json(200, result) : json(404, { error: "NOT_FOUND" });
    } catch (error) {
      if (error instanceof AuthDenied) return json(401, { error: "UNAUTHORIZED" });
      if (error instanceof UpstreamUnavailable) return json(503, { error: "SERVICE_UNAVAILABLE" });
      if (error instanceof TypeError) return json(400, { error: "INVALID_REQUEST" });
      return json(503, { error: "SERVICE_UNAVAILABLE" });
    }
  };
}
