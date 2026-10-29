import { useEffect, useMemo, useRef, useState } from 'react'
import {F2_VOICES,VOICE_SPEEDS,voiceChoices,emptyVoiceSelection,makeVoiceAction,validateVoiceSelection} from './voiceover-model.mjs'
import LocalVoicePanel from './LocalVoicePanel.jsx'
import Feature2TracePanel from './Feature2TracePanel.jsx'
import './VoiceoverSelector.css'

// Reusable Feature2 source-only panel; coordinator/F4 must mount it with real
// JWT/RLS membership, reviewed source script, actual opt-in Speech API and
// separate secure signed upload. No browser API key or direct Azure requests.
export default function VoiceoverSelector({
  shopId,campaignId,planSha256,sourceScript='',
  enabled=false,approvedAudioAssets=[],
  onSelectionChange=null,onRequestPreview=null,onRequestSynthesis=null,
  onRequestUpload=null,onRequestLocalPreview=null,onRequestLocalSynthesis=null,
  onFetchLocalAudio=null,onFetchLocalQualityReview=null,
  onFetchLocalSignedWerReview=null,onProposeLocalScriptRevision=null,
  onProposeLocalPronunciation=null,onCommitReviewedLocalDraft=null,
  onRequestLocalSentenceRetake=null,
  traceWorkflowId=null,traceSourceSha256=null,onFetchPrivateTrace=null,
}){
  const [selection,setSelection]=useState(emptyVoiceSelection)
  const [voiceProvider,setVoiceProvider]=useState('kokoro')
  const [confirmed,setConfirmed]=useState(false)
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  const [message,setMessage]=useState('')
  const [file,setFile]=useState(null)
  const requestScopeRef=useRef('')
  // A customer revision, shop change, voice selection or revoked role
  // invalidates every in-flight paid request and upload receipt.
  requestScopeRef.current=[shopId,campaignId,planSha256,sourceScript,
    enabled,selection.mode,selection.voice_id,selection.speed,voiceProvider,
    file?.name,file?.size,file?.lastModified].join(':')
  useEffect(()=>{
    setSelection(emptyVoiceSelection())
    setBusy(false);setConfirmed(false);setError('');setMessage('');setFile(null)
    setLocale('en-IN');setVoiceProvider('kokoro')
  },[shopId,campaignId,planSha256,sourceScript])
  const authorizedAssets=useMemo(()=>
    (Array.isArray(approvedAudioAssets)?approvedAudioAssets:[])
    .filter(a=>a?.shop_id===shopId && a?.authorized===true && a?.kind==='audio'),
    [approvedAudioAssets,shopId])
  const [locale,setLocale]=useState('en-IN')
  const ready=enabled===true && Boolean(shopId&&campaignId&&planSha256)
  function choose(next){
    setSelection(next);setConfirmed(false);setError('');setMessage('')
    if(typeof onSelectionChange==='function')onSelectionChange(next)
  }
  const display=selection.mode==='ai' ? voiceChoices(locale) : F2_VOICES
  async function generate(preview){
    setError('');setMessage('')
    if(!ready||typeof (preview?onRequestPreview:onRequestSynthesis)!=='function') {
      setError('The tenant-safe Speech service is not connected');return
    }
    if(!sourceScript||typeof sourceScript!=='string'||sourceScript.length>1800){
      setError('Reviewed Feature2 narration is required');return
    }
    let payload
    try{
      payload=makeVoiceAction({selection,shopId,campaignId,planSha256,
        approvedAudioAssets:authorizedAssets,userConfirmedCharge:confirmed,
        idempotencyKey:crypto.randomUUID(),preview})
    }catch{setError('Choose an available voice and confirm provider charges');return}
    const scope=requestScopeRef.current
    setBusy(true)
    try{
      const result=await (preview?onRequestPreview:onRequestSynthesis)(payload)
      if(scope!==requestScopeRef.current)throw Error('Voice request context changed')
      if(result?.shop_id!==shopId||result?.campaign_id!==campaignId||
        result?.plan_sha256!==planSha256||result?.private!==true||
        typeof result?.asset_id!=='string'||result?.can_publish!==false)
        throw Error('Signed private response could not be verified')
      setMessage(preview?'Private voice preview saved for authorized review.':
        'Private narration generated. It still requires editorial approval.')
      setConfirmed(false)
    }catch(e){if(scope===requestScopeRef.current)
      setError(e?.message||'Speech request failed; check original job before retrying')}
    finally{if(scope===requestScopeRef.current)setBusy(false)}
  }
  async function upload(){
    setError('');setMessage('')
    if(!ready||typeof onRequestUpload!=='function'||!file){
      setError('A tenant-private audio uploader is not connected');return
    }
    if(!['audio/wav','audio/x-wav','audio/mpeg'].includes(file.type)||
      file.size<100||file.size>25*1024*1024){
      setError('Only WAV or MP3 up to 25 MB is supported');return
    }
    const scope=requestScopeRef.current
    setBusy(true)
    try{
      const receipt=await onRequestUpload(file,{shop_id:shopId,campaign_id:campaignId,
        creative_plan_sha256:planSha256,requires_rights_review:true})
      if(scope!==requestScopeRef.current||receipt?.shop_id!==shopId||
        receipt?.campaign_id!==campaignId||
        receipt?.private!==true||receipt?.can_publish!==false||
        typeof receipt?.asset_id!=='string')throw Error('Private upload not verified')
      setMessage('Upload received for authorization and rights review.')
    }catch(e){if(scope===requestScopeRef.current)
      setError(e?.message||'Private upload failed; no audio was selected')}
    finally{if(scope===requestScopeRef.current)setBusy(false)}
  }
  return <section className="rg-voice" aria-label="Reel voiceover settings">
    <h3>Voiceover</h3>
    <p>Use AI narration, your own approved recording, or no voiceover.</p>
    <fieldset disabled={!ready||busy}>
      <legend>Voiceover source</legend>
      {[
        ['ai','Generate an AI voice'],
        ['uploaded','Use an existing recording'],
        ['none','No voiceover'],
      ].map(([mode,label])=><label key={mode}>
        <input type="radio" name="rgai_voice_mode" checked={selection.mode===mode}
          onChange={()=>{if(mode==='ai')setLocale('en-IN');choose(mode==='ai'?{
            mode,language:'en-IN',voice_id:'en-IN-NeerjaNeural',speed:'normal',audio_asset_id:null,
          }:mode==='none'?emptyVoiceSelection():{
            mode,language:null,voice_id:null,speed:'normal',audio_asset_id:null,
          })}}/>
        {label}
      </label>)}
      {selection.mode==='ai'&&<>
        <label>AI speech provider
          <select aria-label="AI voice provider" value={voiceProvider} onChange={e=>{setVoiceProvider(e.target.value);setConfirmed(false)}}>
            <option value="kokoro">Free local Kokoro (English only)</option>
            <option value="azure">Azure Speech (explicitly paid / Hindi / Marathi)</option>
          </select>
        </label>
        {voiceProvider==='kokoro'?<LocalVoicePanel shopId={shopId}
          campaignId={campaignId} planSha256={planSha256}
          enabled={ready} sourceScript={sourceScript}
          onLocalPreview={onRequestLocalPreview}
          onLocalGenerate={onRequestLocalSynthesis}
          onFetchLocalAudio={onFetchLocalAudio}
          onFetchQualityReview={onFetchLocalQualityReview}
          onFetchSignedWerReview={onFetchLocalSignedWerReview}
          onProposeScriptRevision={onProposeLocalScriptRevision}
          onProposePronunciation={onProposeLocalPronunciation}
          onCommitReviewedDraft={onCommitReviewedLocalDraft}
          onRequestSentenceRetake={onRequestLocalSentenceRetake}/> : <>

        <label>Language
          <select value={locale} onChange={e=>{
            const value=e.target.value;setLocale(value)
            const next=voiceChoices(value)[0]
            choose({...selection,language:value,voice_id:next.id})
          }}>
            <option value="en-IN">Indian English</option>
            <option value="hi-IN">Hindi</option>
            <option value="mr-IN">Marathi</option>
          </select>
        </label>
        <label>AI voice
          <select value={selection.voice_id||''} onChange={e=>
            choose({...selection,voice_id:e.target.value})}>
            {display.map(v=><option key={v.id} value={v.id}>{v.name} — {v.gender}</option>)}
          </select>
        </label>
        <label>Speaking speed
          <select value={selection.speed} onChange={e=>choose({...selection,speed:e.target.value})}>
            {VOICE_SPEEDS.map(s=><option key={s} value={s}>{s}</option>)}
          </select>
        </label>
        <p>Audio synthesis and previews may incur Azure Speech charges. Nothing plays automatically.</p>
        <label><input type="checkbox" checked={confirmed}
          onChange={e=>setConfirmed(e.target.checked)}/> I approve this voice request and its configured spending cap</label>
        <button type="button" disabled={!confirmed||!onRequestPreview}
          onClick={()=>generate(true)}>Generate preview</button>
        <button type="button" disabled={!confirmed||!onRequestSynthesis}
          onClick={()=>generate(false)}>Generate narration</button>
        </>}
      </>}
      {selection.mode==='uploaded'&&<>
        <label>Approved private narration
          <select value={selection.audio_asset_id||''}
            onChange={e=>choose({...selection,audio_asset_id:e.target.value||null})}>
            <option value="">Choose an approved recording</option>
            {authorizedAssets.map(a=><option key={a.id} value={a.id}>{a.title||a.id}</option>)}
          </select>
        </label>
        {onRequestUpload&&<label>Upload your recording for review (WAV/MP3)
          <input type="file" accept=".wav,.mp3,audio/wav,audio/mpeg"
            onChange={e=>{setFile(e.target.files?.[0]||null);setError('');setMessage('')}}/>
          <button type="button" disabled={!file} onClick={upload}>Upload for private review</button>
        </label>}
      </>}
    </fieldset>
    {traceWorkflowId&&traceSourceSha256&&<Feature2TracePanel
      shopId={shopId} campaignId={campaignId}
      workflowId={traceWorkflowId} sourceSha256={traceSourceSha256}
      enabled={ready} onFetchPrivateTrace={onFetchPrivateTrace}/>}
    {!ready&&<p role="status">Voiceover source ready; account-backed Speech integration not yet enabled.</p>}
    {error&&<p role="alert">{error}</p>}
    {message&&<p role="status">{message}</p>}
  </section>
}
