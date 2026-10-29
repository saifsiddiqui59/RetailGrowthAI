import {useEffect, useRef, useState} from 'react'
import {F2_LOCAL_VOICES, VOICE_SPEEDS, makeLocalVoiceAction,
  makeReviewedDraftRequest, verifyReviewedDraftReceipt,
  makeLocalSentenceRetakeAction, verifyLocalSentenceRetakeReceipt} from './voiceover-model.mjs'
import {verifyLocalPrivatePlayback} from './voiceover-private-playback.mjs'
import {verifyPrivateVoiceQualityReview,verifySignedWordErrorReview} from './voiceover-quality-review.mjs'

// Part of existing F2 VoiceoverSelector, not a new app. Actual backend must
// authenticate and run upstream CPU Kokoro with pinned local model weights.
// This UI creates only safe requests, never model audio or grants.
export default function LocalVoicePanel({
 shopId,campaignId,planSha256,enabled=false,sourceScript='',
 onLocalPreview=null,onLocalGenerate=null,onFetchLocalAudio=null,
 onFetchQualityReview=null,onFetchSignedWerReview=null,
 onProposeScriptRevision=null,onProposePronunciation=null,
 onCommitReviewedDraft=null,onRequestSentenceRetake=null,
}){
 const [language,setLanguage]=useState('en-us')
 const [voice,setVoice]=useState('af_heart')
 const [speed,setSpeed]=useState('normal')
 const [busy,setBusy]=useState(false)
 const [error,setError]=useState('')
 const [message,setMessage]=useState('')
 const [saved,setSaved]=useState(null)
 const [quality,setQuality]=useState(null)
 const [wer,setWer]=useState(null)
 const [pendingProposal,setPendingProposal]=useState(null)
 const [reviewAcknowledged,setReviewAcknowledged]=useState(false)
 const [sentenceIndex,setSentenceIndex]=useState(0)
 const [scriptDraft,setScriptDraft]=useState(sourceScript)
 const [pronounceWord,setPronounceWord]=useState('')
 const [pronounceAs,setPronounceAs]=useState('')
 const [audioUrl,setAudioUrl]=useState('')
 const urlRef=useRef(null)
 const scopeRef=useRef('')
 scopeRef.current=shopId+':'+campaignId+':'+planSha256
 function clearAudio(){
  if(urlRef.current)URL.revokeObjectURL(urlRef.current)
  urlRef.current=null;setAudioUrl('')
 }
 useEffect(()=>{
  setSaved(null);setQuality(null);setWer(null);setPendingProposal(null)
  setReviewAcknowledged(false);setSentenceIndex(0)
  setAudioUrl('');setScriptDraft(sourceScript)
  setPronounceWord('');setPronounceAs('')
  return ()=>{if(urlRef.current)URL.revokeObjectURL(urlRef.current);urlRef.current=null}
 },[shopId,campaignId,planSha256,sourceScript])
 const choices=F2_LOCAL_VOICES.filter(x=>x.locale===language)
 const sentences=(typeof sourceScript==='string'?sourceScript.match(/[^.!?]+[.!?]?/g):null)||[]
 async function propose(kind){
  const callback=kind==='script'?onProposeScriptRevision:onProposePronunciation
  if(enabled!==true||typeof callback!=='function'){
   setError('Authenticated editor review endpoint unavailable');return
  }
  const scope=scopeRef.current
  const text=scriptDraft.trim()
  if(kind==='script' && (!text||text.length>1400||text===sourceScript.trim())){
   setError('Enter a revised narration draft (max 1400 characters)');return
  }
  if(kind==='word' && (!/^[A-Za-z-]{1,60}$/.test(pronounceWord.trim())||
      !/^[A-Za-z- ]{1,80}$/.test(pronounceAs.trim()))){
   setError('Provide a supported correction word and proposed pronunciation');return
  }
  setError('');setMessage('');setBusy(true)
  try{
   const result=await callback({
     shop_id:shopId,campaign_id:campaignId,
     creative_plan_sha256:planSha256,
     idempotency_key:crypto.randomUUID(),
     requires_human_editor_review:true,
     ...(kind==='script'?{proposed_script:text}:
       {word:pronounceWord.trim(),spoken_as:pronounceAs.trim(),language})
   })
   if(scope!==scopeRef.current || result?.shop_id!==shopId ||
      result?.campaign_id!==campaignId || result?.review_status!=='NEEDS_REVIEW' ||
      result?.can_publish!==false || result?.automatically_applied===true){
    throw Error('Untrusted correction proposal response')
   }
   if(kind==='script' && result?.private===true &&
      /^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/.test(result.proposal_id||'') &&
      /^[a-f0-9]{64}$/.test(result.original_prompt_sha256||'') &&
      /^[a-f0-9]{64}$/.test(result.improved_prompt_sha256||'') &&
      Number.isInteger(result.source_revision)){
     setPendingProposal({...result,creative_plan_sha256:planSha256})
     setReviewAcknowledged(false)
   }
   setMessage('Proposal sent for human editor review; approved source script is unchanged')
  }catch(e){setError(e?.message||'Revision proposal rejected')}
  finally{setBusy(false)}
 }
 async function commitApprovedDraft(){
   if(enabled!==true||typeof onCommitReviewedDraft!=='function'||!pendingProposal){
     setError('Signed editor approval and revision backend unavailable');return
   }
   const scope=scopeRef.current
   setError('');setMessage('');setBusy(true)
   try{
     const request=makeReviewedDraftRequest({shopId,campaignId,planSha256,
       proposal:pendingProposal,reviewEventId:crypto.randomUUID(),
       idempotencyKey:crypto.randomUUID(),
       explicitComparisonAcknowledged:reviewAcknowledged})
     const receipt=await onCommitReviewedDraft(request)
     const checked=verifyReviewedDraftReceipt({shopId,campaignId,
       proposal:pendingProposal,receipt})
     if(scope!==scopeRef.current)throw Error('Review context changed')
     setPendingProposal(null);setReviewAcknowledged(false)
     setMessage('Reviewed revision saved as private draft '+checked.revision+
       '. Re-run copy, media rights and human approval before publishing.')
   }catch(e){setError(e?.message||'Human review is not independently verified')}
   finally{setBusy(false)}
 }
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
 async function loadQuality(){
  if(!saved||enabled!==true||typeof onFetchQualityReview!=='function'){
    setError('Authenticated private quality reader unavailable');return
  }
  const scope=scopeRef.current
  setError('');setMessage('');setBusy(true)
  try{
    const response=await onFetchQualityReview({
      shop_id:shopId,campaign_id:campaignId,
      creative_plan_sha256:planSha256,
      audio_asset_id:saved.private_audio_asset_id,
    })
    const reviewed=verifyPrivateVoiceQualityReview({
      shopId,campaignId,planSha256,receipt:saved,review:response,
    })
    if(scope!==scopeRef.current)throw Error('Review context revoked during read')
    setQuality(reviewed);setWer(null)
    setMessage('Speech-to-text hints loaded; listen to the original and request human review')
  }catch(e){setQuality(null);setError(e?.message||'Audio review unavailable')}
  finally{setBusy(false)}
 }
 async function loadSignedWer(){
  if(!saved||!quality||enabled!==true||typeof onFetchSignedWerReview!=='function'){
   setError('Signed current original-WAV and reviewer endpoint unavailable');return
  }
  const scope=scopeRef.current
  setError('');setBusy(true)
  try{
   const record=await onFetchSignedWerReview({
     shop_id:shopId,campaign_id:campaignId,
     creative_plan_sha256:planSha256,
     audio_asset_id:saved.private_audio_asset_id,
     original_audio_sha256:saved.original_audio_sha256,
   })
   const selected=verifySignedWordErrorReview({
     shopId,campaignId,planSha256,receipt:saved,metrics:record})
   if(scope!==scopeRef.current)throw Error('Signed WAV review context changed')
   setWer(selected)
  }catch(e){setWer(null);setError(e?.message||'Signed word accuracy review unavailable')}
  finally{setBusy(false)}
 }
 async function proposeSentenceRetake(){
  if(!quality||!saved||!enabled||typeof onRequestSentenceRetake!=='function'){
    setError('Original private speech and signed quality review required');return
  }
  const scope=scopeRef.current
  setError('');setBusy(true)
  try{
    const request=makeLocalSentenceRetakeAction({shopId,campaignId,planSha256,
      originalAudioSha256:saved.original_audio_sha256,
      sentenceIndex,jobKey:crypto.randomUUID(),voiceId:voice,lang:language,speed})
    const result=await onRequestSentenceRetake(request)
    verifyLocalSentenceRetakeReceipt({request,receipt:result})
    if(scope!==scopeRef.current)throw Error('Original audio or campaign changed')
    setMessage('New private sentence proposed. Await a fresh Feature7 transcript, human listening and Feature4 scene assembly.')
    setQuality(null);setWer(null);setSaved(null);clearAudio()
  }catch(e){setError(e?.message||'Retake rejected; inspect one-shot job before retry')}
  finally{setBusy(false)}
 }
 async function submit(preview){
  setError('');setMessage('');setSaved(null);setQuality(null);setWer(null);clearAudio()
  const callback=preview?onLocalPreview:onLocalGenerate
  if(enabled!==true||typeof callback!=='function'){
   setError('Signed local Kokoro speech worker not connected');return
  }
  if(typeof sourceScript!=='string'||sourceScript.length===0||sourceScript.length>1400){
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
  <label>Editable narration draft (changes require editor review)
   <textarea rows={3} maxLength={1400} value={scriptDraft}
    onChange={e=>{setScriptDraft(e.target.value);setPendingProposal(null);
      setReviewAcknowledged(false)}} aria-label="Narration revision draft"/>
  </label>
  <button type="button" disabled={busy||enabled!==true||!onProposeScriptRevision||
    scriptDraft.trim()===sourceScript.trim()} onClick={()=>propose('script')}>
   Submit narration revision for human review
  </button>
  {scriptDraft.trim()!==sourceScript.trim()&&<section aria-label="Compare source and proposed narration">
    <h4>Compare A/B narration — review only</h4>
    <p><strong>A — Current reviewed source</strong></p>
    <p>{sourceScript}</p>
    <p><strong>B — Your proposed narration</strong></p>
    <p>{scriptDraft}</p>
    <p>Changing words invalidates prior speech alignment, timing and rights reviews.</p>
    {pendingProposal&&<>
      <label><input type="checkbox" checked={reviewAcknowledged}
        onChange={e=>setReviewAcknowledged(e.target.checked)}/>
        I compared A and B. Server-signed independent editor approval is still required.</label>
      <button type="button" disabled={!enabled||busy||!reviewAcknowledged||
        typeof onCommitReviewedDraft!=='function'} onClick={commitApprovedDraft}>
        Save server-approved revision as a new private draft
      </button>
    </>}
  </section>}
  {onProposePronunciation&&<fieldset disabled={!enabled||busy}>
   <legend>Suggest a shop pronunciation</legend>
   <label>Word <input value={pronounceWord} maxLength={60}
     onChange={e=>setPronounceWord(e.target.value)}/></label>
   <label>Speak as <input value={pronounceAs} maxLength={80}
     onChange={e=>setPronounceAs(e.target.value)}/></label>
   <button type="button" onClick={()=>propose('word')}>
     Request pronunciation dictionary approval
   </button>
   <p>Corrections take effect only after independent editor approval and audio re-listening.</p>
  </fieldset>}
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
    <button type="button" disabled={busy||enabled!==true||!onFetchQualityReview}
      onClick={loadQuality}>Review signed word-level transcription</button>
    {quality&&onFetchSignedWerReview&&<button type="button" disabled={!enabled||busy}
      onClick={loadSignedWer}>Compare signed F7 word error and human transcription</button>}
    {wer&&<section aria-label="Signed original WAV word-error comparison">
      <p>F7 transcript vs reviewed script word error rate: {(wer.asr.word_error_rate*100).toFixed(1)}%
        ({wer.asr.substitutions} substitutions, {wer.asr.deletions} deletions,
         {wer.asr.insertions} insertions).</p>
      {wer.manual_human_reference?<p>Independent signed human reference vs script:
        {(wer.manual_human_reference.word_error_rate*100).toFixed(1)}%.
        F7 vs human reference: {(wer.asr_vs_human.word_error_rate*100).toFixed(1)}%.</p>:
        <p>Independent signed human transcript not available.</p>}
      <p>Word errors are textual estimates, not pronunciation or actual-model certification.
        Listen to original private audio; rights and publishing review remain required.</p>
    </section>}
    {quality&&<section aria-label="Original WAV quality and review hints">
      <p>ASR script comparison: {quality.asr_matched_script?'No text differences detected':'Check flagged words against the original audio'}.
        Audio words and pronunciation are not independently certified.</p>
      {quality.pcm_warnings.length>0&&<p>Audio warnings: {quality.pcm_warnings.join(', ')}.</p>}
      {quality.issues.length>0&&<ol aria-label="Possible spoken-word mismatches">
        {quality.issues.slice(0,30).map((entry,i)=><li key={i}>
          {entry.word}: {entry.problem}
          {entry.at_seconds!==null?' (around '+entry.at_seconds.toFixed(2)+' seconds)':''}
          {' — Listen and request editor-approved correction.'}
        </li>)}
      </ol>}
      {quality.issues.length>30&&<p>More word warnings exist. Review all of them in your protected editor.</p>}
      <p>Word confidence unavailable. Listening, original media rights and editorial approval are still mandatory before rendering.</p>
    </section>}
    {quality&&onRequestSentenceRetake&&sentences.length>0&&sentences.length<=13&&<div>
      <label>Correct one approved-dictionary sentence
        <select aria-label="Sentence to retake" value={sentenceIndex}
          onChange={e=>setSentenceIndex(Number(e.target.value))}>
          {sentences.map((sentence,i)=><option key={i} value={i}>
            {i+1}. {sentence.trim().slice(0,90)}
          </option>)}
        </select>
      </label>
      <button type="button" disabled={busy||!enabled} onClick={proposeSentenceRetake}>
        Request one private sentence retake
      </button>
      <p>Retakes are not auto-merged or publishable. F7 speech alignment and human review are required again.</p>
    </div>}
    {audioUrl&&<audio controls src={audioUrl} aria-label="Verified private Kokoro narration"/>}
   </div>}
  {error&&<p role="alert">{error}</p>}
  {message&&<p role="status">{message}</p>}
 </section>
}
