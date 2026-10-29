import {useState} from 'react'
import {F2_LOCAL_VOICES, VOICE_SPEEDS, makeLocalVoiceAction} from './voiceover-model.mjs'

// Part of existing F2 VoiceoverSelector, not a new app. Actual backend must
// authenticate and run upstream CPU Kokoro with pinned local model weights.
// This UI creates only safe requests, never model audio or grants.
export default function LocalVoicePanel({
 shopId,campaignId,planSha256,enabled=false,sourceScript='',
 onLocalPreview=null,onLocalGenerate=null,
}){
 const [language,setLanguage]=useState('en-us')
 const [voice,setVoice]=useState('af_heart')
 const [speed,setSpeed]=useState('normal')
 const [busy,setBusy]=useState(false)
 const [error,setError]=useState('')
 const [message,setMessage]=useState('')
 const choices=F2_LOCAL_VOICES.filter(x=>x.locale===language)
 async function submit(preview){
  setError('');setMessage('')
  const callback=preview?onLocalPreview:onLocalGenerate
  if(enabled!==true||typeof callback!=='function'){
   setError('Signed local Kokoro speech worker not connected');return
  }
  if(typeof sourceScript!=='string'||sourceScript.length===0||sourceScript.length>1800){
   setError('Reviewed script unavailable');return
  }
  let request
  try{
    request=makeLocalVoiceAction({shopId,campaignId,planSha256,
      idempotencyKey:crypto.randomUUID(),voiceId:voice,
      lang:language,speed,preview})
  }catch{setError('Invalid local voice choice');return}
  setBusy(true)
  try{
   const proof=await callback(request)
   if(proof?.shop_id!==shopId||proof?.campaign_id!==campaignId||
      proof?.creative_plan_sha256!==planSha256||
      proof?.private!==true||proof?.provider!=='kokoro-onnx'||
      proof?.can_publish!==false||
      typeof proof?.private_audio_asset_id!=='string')throw Error('No verified private local narration')
   setMessage('Local speech saved privately for human listening and rights review')
  }catch(e){setError(e?.message||'Local voice job status uncertain; check history before retry')}
  finally{setBusy(false)}
 }
 return <section className="rg-local-voice" aria-label="Free local Kokoro voiceover">
  <p>Kokoro ONNX / CPU — English voices only. Hindi and Marathi need an explicitly approved compatible provider.</p>
  <label>English accent
   <select value={language} onChange={e=>{
    const lang=e.target.value
    setLanguage(lang);setVoice(F2_LOCAL_VOICES.find(v=>v.locale===lang)?.id||'af_heart')
   }}>
    <option value="en-us">English (US)</option>
    <option value="en-gb">English (UK)</option>
   </select>
  </label>
  <label>Local voice
   <select value={voice} onChange={e=>setVoice(e.target.value)}>
    {choices.map(v=><option key={v.id} value={v.id}>{v.name} — {v.gender}</option>)}
   </select>
  </label>
  <label>Speed
   <select value={speed} onChange={e=>setSpeed(e.target.value)}>
    {VOICE_SPEEDS.map(s=><option key={s} value={s}>{s}</option>)}
   </select>
  </label>
  <button type="button" disabled={busy||enabled!==true||!onLocalPreview}
   onClick={()=>submit(true)}>Preview free CPU voice</button>
  <button type="button" disabled={busy||enabled!==true||!onLocalGenerate}
   onClick={()=>submit(false)}>Generate free local narration</button>
  {error&&<p role="alert">{error}</p>}
  {message&&<p role="status">{message}</p>}
 </section>
}
