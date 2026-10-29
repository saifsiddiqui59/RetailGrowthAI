/** Signed retailer model import/review/revoke REST adapter, OFF until host enables.
 * No GPU call, Storage upload, service key or ambiguous POST replay.
 * Server verifies current JWT, tenant membership, independent evidence and curator.
 */
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const SHA = /^[0-9a-f]{64}$/
const REVIEW_KEYS = ['adult_synthetic','likeness_and_consent','image_license',
  'private_media_integrity','visual_quality','approved_uses']
const IMPORT_KEYS = ['model_id','media_asset_id','source_kind','label','image_sha256',
  'license_id','license_evidence_sha256','attribution','approved_uses']
function id(value) {
  if (typeof value !== 'string' || !UUID.test(value)) throw Error('Canonical model, media or shop UUID required')
  return value.toLowerCase()
}
function sha(value) {if (typeof value !== 'string' || !SHA.test(value)) throw Error('Verified lower-case SHA256 required'); return value}
function exact(obj, keys) {
  if (!obj || typeof obj !== 'object' || Array.isArray(obj) ||
      Object.keys(obj).length !== keys.length || keys.some(k => !Object.hasOwn(obj,k)))
    throw Error('Unexpected model operation fields')
  return obj
}
function note(value, min=12, max=500) {
  if (typeof value !== 'string' || value.trim().length < min || value.length > max ||
      [...value].some(c => c.charCodeAt(0) < 32 || c.charCodeAt(0) === 127))
    throw Error('Auditable human note required')
  return value.trim()
}
function revision(n) {
  if (!Number.isInteger(n) || n < 1 || n > 2147483646) throw Error('Current model revision required')
  return n
}
function must(cond) {if (!cond) throw Error('Untrusted model operation receipt')}

export function createFeature3ModelWorkflowApi({baseUrl,tokenProvider,fetchImpl = fetch}) {
  if (typeof baseUrl !== 'string') throw Error('HTTPS model API origin required')
  const url = new URL(baseUrl)
  if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash ||
      !['','/'].includes(url.pathname) || typeof tokenProvider !== 'function' || typeof fetchImpl !== 'function')
    throw Error('Strict HTTPS model API and authenticated JWT provider required')
  async function request(shopId, path, body) {
    const token = await tokenProvider()
    if (typeof token !== 'string' || token.length > 8192 || !token.trim() ||
        token.startsWith('sb_secret_') || token.startsWith('sb_publishable_'))
      throw Error('Please sign in again')
    // POST once, never retry after ambiguous 409, timeout or 503.
    const response = await fetchImpl(url.origin + '/api/shops/' + id(shopId) + path, {
      method:'POST',redirect:'error',cache:'no-store',
      headers:{'Authorization':'Bearer '+token,'Content-Type':'application/json'},
      body:JSON.stringify(body),
    })
    if (!response.ok) throw Error(response.status === 401 ? 'Please sign in again' :
      response.status === 409 ? 'Model changed or access revoked. Refresh before retrying.' :
      'Model operation unavailable or denied')
    const payload = await response.json().catch(() => null)
    if (!payload || typeof payload !== 'object' || Array.isArray(payload)) throw Error('Untrusted model operation receipt')
    return payload
  }
  function reviewChecks(checks, decision) {
    exact(checks,REVIEW_KEYS)
    if (REVIEW_KEYS.some(k => typeof checks[k] !== 'boolean') ||
        (decision === 'APPROVE' && REVIEW_KEYS.some(k => checks[k] !== true)))
      throw Error('Six independently reviewed human checks required')
    return Object.fromEntries(REVIEW_KEYS.map(k => [k,checks[k]]))
  }
  function validateReviewReceipt(receipt,shop,model,expected,status) {
    exact(receipt,['shop_id','model_id','status','rights_revision','review_event_id',
      'audit_persisted','gpu_enabled','generation_executed'])
    must(receipt.shop_id === shop && receipt.model_id === model && receipt.status === status &&
      receipt.rights_revision === expected + 1 && UUID.test(receipt.review_event_id) &&
      receipt.audit_persisted === true && receipt.gpu_enabled === false &&
      receipt.generation_executed === false)
    return Object.freeze({...receipt})
  }
  return Object.freeze({
    registerModelOriginal: async (shopId,input) => {
      const sid = id(shopId)
      exact(input,['model_id','image_sha256','license_name','license_url','attribution'])
      const mid = id(input.model_id)
      sha(input.image_sha256)
      if (!['owned','cc0','commercial','royalty_free'].includes(input.license_name) ||
          typeof input.attribution !== 'string' ||
          input.attribution.trim().length < 10 || input.attribution.trim().length > 200 ||
          [...input.attribution].some(c=>c.charCodeAt(0)<32 || c.charCodeAt(0)===127) ||
          (input.license_url !== null &&
            (typeof input.license_url !== 'string' || input.license_url.length > 500)) ||
          (input.license_name !== 'owned' && !input.license_url)) {
        throw Error('Source registration needs a declared legal basis and attribution')
      }
      if (input.license_url !== null) {
        const link = new URL(input.license_url)
        if (link.protocol !== 'https:' || link.username || link.password || !link.hostname)
          throw Error('Untrusted license-evidence URL')
      }
      const result = await request(sid,'/feature3-model-originals/register',{
        ...input,model_id:mid,attribution:input.attribution.trim(),
      })
      exact(result,['shop_id','model_id','media_asset_id','image_sha256',
        'registered','byte_sha_verified','license_verified','status','gpu_authorized'])
      must(result.shop_id===sid && result.model_id===mid &&
        UUID.test(result.media_asset_id) &&
        result.image_sha256===input.image_sha256 &&
        result.registered===true && result.byte_sha_verified===false &&
        result.license_verified===false &&
        result.status==='SOURCE_REGISTERED_PENDING_EVIDENCE' &&
        result.gpu_authorized===false)
      return Object.freeze({...result})
    },
    importPendingModel: async (shopId,input) => {
      const sid = id(shopId)
      exact(input,IMPORT_KEYS)
      const model = id(input.model_id), asset = id(input.media_asset_id)
      sha(input.image_sha256); sha(input.license_evidence_sha256)
      if (!['retailer_licensed','created_ai','opensource_render'].includes(input.source_kind) ||
          !['CC0-1.0','CC-BY-4.0','REVIEWED-COMMERCIAL'].includes(input.license_id) ||
          typeof input.label !== 'string' || !input.label.trim() || input.label.trim().length > 64 ||
          typeof input.attribution !== 'string' || input.attribution.length > 200 ||
          (input.license_id === 'CC-BY-4.0' && !input.attribution.trim()) ||
          !Array.isArray(input.approved_uses) || !input.approved_uses.length ||
          input.approved_uses.length > 3 ||
          input.approved_uses.some(x => !['poster','try_on','video_reference'].includes(x)) ||
          new Set(input.approved_uses).size !== input.approved_uses.length ||
          [...input.label,...input.attribution].some(c=>c.charCodeAt(0)<32 || c.charCodeAt(0)===127))
        throw Error('Invalid pending model metadata')
      const data = await request(sid,'/feature3-models/import',{...input,model_id:model,media_asset_id:asset})
      exact(data,['shop_id','model_id','media_asset_id','status','rights_revision',
        'rights_verified','evidence_verified','gpu_authorized','generation_executed'])
      must(data.shop_id === sid && data.model_id === model && data.media_asset_id === asset &&
        data.status === 'PENDING_REVIEW' && data.rights_revision === 1 &&
        data.rights_verified === false && data.evidence_verified === false &&
        data.gpu_authorized === false && data.generation_executed === false)
      return Object.freeze({...data})
    },
    reviewModel: async (shopId,modelId,input) => {
      const sid=id(shopId), mid=id(modelId)
      exact(input,['decision','expected_revision','image_sha256','evidence_revision','checks','notes'])
      if (!['APPROVE','REJECT'].includes(input.decision) || input.evidence_revision !== 1)
        throw Error('Invalid human review decision')
      const expected=revision(input.expected_revision)
      sha(input.image_sha256)
      const checks=reviewChecks(input.checks,input.decision)
      const notes=note(input.notes)
      const data=await request(sid,'/feature3-models/'+mid+'/review',{
        decision:input.decision,expected_revision:expected,image_sha256:input.image_sha256,
        evidence_revision:1,checks,notes,
      })
      return validateReviewReceipt(data,sid,mid,expected,input.decision === 'APPROVE' ? 'APPROVED' : 'REJECTED')
    },
    revokeModel: async (shopId,modelId,input) => {
      const sid=id(shopId), mid=id(modelId)
      exact(input,['expected_revision','image_sha256','reason'])
      const expected=revision(input.expected_revision)
      sha(input.image_sha256)
      const reason=note(input.reason)
      const data=await request(sid,'/feature3-models/'+mid+'/revoke',{
        expected_revision:expected,image_sha256:input.image_sha256,reason,
      })
      return validateReviewReceipt(data,sid,mid,expected,'REVOKED')
    },
  })
}
