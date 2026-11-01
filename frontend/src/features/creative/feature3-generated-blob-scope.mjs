/** Scoped and revocable object URLs for private Feature3 generated PNGs.
 * Never allocates a URL until a separately JWT/rights/SHA-verified binary
 * receipt arrives. Scope must be reselected after account/shop changes.
 * This is browser-memory cleanup, NOT invalidation of previous signed URLs.
 */
const ID=/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
const SHA=/^[a-f0-9]{64}$/
export function createFeature3GeneratedBlobScope({
  createURL=blob=>URL.createObjectURL(blob),
  revokeURL=url=>URL.revokeObjectURL(url),
}={}) {
  if(typeof createURL!=='function'||typeof revokeURL!=='function')
    throw Error('Private preview memory lifecycle required')
  let shop=null,job=null,url=null
  // A failed browser revoke must never leave a private URL visible, but
  // dropping its only reference would prevent cleanup after recovery.
  // Track only URLs issued by this instance; do not accept remote URLs.
  const pendingRevoke=new Set()
  const revokePending=()=>{
    let failed=false
    for(const owned of pendingRevoke){
      try {
        revokeURL(owned)
        pendingRevoke.delete(owned)
      } catch {
        failed=true
      }
    }
    if(failed) throw Error('Private generated Blob cleanup failed')
  }
  const clear=()=>{
    if(url!==null) pendingRevoke.add(url)
    url=null
    job=null
    revokePending()
  }
  const selectScope=nextShop=>{
    if(!ID.test(nextShop||'')) {
      // A failed cleanup cannot leave the previous shop authorized.
      shop=null
      clear()
      return
    }
    if(shop!==nextShop){
      shop=null
      clear()
      shop=nextShop
    }
  }
  const install=(nextShop,nextJob,receipt)=>{
    if(!ID.test(nextShop||'')||!ID.test(nextJob||'')||shop!==nextShop||
       !receipt||typeof receipt!=='object'||Array.isArray(receipt)||
       receipt.shopId!==shop||receipt.jobId!==nextJob||
       !ID.test(receipt.mediaAssetId||'')||
       !SHA.test(receipt.imageSha256||'')||
       receipt.private!==true||receipt.publishApproved!==false||
       receipt.approvedModel!==false||
       !(receipt.blob instanceof Blob)||receipt.blob.type!=='image/png'||
       receipt.blob.size<100||receipt.blob.size>25*1024*1024||
       'url' in receipt||'signedURL' in receipt||'objectPath' in receipt){
      throw Error('Untrusted private generated preview receipt')
    }
    // A browser that keeps rejecting revocation must not accumulate new
    // private object URLs through repeated Preview clicks. Recover the
    // hidden, previously owned URLs *before* allocating another Blob URL.
    // Failure is non-renderable and cannot be bypassed by another install.
    if(pendingRevoke.size) revokePending()
    const next=createURL(receipt.blob)
    if(typeof next!=='string'||!next.startsWith('blob:')){
      if(typeof next==='string'&&next.startsWith('blob:'))revokeURL(next)
      throw Error('Only local revocable Blob preview URL permitted')
    }
    // A Blob URL factory must never alias the still-owned previous preview.
    // Otherwise clear() would revoke the URL we are about to display.
    if(next===url||pendingRevoke.has(next))
      throw Error('Private generated Blob URL must be fresh')
    try {
      clear()
    } catch {
      // Never expose this newly issued URL on a failed replacement.
      // Even if its own revocation fails, retain its private cleanup receipt.
      pendingRevoke.add(next)
      try { revokePending() } catch { /* retry on the next explicit cleanup */ }
      throw Error('Private generated Blob replacement cleanup failed')
    }
    job=nextJob
    url=next
    return next
  }
  const view=(nextShop,nextJob)=>nextShop===shop&&nextJob===job?url:null
  // A delayed image decode failure must never revoke a newer private preview.
  // Only the exact locally issued URL owned by this shop/job may be discarded.
  const discardFailed=(nextShop,nextJob,expectedURL)=>{
    if(nextShop!==shop||nextJob!==job||url===null||expectedURL!==url)
      return false
    clear()
    return true
  }
  return Object.freeze({selectScope,install,view,clear,discardFailed})
}
