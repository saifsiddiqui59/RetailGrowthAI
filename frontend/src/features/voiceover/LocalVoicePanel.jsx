import {useEffect, useRef, useState} from 'react'
import {F2_LOCAL_VOICES, VOICE_SPEEDS, makeLocalVoiceAction} from './voiceover-model.mjs'
import {verifyLocalPrivatePlayback} from './voiceover-private-playback.mjs'

// Part of existing F2 VoiceoverSelector, not a new app. Actual backend must
// authenticate and run upstream CPU Kokoro with pinned local model weights.
// This UI creates only safe requests, never model audio or grants.
export default function LocalVoicePanel({
 shopId,campaignId,planSha256,enabled=false,sourceScript='',
 onLocalPreview=null,onLocalGenerate=null,onFetchLocalAudio=null,
}){
 const [language,setLanguage]=useState('en-us')
 const [voice,setVoice]=useState('af_heart')
 const [speed,setSpeed]=useState('normal')
 const [busy,setBusy]=useState(false)
 const [error,setError]=useState('')
 const [message,setMessage]=useState('')
 const [saved,setSaved]=useState(null)
 const [audioUrl,setAudioUrl]=useState('')
 const urlRef=useRef(null)
 const scopeRef=useRef('')
 scopeRef.current=shopId+':'+campaignId+':'+planSha256
 function clearAudio(){
  if(urlRef.current)URL.revokeObjectURL(urlRef.current)
  urlRef.current=null;setAudioUrl('')
 }
 useEffect(()=>{
  setSaved(null);setAudioUrl('')
  return ()=>{if(urlRef.current)URL.revokeObjectURL(urlRef.current);urlRef.current=null}
 },[shopId,campaignId,planSha256])
 const choices=F2_LOCAL_VOICES.filter(x=>x.locale===language)
 async function fetchAudio(){
  if(!saved||typeof onFetchLocalAudio!=='function'||enabled!==true){
   setError('Authorized private WAV reader unavailable');return
  }
  const scope=scopeRef.current
  setError('');setBusy(true)
  try{
   const payload=await onFetchLocalAudio({shop_id:shopId,campaign_id:campaignId,
      audio_asset_id:saved.private_audio_asset_id})
   const checked=await verifyLocalPrivatePlayback({shopId,campaignId,
      receipt:saved,readResult:payload})
   if(scope!==scopeRef.current)throw Error('Shop or source changed during playback request')
   clearAudio()
   const url=URL.createObjectURL(new Blob([checked.bytes],{type:checked.mime_type}))
   urlRef.current=url;setAudioUrl(url)
  }catch(e){setError(e?.message||'Original private WAV failed verification')}
  finally{setBusy(false)}
 }
 async function submit(preview){
  setError('');setMessage('');setSaved(null);clearAudio()
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
  const scope=scopeRef.current
  setBusy(true)
  try{
   const proof=await callback(request)
   if(proof?.shop_id!==shopId||proof?.campaign_id!==campaignId||
      proof?.creative_plan_sha256!==planSha256||
      proof?.private!==true||proof?.provider!=='kokoro-onnx'||
      proof?.can_publish!==false||
      typeof proof?.private_audio_asset_id!=='string'||
      !/^[a-f0-9]{64}$/.test(proof?.original_audio_sha256||'')||
      proof?.review_state!=='PENDING_HUMAN_LISTEN_AND_RIGHTS')
      throw Error('No verified private local narration')
   if(scope!==scopeRef.current)throw Error('Shop or script changed during local voice job')
   setSaved(proof)
   setMessage('Private original audio saved; human listening and rights review still required')
  }catch(e){setError(e?.message||'Local voice job status uncertain; check history before retry')}
  finally{setBusy(false)}
 }
 return <section className="rg-local-voice" aria-label="Free local Kokoro voiceover">
  <p>Kokoro ONNX / CPU — English voices only. Hindi and Marathi need an explicitly approved compatible provider.</p>
  <label>Approved narration script
   <textarea rows={3} value={sourceScript} readOnly aria-label="Approved source narration script"/>
  </label>
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
  {saved&&<div aria-label="Private narration review">
    <p>Quality: {saved.quality_issues?.length ?
      saved.quality_issues.map(x=>x.problem).join(', ') :
      'No flagged PCM issues; actual words and pronunciation not yet certified'}.</p>
    <p>Feature #7: {saved.stt_status||'Pending signed original-audio transcription'}</p>
    <p>Editorial status: Pending human listening and rights approval</p>
    <button type="button" disabled={busy||enabled!==true||!onFetchLocalAudio}
      onClick={fetchAudio}>Load verified private WAV preview</button>
    {audioUrl&&<audio controls src={audioUrl} aria-label="Verified private Kokoro narration"/>}
   </div>}
  {error&&<p role="alert">{error}</p>}
  {message&&<p role="status">{message}</p>}
 </section>
}
