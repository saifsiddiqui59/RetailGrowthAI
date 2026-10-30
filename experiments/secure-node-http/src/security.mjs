/**
 * RetailGrowthAI Part 1 experimental Node JWT boundary (source only).
 * Verifies Supabase asymmetric tokens against the pinned project's JWKS.
 * No fallback to native Static Web Apps principal or unsigned JWT.
 */
import { createPublicKey, verify as cryptoVerify } from "node:crypto";

export class AuthDenied extends Error {
  constructor() { super("UNAUTHORIZED"); this.name = "AuthDenied"; }
}
export class UpstreamUnavailable extends Error {
  constructor() { super("SERVICE_UNAVAILABLE"); this.name = "UpstreamUnavailable"; }
}
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const TOKEN_MAX = 8192;
const JWKS_MAX_BYTES = 32768;

export function canonicalUuid(value) {
  if (typeof value !== "string" || !UUID.test(value)) throw new TypeError("INVALID_UUID");
  return value;
}

export function supabaseOrigin(origin) {
  if (typeof origin !== "string") throw new TypeError("INVALID_SUPABASE_ORIGIN");
  const url = new URL(origin);
  if (url.protocol !== "https:" || !url.hostname || url.username || url.password ||
      url.pathname !== "/" || url.search || url.hash || url.port) {
    throw new TypeError("INVALID_SUPABASE_ORIGIN");
  }
  return url.origin;
}

function decodeJsonUrl(text) {
  if (typeof text !== "string" || !text || !/^[A-Za-z0-9_-]+$/.test(text) ||
      text.length > 12000) throw new AuthDenied();
  let data;
  try {
    const bytes = Buffer.from(text, "base64url");
    if (bytes.toString("base64url") !== text) throw new AuthDenied();
    data = JSON.parse(bytes.toString("utf8"));
  } catch { throw new AuthDenied(); }
  if (!data || typeof data !== "object" || Array.isArray(data)) throw new AuthDenied();
  return data;
}
function sigBuffer(text) {
  if (typeof text !== "string" || !/^[A-Za-z0-9_-]+$/.test(text)) throw new AuthDenied();
  const bytes = Buffer.from(text, "base64url");
  if (!bytes.length || bytes.toString("base64url") !== text) throw new AuthDenied();
  return bytes;
}

export function createSupabaseVerifier({ origin, fetchImpl = fetch, now = () => Date.now() }) {
  const apiOrigin = supabaseOrigin(origin);
  const issuer = apiOrigin + "/auth/v1";
  const jwksUri = issuer + "/.well-known/jwks.json";
  let cached = null;
  let expiresAt = 0;
  async function publicKeys() {
    if (cached && now() < expiresAt) return cached;
    let response;
    try {
      response = await fetchImpl(jwksUri, {
        method: "GET", headers: { Accept: "application/json" },
        redirect: "error", cache: "no-store", signal: AbortSignal.timeout(5000),
      });
      if (!response.ok) throw new Error("JWKS_UNAVAILABLE");
      const text = await response.text();
      if (text.length > JWKS_MAX_BYTES) throw new Error("JWKS_TOO_LARGE");
      const data = JSON.parse(text);
      if (!data || !Array.isArray(data.keys) || data.keys.length > 20) throw new Error("JWKS_INVALID");
      const keys = new Map();
      for (const key of data.keys) {
        if (!key || typeof key !== "object" || typeof key.kid !== "string" ||
            !key.kid || key.kid.length > 128 || !["ES256", "RS256"].includes(key.alg) ||
            key.use && key.use !== "sig" || keys.has(key.kid)) {
          throw new Error("JWKS_INVALID");
        }
        if (key.alg === "ES256" && !(key.kty === "EC" && key.crv === "P-256")) continue;
        if (key.alg === "RS256" && key.kty !== "RSA") continue;
        keys.set(key.kid, key);
      }
      if (!keys.size) throw new Error("JWKS_EMPTY");
      cached = keys;
      expiresAt = now() + 300000;
      return keys;
    } catch {
      // Never accept unverified tokens during a key fetch failure.
      throw new UpstreamUnavailable();
    }
  }
  return async function verifyJwt(token) {
    if (typeof token !== "string" || token.length < 10 || token.length > TOKEN_MAX) {
      throw new AuthDenied();
    }
    const parts = token.split(".");
    if (parts.length !== 3) throw new AuthDenied();
    const [headerPart, payloadPart, signaturePart] = parts;
    const header = decodeJsonUrl(headerPart);
    const claims = decodeJsonUrl(payloadPart);
    const signature = sigBuffer(signaturePart);
    if (!["ES256", "RS256"].includes(header.alg) ||
        typeof header.kid !== "string" || !header.kid || header.kid.length > 128 ||
        (header.typ !== undefined && header.typ !== "JWT") ||
        ["jku", "x5u", "crit", "enc", "zip"].some(field => field in header)) {
      throw new AuthDenied();
    }
    const keys = await publicKeys();
    const jwk = keys.get(header.kid);
    if (!jwk || jwk.alg !== header.alg) throw new AuthDenied();
    if (header.alg === "ES256" && signature.length !== 64) throw new AuthDenied();
    let verified = false;
    try {
      const key = createPublicKey({ key: jwk, format: "jwk" });
      verified = cryptoVerify("sha256", Buffer.from(headerPart + "." + payloadPart), {
        key, ...(header.alg === "ES256" ? { dsaEncoding: "ieee-p1363" } : {}),
      }, signature);
    } catch { throw new AuthDenied(); }
    if (!verified) throw new AuthDenied();
    const seconds = Math.floor(now() / 1000);
    if (claims.iss !== issuer || claims.aud !== "authenticated" ||
        claims.role !== "authenticated" || claims.is_anonymous === true ||
        typeof claims.exp !== "number" || !Number.isSafeInteger(claims.exp) ||
        typeof claims.iat !== "number" || !Number.isSafeInteger(claims.iat) ||
        claims.iat > seconds || claims.iat <= 0 || claims.exp <= seconds ||
        (claims.nbf !== undefined && (typeof claims.nbf !== "number" || claims.nbf > seconds))) {
      throw new AuthDenied();
    }
    try { return canonicalUuid(claims.sub); } catch { throw new AuthDenied(); }
  };
}
