// Feature2 F2-19/F2-20 signed read-only browser client for vetted, opt-in API.
// Never performs speech generation, creates jobs, retries unknown ACKs, calls
// Azure/paid providers, downloads public/signed URLs or grants media rights.
// This source remains disabled until reviewed Functions ZIP and private DB
// migrations/Storage policies are deployed and their exact endpoint enabled.
import {verifyPrivateVoiceJobStatus} from './voiceover-model.mjs'

const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
const SHA=/^[0-9a-f]{64}$/
const MAX_BYTES=20_000_000
const fail=()=>{throw Error('Authenticated private Feature2 speech read unavailable')}

function scope({shopId,campaignId}){
  if(!UUID.test(shopId||'')||!UUID.test(campaignId||''))fail()
}
function secureOrigin(raw){
  if(typeof raw!=='string'||!raw||raw.includes('?')||raw.includes('#'))fail()
  let url
  try{url=new URL(raw)}catch{fail()}
  if(url.protocol!=='https:'||url.username||url.password||
     url.search||url.hash||!url.hostname||
     (url.pathname!=='/'&&url.pathname!=='/api'&&url.pathname!=='/api/'))fail()
  return url.origin+(url.pathname==='/api'||url.pathname==='/api/'?'/api':'/api')
}
function headers(token){
  if(typeof token!=='string'||!token||token.length>8192||
     token!==token.trim()||/[\r\n\x00]/.test(token))fail()
  return {'Authorization':'Bearer '+token,'Cache-Control':'no-store'}
}

export function createFeature2PrivateVoiceReader({
  baseUrl,tokenProvider,fetcher=globalThis.fetch,enabled=false,
}={}){
  const base=secureOrigin(baseUrl)
  if(typeof tokenProvider!=='function'||typeof fetcher!=='function')fail()
  async function get(path,{signal,accept='application/json'}={}){
    if(enabled!==true)fail()
    const before=await tokenProvider()
    const response=await fetcher(base+path,{
      method:'GET',headers:{...headers(before),'Accept':accept},
      cache:'no-store',redirect:'error',credentials:'omit',signal,
    })
    if(!response||response.status!==200||response.ok!==true)fail()
    // A new shop/user login must replace the reader; a rotated token also
    // fences the old request instead of showing an earlier user's response.
    const after=await tokenProvider()
    if(after!==before)fail()
    return {response,token:before}
  }
  async function getPrivateStatus({
    shop_id,campaign_id,request_key,creative_plan_sha256,signal,
  }={}){
    const shopId=shop_id,campaignId=campaign_id
    scope({shopId,campaignId})
    if(!UUID.test(request_key||'')||!SHA.test(creative_plan_sha256||''))fail()
    const {response,token}=await get(
      '/shops/'+shopId+'/campaigns/'+campaignId+
      '/feature2-voice-jobs/'+request_key,{signal})
    if((response.headers?.get('content-type')||'').split(';')[0]
        .trim().toLowerCase()!=='application/json')fail()
    let body
    try{body=await response.json()}catch{fail()}
    // Reuse the same private status validator as LocalVoicePanel.
    verifyPrivateVoiceJobStatus({shopId,campaignId,
      planSha256:creative_plan_sha256,requestKey:request_key,status:body})
    if(await tokenProvider()!==token)fail()
    return body
  }

  async function getOriginalWav({
    shop_id,campaign_id,audio_asset_id,original_audio_sha256,signal,
  }={}){
    const shopId=shop_id,campaignId=campaign_id
    scope({shopId,campaignId})
    if(!UUID.test(audio_asset_id||'')||!SHA.test(original_audio_sha256||''))fail()
    const {response,token}=await get(
      '/shops/'+shopId+'/campaigns/'+campaignId+
      '/feature2-original-wav/'+audio_asset_id+'/'+original_audio_sha256,
      {signal,accept:'audio/wav'})
    const mime=(response.headers?.get('content-type')||'')
      .split(';')[0].trim().toLowerCase()
    const cache=(response.headers?.get('cache-control')||'').toLowerCase()
    const length=response.headers?.get('content-length')
    if(mime!=='audio/wav'||!cache.split(',').some(x=>x.trim()==='no-store')||
       (length!==null && (!/^[0-9]+$/.test(length)||
          Number(length)>MAX_BYTES||Number(length)<128))||
       !response.body||typeof response.body.getReader!=='function')fail()
    // Stream a bounded private download. Never materialize attacker-sized
    // blobs with response.arrayBuffer() before checking their actual length.
    const reader=response.body.getReader()
    const chunks=[]
    let total=0
    try{
      while(true){
        const {done,value}=await reader.read()
        if(done)break
        if(!(value instanceof Uint8Array)||!value.length)fail()
        total+=value.length
        if(total>MAX_BYTES)fail()
        chunks.push(value)
      }
    }catch{
      try{await reader.cancel()}catch{/* No fallback to public URL */}
      fail()
    }finally{
      try{reader.releaseLock()}catch{/* Release is best-effort only */}
    }
    if(total<128||!globalThis.crypto?.subtle)fail()
    const bytes=new Uint8Array(total)
    let start=0
    for(const part of chunks){bytes.set(part,start);start+=part.length}
    if(String.fromCharCode(...bytes.subarray(0,4))!=='RIFF'||
       String.fromCharCode(...bytes.subarray(8,12))!=='WAVE')fail()
    const hash=new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',bytes))
    const hex=Array.from(hash).map(x=>x.toString(16).padStart(2,'0')).join('')
    if(hex!==original_audio_sha256||await tokenProvider()!==token)fail()
    return Object.freeze({
      schema:'retailgrowth.feature2-private-original-wav-read.v1',
      shop_id:shopId,campaign_id:campaignId,asset_id:audio_asset_id,
      original_audio_sha256:hex,mime_type:'audio/wav',
      audio_bytes:bytes,private:true,can_publish:false,
    })
  }
  return Object.freeze({getPrivateStatus,getOriginalWav})
}
