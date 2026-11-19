/** GPU-free browser-only guard for uncertain Feature3 draft POST outcomes.
 *
 * The server's CAS/RLS remains authoritative. An ambiguous POST may have
 * committed even when the browser receives a 503/timeout, so never issue a
 * second write merely because React re-rendered or the user double-clicked.
 * A successful authenticated history GET permits an explicit user decision,
 * not an automatic replay. Guard state is scoped to the same tenant/day/API.
 */
export function createFeature3DraftWriteGuard() {
  let owner=null, provider=null, pending=null
  let uncertain=false, historyChecked=false
  const same=(scope,api)=>Boolean(scope && api && scope===owner && api===provider)
  const select=(scope,api)=>{
    if (typeof scope!=='string' || !scope || !api) return false
    if (!same(scope,api)) {
      owner=scope; provider=api; pending=null
      uncertain=false; historyChecked=false
    }
    return true
  }
  return Object.freeze({
    select,
    begin(scope,api) {
      if (!select(scope,api) || pending || uncertain) return null
      const ticket=Object.freeze({scope,api})
      pending=ticket
      return ticket
    },
    complete(ticket) {
      if (!ticket || pending!==ticket) return false
      pending=null
      return true
    },
    abortBeforePost(ticket) {
      if (!ticket || pending!==ticket) return false
      pending=null
      return true
    },
    unknownAfterPost(ticket) {
      if (!ticket || pending!==ticket) return false
      pending=null
      uncertain=true
      historyChecked=false
      return true
    },
    invalidateHistory(scope,api) {
      if (!same(scope,api) || !uncertain) return false
      historyChecked=false
      return true
    },
    verifiedHistory(scope,api) {
      if (!same(scope,api) || !uncertain || pending) return false
      historyChecked=true
      return true
    },
    resolveDeliberately(scope,api) {
      if (!same(scope,api) || !uncertain || !historyChecked || pending) return false
      uncertain=false
      historyChecked=false
      return true
    },
    status(scope,api) {
      return Object.freeze({
        busy: same(scope,api) && pending!==null,
        uncertain: same(scope,api) && uncertain,
        historyChecked: same(scope,api) && uncertain && historyChecked,
      })
    },
  })
}
