// Pure, testable Feature #1 READ-model seam. No OAuth, transport, persistence or publishing.
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const PROVIDERS=new Set(['instagram','facebook','linkedin','youtube'])
const ACCOUNT_STATES=new Set(['CONNECTED','DISCONNECTED','EXPIRED','REVOKED','PENDING'])
const POST_STATES=new Set(['SCHEDULED','QUEUED','PUBLISHING','PUBLISHED','FAILED','CANCELLED'])
const SCOPES=new Set(['read_identity','publish_image','publish_video'])
const safeText=(v,max=100)=>typeof v==='string'&&v.trim().length>0&&v.length<=max
// Date.parse normalizes invalid calendar dates (for example 2026-02-31).
// Verify every UTC component before displaying an alleged provider event.
const iso=(v)=>{
  if(typeof v!=='string')return false
  const parts=/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,3})?Z$/.exec(v)
  if(!parts)return false
  const date=new Date(v)
  return Number.isFinite(date.getTime()) &&
    date.getUTCFullYear()===Number(parts[1]) &&
    date.getUTCMonth()+1===Number(parts[2]) &&
    date.getUTCDate()===Number(parts[3]) &&
    date.getUTCHours()===Number(parts[4]) &&
    date.getUTCMinutes()===Number(parts[5]) &&
    date.getUTCSeconds()===Number(parts[6])
}
const onlyKeys=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).every(k=>keys.includes(k))
const err=()=>{throw new Error('Integration read data could not be verified')}
function validateScope(shopId,items){
  if(!UUID.test(shopId||'')||!Array.isArray(items)||items.length>100)err()
}
function noDuplicates(ids){if(new Set(ids).size!==ids.length)err()}
export function normalizeSocialAccounts(shopId,records){
  validateScope(shopId,records)
  if(records.length>20)err()
  const fields=['id','shop_id','provider','channel_name','channel_id','status','scopes','verified_at']
  const list=records.map(a=>{
    if(!onlyKeys(a,fields)||!UUID.test(a.id||'')||a.shop_id!==shopId||
       !PROVIDERS.has(a.provider)||!safeText(a.channel_name,80)||
       !safeText(a.channel_id,90)||!ACCOUNT_STATES.has(a.status)||
       !Array.isArray(a.scopes)||a.scopes.length>3||
       !a.scopes.every(x=>SCOPES.has(x))||new Set(a.scopes).size!==a.scopes.length||
       !iso(a.verified_at)||
       (a.status!=='CONNECTED'&&a.scopes.some(x=>x.startsWith('publish_'))))err()
    return {id:a.id,provider:a.provider,channel_name:a.channel_name,
      channel_id:a.channel_id,status:a.status,scopes:[...a.scopes],verified_at:a.verified_at}
  })
  noDuplicates(records.map(x=>x.id))
  return list
}
export function normalizePublishingHistory(shopId,records){
  validateScope(shopId,records)
  const fields=['id','shop_id','provider','channel_name','status','scheduled_at','timezone','attempts','receipt_id','failure_code']
  const out=records.map(p=>{
    if(!onlyKeys(p,fields)||!UUID.test(p.id||'')||p.shop_id!==shopId||
       !PROVIDERS.has(p.provider)||!safeText(p.channel_name,80)||
       !POST_STATES.has(p.status)||!iso(p.scheduled_at)||
       !safeText(p.timezone,60)||!Number.isSafeInteger(p.attempts)||
       p.attempts<0||p.attempts>10||
       (p.status==='PUBLISHED'?!safeText(p.receipt_id,100):p.receipt_id!==null)||
       (p.status==='FAILED'?!safeText(p.failure_code,50):p.failure_code!==null))err()
    try {new Intl.DateTimeFormat('en-IN',{timeZone:p.timezone}).format(0)}
    catch {err()}
    // Safelist the only visible, non-secret read fields.
    return {id:p.id,provider:p.provider,channel_name:p.channel_name,
      status:p.status,scheduled_at:p.scheduled_at,timezone:p.timezone,
      attempts:p.attempts,receipt_id:p.receipt_id,failure_code:p.failure_code}
  })
  noDuplicates(records.map(x=>x.id))
  return out.sort((a,b)=>b.scheduled_at.localeCompare(a.scheduled_at)||b.id.localeCompare(a.id))
}
export function formatSchedule(utc,timezone){
  if(!iso(utc)||!safeText(timezone,60))err()
  // Explicit short UTC offset disambiguates repeated local times during DST fall-back.
  try{return new Intl.DateTimeFormat('en-IN',{
    year:'numeric',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',
    timeZone:timezone,timeZoneName:'shortOffset',hour12:true,
  }).format(new Date(utc))+' · '+timezone}
  catch{err()}
}
export const PROVIDER_LABELS=Object.freeze({
 instagram:'Instagram',facebook:'Facebook',linkedin:'LinkedIn',youtube:'YouTube'
})
