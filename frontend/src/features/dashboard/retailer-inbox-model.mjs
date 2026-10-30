// Validate the existing retailer_inbox RPC result before React or Query can use it.
// The RLS-protected server remains authoritative; this is client defense in depth.
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const CATEGORIES=new Set(['campaign','video','poster'])
const SEVERITIES=new Set(['info','attention'])
const KEYS=new Set(['id','shop_id','category','severity','title','detail','created_at','read_at'])
const fail=()=>{throw new Error('Retailer inbox records could not be verified')}
const safeText=(value,min,max)=>typeof value==='string'&&value.length>=min&&value.length<=max
const leap=year=>year%4===0&&(year%100!==0||year%400===0)

// Supabase/Postgres sends timestamptz in UTC or an explicit numeric offset,
// with up to six fractional digits. Date.parse alone accepts impossible dates.
export function validInboxTime(value) {
  if(typeof value!=='string')return false
  const m=/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?(Z|[+-](\d{2}):(\d{2}))$/.exec(value)
  if(!m)return false
  const [year,month,day,hour,minute,second]=m.slice(1,7).map(Number)
  const maxDay=[31,leap(year)?29:28,31,30,31,30,31,31,30,31,30,31][month-1]
  return year>=1&&month>=1&&month<=12&&day>=1&&day<=maxDay &&
    hour<=23&&minute<=59&&second<=59 &&
    (m[8]==='Z'||(Number(m[9])<=23&&Number(m[10])<=59)) &&
    Number.isFinite(Date.parse(value))
}

export function verifyRetailerInbox(shopId, result, view='all', category='all', limit=20) {
  if(!UUID.test(shopId||'')||!['all','unread'].includes(view)||
     !['all',...CATEGORIES].includes(category)||
     !Number.isSafeInteger(limit)||limit<1||limit>40||
     !result||typeof result!=='object'||Array.isArray(result)||
     Object.keys(result).some(key=>!['shop_id','matching_total','unread_total','checked_at','items'].includes(key))||
     result.shop_id!==shopId||!validInboxTime(result.checked_at)||
     !Number.isSafeInteger(result.matching_total)||result.matching_total<0||
     !Number.isSafeInteger(result.unread_total)||result.unread_total<0||
     !Array.isArray(result.items)||result.items.length>limit||
     result.items.length>result.matching_total)fail()
  const ids=new Set()
  const items=result.items.map(row=>{
    if(!row||typeof row!=='object'||Array.isArray(row)||
       Object.keys(row).some(key=>!KEYS.has(key))||
       !Number.isSafeInteger(row.id)||row.id<1||ids.has(row.id)||
       row.shop_id!==shopId||!CATEGORIES.has(row.category)||
       (category!=='all'&&row.category!==category)||
       !SEVERITIES.has(row.severity)||
       !safeText(row.title,4,120)||!safeText(row.detail,4,240)||
       !validInboxTime(row.created_at)||
       !(row.read_at===null||validInboxTime(row.read_at))||
       (view==='unread'&&row.read_at!==null))fail()
    ids.add(row.id)
    return {id:row.id,shop_id:row.shop_id,category:row.category,
      severity:row.severity,title:row.title,detail:row.detail,
      created_at:row.created_at,read_at:row.read_at}
  })
  return {shop_id:shopId,checked_at:result.checked_at,
    matching_total:result.matching_total,unread_total:result.unread_total,items}
}
