// Synthetic literal is *not* a JWT, secret, credential or customer identifier.
// Only proves that the managed Free SWA Node API receives our custom header.
const TRANSPORT_SENTINEL = "p0249-public-synthetic-header-proof";
export function syntheticJwtTransport(headerValue = "") {
  return headerValue === TRANSPORT_SENTINEL
    ? {status:200,jsonBody:{transport:"CUSTOM_HEADER_DELIVERED_SYNTHETIC_ONLY"}}
    : {status:401,jsonBody:{error:"SYNTHETIC_HEADER_MISSING"}};
}

// WineShopPOS-style tiny Node HTTP A/B control, NOT customer API.
// Deliberately has no tenant queries or mutation capability.
export function routeControl(method,path,authorization="") {
  if (method!=="GET") return {status:405,jsonBody:{error:"METHOD_NOT_ALLOWED"}};
  if (path==="/api/p0-health-lite") return {status:200,jsonBody:{status:"HEALTH_ONLY"}};
  if (path.startsWith("/api/campaigns/")) return authorization.startsWith("Bearer ")
    ? {status:503,jsonBody:{error:"CONTROL_NO_TENANT_IMPLEMENTATION"}}
    : {status:401,jsonBody:{error:"AUTH_REQUIRED"}};
  return {status:404,jsonBody:{error:"NOT_FOUND"}};
}
