// WineShopPOS-style tiny Node HTTP A/B control, NOT customer API.
// Deliberately has no tenant queries or mutation capability.
export function routeControl(method,path) {
  if (method!=="GET") return {status:405,jsonBody:{error:"METHOD_NOT_ALLOWED"}};
  if (path==="/api/p0-health-lite") return {status:200,jsonBody:{status:"HEALTH_ONLY"}};
  // Synthetic control never authenticates: always deny, even when a bearer header
  // was supplied by a client or injected by an upstream platform component.
  if (path.startsWith("/api/campaigns/")) return {status:401,jsonBody:{error:"AUTH_REQUIRED"}};
  return {status:404,jsonBody:{error:"NOT_FOUND"}};
}
