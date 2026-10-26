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
