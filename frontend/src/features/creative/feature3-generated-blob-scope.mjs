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
  const clear=()=>{
    const previous=url
    url=null
    job=null
    if(previous!==null)revokeURL(previous)
  }
  const selectScope=nextShop=>{
    if(!ID.test(nextShop||'')) {
      clear()
      shop=null
      return
    }
    if(shop!==nextShop){
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
    const next=createURL(receipt.blob)
    if(typeof next!=='string'||!next.startsWith('blob:')){
      if(typeof next==='string'&&next.startsWith('blob:'))revokeURL(next)
      throw Error('Only local revocable Blob preview URL permitted')
    }
    clear()
    job=nextJob
    url=next
    return next
  }
  const view=(nextShop,nextJob)=>nextShop===shop&&nextJob===job?url:null
  return Object.freeze({selectScope,install,view,clear})
}
