// Fictional tenant-owned test INPUTS. NO tokens, network calls, PII or actual delivery.
export const OFFLINE_SCENARIOS=Object.freeze([
 {id:'f1111111-1111-4111-8111-111111111111',name:'Aarohi Fashion (fictional)'},
 {id:'f2222222-2222-4222-8222-222222222222',name:'Green Basket Grocery (fictional)'},
 {id:'f3333333-3333-4333-8333-333333333333',name:'Marigold Bistro Restaurant (fictional)'}
])
const isoDay=n=>new Date(Date.UTC(2026,9,28,4+n*24,30)).toISOString().replace('.000','')
const id=(prefix,n)=>prefix+'0000000-0000-4000-8000-'+String(n).padStart(12,'0')
export function offlineScenario(shopId){
 if(!OFFLINE_SCENARIOS.some(s=>s.id===shopId)) throw new Error('Unknown offline scenario')
 const fashion=shopId===OFFLINE_SCENARIOS[0].id
 const grocery=shopId===OFFLINE_SCENARIOS[1].id
 const accounts=(fashion?[
  ['instagram','@aarohi.style','CONNECTED',['read_identity','publish_image','publish_video']],
  ['facebook','Aarohi Fashion Page','EXPIRED',['read_identity']],
  ['linkedin','Aarohi Retail','REVOKED',[]],
  ['youtube','Aarohi Fashion Shorts','PENDING',[]]
 ]:grocery?[
  ['instagram','@greenbasket.sample','CONNECTED',['read_identity','publish_image']],
  ['facebook','Green Basket Grocery Page','CONNECTED',['read_identity','publish_image']],
  ['youtube','Green Basket Shorts','EXPIRED',[]]
 ]:[
  ['instagram','@marigold.bistro','CONNECTED',['read_identity','publish_image','publish_video']],
  ['facebook','Marigold Bistro Page','EXPIRED',['read_identity']],
  ['linkedin','Marigold Bistro Team','REVOKED',[]],
  ['youtube','Marigold Bistro Shorts','PENDING',[]],
  ['facebook','Marigold Bistro disconnected sample','DISCONNECTED',[]]
 ]).map(([provider,channel_name,status,scopes],i)=>({
  id:id('a',i+1),shop_id:shopId,provider,channel_name,channel_id:'FICTIONAL-'+(i+1),
  status,scopes,verified_at:'2026-10-28T09:00:00Z'
 }))
 const history=Array.from({length:fashion?26:8},(_,i)=>{
  const state=['SCHEDULED','QUEUED','PUBLISHING','PUBLISHED','FAILED','CANCELLED'][i%6]
  const provider=['instagram','facebook','linkedin','youtube'][i%4]
  return {id:id('b',i+1),shop_id:shopId,provider,
   channel_name:fashion?'Aarohi fictional channel':grocery?'Green Basket fictional channel':'Marigold Bistro fictional channel',
   status:state,scheduled_at:isoDay(i),timezone:'Asia/Kolkata',
   attempts:state==='FAILED'?2:['PUBLISHED','PUBLISHING'].includes(state)?1:0,
   receipt_id:state==='PUBLISHED'?'OFFLINE-RECEIPT-'+(i+1):null,
   failure_code:state==='FAILED'?'TEST_PROVIDER_REJECTED':null}
 })
 return {shopId,accounts,history}
}
