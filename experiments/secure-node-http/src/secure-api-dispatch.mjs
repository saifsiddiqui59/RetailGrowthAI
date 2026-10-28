/**
 * Part 1 secure SWA managed-Node HTTP composition candidate. SOURCE ONLY:
 * do not register this dispatcher or route the live SPA to it until:
 *   1) reviewed Reel SQL migration is installed on guarded DEV;
 *   2) the real SWA custom header/JWKS transport is authenticated on preview;
 *   3) OWNER/EDITOR, VIEWER, cross-tenant and full MP4 acceptance pass.
 *
 * There is deliberately no service_role key, Azure Queue write or HTTP retry.
 * A custom Supabase bearer header is transport ONLY, not an authorization fact.
 */
import { Buffer } from "node:buffer";

const MAX_JWT_BYTES = 8192;
const MAX_MUTATION_BYTES = 65536;
const UUID_ROUTE = "[^/]+";
const errorResponse = (status, error) => ({
  status,
  jsonBody: { error },
  headers: {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Vary": "Origin",
    "X-RGAI-Secure-Adapter": "candidate-v1",
  },
});

function matchWrite(method, path) {
  if (method === "POST" && path === "/api/campaigns") return "campaign";
  if (method === "PATCH" &&
      /^\/api\/campaigns\/[^/]+\/days\/[^/]+$/.test(path)) return "campaign";
  if (method === "POST" && (
    /^\/api\/campaigns\/[^/]+\/posters$/.test(path) ||
    /^\/api\/poster-drafts\/[^/]+\/(renders|select)$/.test(path)
  )) return "poster";
  if (method === "POST" &&
      /^\/api\/campaigns\/[^/]+\/renders$/.test(path)) return "reel";
  return null;
}

function verifiedTransportHeader(headers) {
  // On SWA, Authorization may be handled by the hosting gateway; it is NEVER
  // accepted as an alternative to this explicitly forwarded Supabase header.
  const value = headers.get("x-rgai-supabase-jwt");
  if (!value || typeof value !== "string" ||
      Buffer.byteLength(value, "utf8") > MAX_JWT_BYTES ||
      value.length < 10 || /[\s,\u0000-\u001f\u007f]/.test(value)) {
    return null;
  }
  // Cryptographic ES256/RS256 JWKS verification happens in each downstream
  // read/write gateway BEFORE any user-scoped PostgREST RLS operation.
  return "Bearer " + value;
}

async function jsonBody(request) {
  const contentType = request.headers.get("content-type") || "";
  if (!/^application\/json(?:\s*;\s*charset=utf-8)?$/i.test(contentType)) {
    throw new TypeError("INVALID_JSON_CONTENT_TYPE");
  }
  const lengthHeader = request.headers.get("content-length");
  if (lengthHeader && (!/^\d+$/.test(lengthHeader) ||
      Number(lengthHeader) > MAX_MUTATION_BYTES)) {
    throw new TypeError("OVERSIZED_BODY");
  }
  if (typeof request.text !== "function") throw new TypeError("MISSING_BODY_READER");
  const bodyText = await request.text();
  if (typeof bodyText !== "string" ||
      Buffer.byteLength(bodyText, "utf8") > MAX_MUTATION_BYTES) {
    throw new TypeError("OVERSIZED_BODY");
  }
  let parsed;
  try { parsed = JSON.parse(bodyText); }
  catch { throw new TypeError("INVALID_JSON"); }
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new TypeError("BODY_NOT_OBJECT");
  }
  return parsed;
}

export function createSecureHttpDispatcher({
  readGateway, campaignGateway, posterGateway, reelGateway,
  writesEnabled = false, renderWritesEnabled = false, allowedOrigin,
} = {}) {
  if (typeof readGateway !== "function") throw new TypeError("MISSING_READ_GATEWAY");
  if (writesEnabled && (!campaignGateway || !posterGateway)) {
    throw new TypeError("MISSING_WRITE_GATEWAYS");
  }
  if (renderWritesEnabled && (!writesEnabled || !reelGateway)) {
    throw new TypeError("REEL_REQUIRES_APPROVED_WRITE_GATEWAY");
  }
  if (writesEnabled && (typeof allowedOrigin !== "string" ||
      !/^https:\/\/[a-z0-9.-]+(?::\d+)?$/.test(allowedOrigin))) {
    throw new TypeError("MISSING_PINNED_ALLOWED_ORIGIN");
  }
  return async function dispatch(request) {
    try {
      const method = request.method;
      const url = new URL(request.url);
      if (url.protocol !== "https:" || url.username || url.password ||
          url.pathname.length > 256 || url.search || url.hash) {
        return errorResponse(400, "INVALID_REQUEST");
      }
      // No wildcard CORS, no SWA principal substitution. A browser with a
      // hostile Origin or cross-site fetch cannot use an authenticated JWT.
      const browserOrigin = request.headers.get("origin");
      const fetchSite = request.headers.get("sec-fetch-site");
      if ((browserOrigin && (!allowedOrigin || browserOrigin !== allowedOrigin)) ||
          (fetchSite && !["same-origin", "none"].includes(fetchSite))) {
        return errorResponse(403, "FORBIDDEN_ORIGIN");
      }
      if (!["GET", "POST", "PATCH"].includes(method)) {
        return errorResponse(405, "METHOD_NOT_ALLOWED");
      }
      const path = url.pathname;
      const write = matchWrite(method, path);
      if (method !== "GET" && !write) {
        return errorResponse(404, "NOT_FOUND");
      }
      if (write && (!writesEnabled || (write === "reel" && !renderWritesEnabled))) {
        return errorResponse(503, "SECURE_WRITE_NOT_ENABLED");
      }
      const authorization = verifiedTransportHeader(request.headers);
      if (!authorization) return errorResponse(401, "UNAUTHORIZED");
      if (method === "GET") return await readGateway(method, path, authorization);

      let body;
      try { body = await jsonBody(request); }
      catch { return errorResponse(400, "INVALID_JSON_BODY"); }
      const gateway = write === "campaign" ? campaignGateway :
        write === "poster" ? posterGateway : reelGateway;
      // Never retry a rejected, timed-out or unknown-result mutation.
      return await gateway(method, path, authorization, body);
    } catch {
      // Suppress URLs, tokens, DB errors, signed downloads and request bodies.
      return errorResponse(503, "SERVICE_UNAVAILABLE");
    }
  };
}
