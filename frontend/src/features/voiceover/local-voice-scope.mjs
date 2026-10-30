// Feature2 UI-only in-flight response fence. No JWT, rights or approval authority.
// Function identities matter: a revoked/replaced trusted callback invalidates
// an earlier promise even when shop/script metadata remains unchanged.
const KEYS = Object.freeze([
  'shopId','campaignId','planSha256','sourceScript',
  'enabled','voice','language','speed',
])
export function localVoiceRequestScope(fields = {}) {
  const scope = Object.fromEntries(KEYS.map(key => [key, fields[key]]))
  scope.handlers = Object.freeze([...(fields.handlers || [])])
  return Object.freeze(scope)
}
export function sameLocalVoiceScope(first, latest) {
  return Boolean(first && latest &&
    KEYS.every(key => Object.is(first[key], latest[key])) &&
    Array.isArray(first.handlers) && Array.isArray(latest.handlers) &&
    first.handlers.length === latest.handlers.length &&
    first.handlers.every((handler, index) =>
      Object.is(handler, latest.handlers[index])))
}
