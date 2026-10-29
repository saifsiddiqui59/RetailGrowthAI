// Safe browser-observed HTTP diagnostic receipt. Never return request/response
// bodies, JWTs, private URLs, query strings, tenant IDs or signed download links.
const UUID = /[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/gi
const SERVER_ID = /^[0-9a-f]{32}$/i
const SOURCES = new Set(['campaign', 'trend'])
export function collectHttpReceipt(onResponse, {source, method, path, response, startedAt, attempt = 1}) {
  if (typeof onResponse !== 'function' || !SOURCES.has(source) ||
      !['GET', 'POST', 'PATCH'].includes(method) || typeof path !== 'string') return
  const operation = path.replace(UUID, ':id')
  // Never emit an attacker-controlled path. All caller routes are existing API
  // client-defined methods, with dynamic UUIDs reduced to literal ':id'.
  if (!/^\/[a-z][a-z0-9:/-]{0,99}$/i.test(operation) ||
      !Number.isInteger(response?.status) || response.status < 100 || response.status > 599) return
  const supplied = response.headers?.get?.('X-Request-ID')
  const request_id = typeof supplied === 'string' && SERVER_ID.test(supplied)
    ? supplied.toLowerCase() : null
  const receipt = Object.freeze({
    source, method, operation, status_code: response.status, request_id,
    elapsed_ms: Math.max(0, Math.min(600_000, Math.round(Date.now() - startedAt))),
    attempt: Number.isInteger(attempt) && attempt >= 1 && attempt <= 3 ? attempt : 1,
    handler_marker_seen: request_id !== null,
  })
  try { onResponse(receipt) } catch { /* optional observation must never change API semantics */ }
}
