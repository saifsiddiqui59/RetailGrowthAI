/** Feature3 v2 browser adapter. Not an activation or deployment.
 * Caller supplies existing authenticated campaign API HTTPS origin & JWT provider.
 * POSTs are NEVER retried on ambiguous gateway errors. A signed GET history
 * read must resolve uncertainty before any further user action.
 */
import { validateFeature3Design } from './feature3-design.mjs'

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const SHA = /^[a-f0-9]{64}$/
function id(x) {
  if (typeof x !== 'string' || !UUID.test(x)) throw Error('Canonical resource UUID required')
  return x.toLowerCase()
}
export function createFeature3Api({ baseUrl, tokenProvider, fetchImpl = fetch,
  signedStorageOrigin = null }) {
  const url = new URL(baseUrl)
  if (url.protocol !== 'https:' || url.username || url.password ||
      url.search || url.hash || !['', '/'].includes(url.pathname)) {
    throw Error('Feature3 API must be a clean HTTPS origin')
  }
  if (typeof tokenProvider !== 'function' || typeof fetchImpl !== 'function')
    throw Error('Authenticated API provider required')
  const origin = url.origin
  async function request(method, path, body = undefined) {
    const jwt = await tokenProvider()
    if (typeof jwt !== 'string' || !jwt || jwt.length > 8192)
      throw Error('Please sign in again')
    // One transport call only. Never replay POST after a timeout/503.
    const res = await fetchImpl(origin + '/api' + path, {
      method, cache: 'no-store', redirect: 'error',
      headers: {
        Authorization: 'Bearer ' + jwt,
        ...(body === undefined ? {} : {'Content-Type':'application/json'}),
      },
      ...(body === undefined ? {} : {body:JSON.stringify(body)}),
    })
    const payload = await res.json().catch(() => null)
    if (!res.ok) {
      const e = new Error(res.status === 401 ? 'Please sign in again' :
        res.status === 409 ? 'Poster version changed or access revoked' :
        'Feature3 service unavailable or denied')
      e.status = res.status
      throw e
    }
    if (!payload || typeof payload !== 'object' || Array.isArray(payload))
      throw Error('Invalid signed Feature3 response')
    return payload
  }
  const path = (cid,did) => '/campaigns/' + id(cid) + '/days/' + id(did) + '/feature3-designs'
  return Object.freeze({
    listDesigns: async (shopId,campaignId,dayId) => {
      const sid = id(shopId), cid=id(campaignId), did=id(dayId)
      const data = await request('GET',path(cid,did))
      if (data.shop_id!==sid || data.campaign_id!==cid || data.day_id!==did ||
          !Array.isArray(data.designs) || data.designs.length>50 ||
          data.designs.some(row => row.shop_id!==sid || row.campaign_id!==cid ||
            row.day_id!==did || !UUID.test(row.id) ||
            !Number.isInteger(row.revision) || row.revision<1 ||
            !['DRAFT','APPROVED','REJECTED'].includes(row.status))) {
        throw Error('Untrusted poster history for another shop/day')
      }
      return data.designs
    },
    saveDesign: async (shopId,campaignId,dayId,document,{designId=null,expectedRevision=0,variationOf=null}={}) => {
      const sid=id(shopId), cid=id(campaignId), did=id(dayId)
      const design=validateFeature3Design(document)
      if (design.shop_id!==sid || !Number.isInteger(expectedRevision) ||
          expectedRevision<0 || expectedRevision>1000000 ||
          (designId===null && expectedRevision!==0) ||
          (designId!==null && expectedRevision===0) ||
          (variationOf!==null && designId!==null)) {
        throw Error('Invalid versioned poster save request')
      }
      const data=await request('POST',path(cid,did),{
        design,expected_revision:expectedRevision,
        ...(designId===null?{}:{design_id:id(designId)}),
        ...(variationOf===null?{}:{variation_of:id(variationOf)}),
      })
      if (data.shop_id!==sid || data.campaign_id!==cid || data.day_id!==did ||
          data.status!=='DRAFT' || data.rendered!==false ||
          !UUID.test(data.design_id) ||
          (designId!==null && data.design_id!==id(designId)) ||
          data.revision!==expectedRevision+1 ||
          typeof data.server_document_sha256!=='string' ||
          !SHA.test(data.server_document_sha256)) {
        throw Error('Untrusted poster save acknowledgement')
      }
      return data
    },
    listGeneratedJobs: async shopId => {
      const sid = id(shopId)
      const data = await request('GET','/shops/'+sid+'/feature3-gpu-jobs')
      if (data.shop_id!==sid || data.gpu_submission_enabled!==false ||
          !Array.isArray(data.jobs) || data.jobs.length>20 ||
          data.jobs.some(job=>job.shop_id!==sid || !UUID.test(job.id) ||
            !['QUEUED','RUNNING','SUCCEEDED','FAILED'].includes(job.status))) {
        throw Error('Untrusted private generated image history')
      }
      return data.jobs
    },
    getGeneratedImageDownload: async (shopId,jobId) => {
      const sid=id(shopId), jid=id(jobId)
      if (typeof signedStorageOrigin!=='string') throw Error('Private Storage origin required')
      const originUrl = new URL(signedStorageOrigin)
      if (originUrl.protocol!=='https:' || originUrl.username || originUrl.password ||
          originUrl.search || originUrl.hash || !['','/'].includes(originUrl.pathname)) {
        throw Error('Invalid private Storage origin')
      }
      const data = await request('GET','/shops/'+sid+'/feature3-gpu-jobs/'+jid+'/download')
      if (data.job_id!==jid || !UUID.test(data.media_asset_id) ||
          data.expires_in_seconds!==60 || data.approved_model!==false ||
          typeof data.url!=='string') throw Error('Untrusted private image receipt')
      const signed=new URL(data.url)
      const prefix='/storage/v1/object/sign/retailgrowth-media/'+sid+
        '/feature3/gpu/'+jid+'/'
      if (signed.origin!==originUrl.origin || !signed.pathname.startsWith(prefix) ||
          !/^([0-9a-f]{64})\.png$/.test(signed.pathname.slice(prefix.length)) ||
          signed.username || signed.password || signed.hash ||
          [...signed.searchParams.keys()].length!==1 ||
          !signed.searchParams.has('token') ||
          !signed.searchParams.get('token')) {
        throw Error('Untrusted private signed storage URL')
      }
      return {jobId:jid,mediaAssetId:id(data.media_asset_id),url:signed.href,
        expiresInSeconds:60,approvedModel:false}
    },
    listModels: async shopId => {
      const sid=id(shopId)
      const data=await request('GET','/shops/'+sid+'/feature3-models')
      if (data.shop_id!==sid || !Array.isArray(data.models) || data.models.length>50 ||
          data.models.some(model=>model.scope!=='shop' || model.owner_shop_id!==sid ||
            model.status!=='APPROVED' || model.synthetic_adult!==true)) {
        throw Error('Untrusted tenant model catalog')
      }
      return data.models
    },
  })
}
