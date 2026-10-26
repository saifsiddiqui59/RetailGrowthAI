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
export function createReadOnlyGateway({ verifyJwt, reader }) {
  if (typeof verifyJwt !== "function" || !reader) throw new TypeError("MISSING_DEPENDENCIES");
  return async function handle(method, path, authorization) {
    if (method !== "GET") return json(405, { error: "METHOD_NOT_ALLOWED" });
    const route = /^\/api\/(campaigns|render-jobs)\/([^/]+)$/.exec(path);
    if (!route) return json(404, { error: "NOT_FOUND" });
    try {
      const token = typeof authorization === "string" &&
        authorization.startsWith("Bearer ") ? authorization.slice(7) : null;
      if (!token) throw new AuthDenied();
      const user = await verifyJwt(token);
      const id = canonicalUuid(route[2]);
      const result = route[1] === "campaigns"
        ? await reader.campaign(token, user, id)
        : await reader.renderJob(token, user, id);
      return result ? json(200, result) : json(404, { error: "NOT_FOUND" });
    } catch (error) {
      if (error instanceof AuthDenied) return json(401, { error: "UNAUTHORIZED" });
      if (error instanceof UpstreamUnavailable) return json(503, { error: "SERVICE_UNAVAILABLE" });
      if (error instanceof TypeError) return json(400, { error: "INVALID_REQUEST" });
      return json(503, { error: "SERVICE_UNAVAILABLE" });
    }
  };
}
