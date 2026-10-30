// Local UI concurrency fence only. It is NOT a JWT/RLS/HMAC verifier.
// Never show a private trace from an obsolete shop, workflow, enabled state,
// callback or overlapping request. The trusted backend must still authorize.
export function createPrivateTraceRequestGate() {
  let scope = null
  let generation = 0
  const setScope = next => {
    if (typeof next !== 'string' || !next) throw Error('Invalid trace request scope')
    if (scope !== next) { scope = next; generation++ }
  }
  return Object.freeze({
    setScope,
    begin(next) {
      setScope(next)
      return Object.freeze({scope, generation: ++generation})
    },
    valid(ticket, next) {
      return ticket?.scope === scope && ticket?.generation === generation &&
        next === scope
    },
    invalidate() { generation++ },
  })
}
