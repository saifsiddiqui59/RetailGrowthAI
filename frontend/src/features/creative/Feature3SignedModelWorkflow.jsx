/** Feature3 signed retailer model workflow; explicitly OFF until host release.
 * An actual registered, tenant-owned private PNG must already exist. Client
 * inputs never certify likeness, image rights, JWT role or human curator.
 */
import {useState} from 'react'
import {getRetailClient} from '../../lib/supabase.js'
import {verifyPrivateModelOriginalUploadReceipt} from './feature3-model-workflow-api.mjs'
const FIELDS = [
 ['adult_synthetic','Confirmed adult synthetic model'],
 ['likeness_and_consent','Independently confirmed likeness/consent'],
 ['image_license','Independently checked per-image commercial license'],
 ['private_media_integrity','Compared actual original private PNG SHA'],
 ['visual_quality','Personally inspected actual source image'],
 ['approved_uses','Confirmed allowed poster, try-on and video uses'],
]
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const SHA=/^[0-9a-f]{64}$/
const field={display:'grid',gap:4,minWidth:0}
export default function Feature3SignedModelWorkflow({shopId,api,enabled=false,disabled=false}) {
 const [modelId,setModelId]=useState('')
 const [mediaId,setMediaId]=useState('')
 const [imageSha,setImageSha]=useState('')
 const [licenseSha,setLicenseSha]=useState('')
 const [label,setLabel]=useState('')
 const [attribution,setAttribution]=useState('')
 const [license,setLicense]=useState('REVIEWED-COMMERCIAL')
 const [kind,setKind]=useState('retailer_licensed')
 const [uses,setUses]=useState(['poster'])
 const [revision,setRevision]=useState('1')
 const [evidence,setEvidence]=useState('1')
 const [checks,setChecks]=useState({})
 const [notes,setNotes]=useState('')
 const [busy,setBusy]=useState(false)
 const [status,setStatus]=useState('')
 const [receipt,setReceipt]=useState(null)
 const [sourceFile,setSourceFile]=useState(null)
 const [sourceLicense,setSourceLicense]=useState('owned')
 const [sourceLicenseUrl,setSourceLicenseUrl]=useState('')
 const [confirmedRights,setConfirmedRights]=useState(false)
 if (!enabled || !api || !shopId || !UUID.test(shopId)) return <p role="note">
  Signed model import and review are disabled pending protected release authorization.
 </p>
 const blocked=disabled||busy
 const uploadReady=UUID.test(modelId)&&sourceFile?.type==='image/png'&&
  sourceFile?.size>=100&&sourceFile.size<=25*1024*1024&&confirmedRights&&
  ['owned','cc0','commercial','royalty_free'].includes(sourceLicense)&&
  attribution.trim().length>=10&&attribution.trim().length<=200&&
  (sourceLicense==='owned'||sourceLicenseUrl.startsWith('https://'))&&
  typeof api.registerModelOriginal==='function'
 const submitUpload=async()=>{
  if(blocked||!uploadReady)return
  setBusy(true);setReceipt(null);setStatus('')
  try{
   const client=getRetailClient()
   // Existing client enforces a current JWT; no service-role key in browser.
   const uploaded=await client.uploadModelOriginal(shopId,{
    file:sourceFile,modelId,licenseName:sourceLicense,
    licenseUrl:sourceLicenseUrl,attribution,confirmedRights:true,
   })
   // Fail closed before the separate registration POST if Storage returned
   // an unexpected tenant, model, path, digest or forged approval state.
   const verifiedUpload=verifyPrivateModelOriginalUploadReceipt(uploaded,shopId,modelId)
   const registration=await api.registerModelOriginal(shopId,{
    model_id:modelId,image_sha256:verifiedUpload.image_sha256,
    license_name:sourceLicense,
    license_url:sourceLicenseUrl||null,attribution:attribution.trim(),
   })
   if(registration.model_id!==uploaded.model_id ||
       registration.image_sha256!==verifiedUpload.image_sha256){
    throw Error('Storage and signed registration identities do not match')
   }
   setMediaId(registration.media_asset_id)
   setImageSha(verifiedUpload.image_sha256)
   setConfirmedRights(false)
   setStatus('Private model PNG registered as unverified source. Independent SHA and license evidence still required before review or reuse.')
  }catch{
   // Upload may have succeeded before an uncertain RPC response.
   // Never repeat an upload or POST automatically after a network failure.
   setStatus('Upload or registration unconfirmed. Check private asset history before any new attempt; do not upload again blindly.')
  }finally{setBusy(false)}
 }

 const importReady=UUID.test(modelId)&&UUID.test(mediaId)&&SHA.test(imageSha)&&SHA.test(licenseSha)&&label.trim().length>0&&uses.length>0
 const reviewReady=UUID.test(modelId)&&SHA.test(imageSha)&&Number.isInteger(Number(revision))&&Number(revision)>0&&evidence==='1'&&notes.trim().length>=12
 const verified=FIELDS.every(([k])=>checks[k]===true)
 const toggleUse=k=>setUses(a=>a.includes(k)?a.filter(v=>v!==k):[...a,k])
 const submit=async action=>{
  if(blocked)return
  setBusy(true);setReceipt(null);setStatus('')
  try{
   let result
   if(action==='import'){
    result=await api.importPendingModel(shopId,{
     model_id:modelId,media_asset_id:mediaId,source_kind:kind,label:label.trim(),
     image_sha256:imageSha,license_id:license,license_evidence_sha256:licenseSha,
     attribution,approved_uses:uses,
    })
    setRevision('1')
   } else if(action==='approve'||action==='reject'){
    result=await api.reviewModel(shopId,modelId,{
     decision:action==='approve'?'APPROVE':'REJECT',
     expected_revision:Number(revision),image_sha256:imageSha,
     evidence_revision:Number(evidence),
     checks:Object.fromEntries(FIELDS.map(([k])=>[k,checks[k]===true])),notes,
    })
    setRevision(String(result.rights_revision))
   } else{
    result=await api.revokeModel(shopId,modelId,{
     expected_revision:Number(revision),image_sha256:imageSha,reason:notes,
    })
    setRevision(String(result.rights_revision))
   }
   setReceipt(result)
   setStatus('Server confirmed '+result.status+'. This does not authorize GPU or publishing.')
  }catch{
   // No automatic retry of a stale/ambiguous POST, never infer success.
   setStatus('No confirmed result. Check signed shop, real evidence and current DB revision before a new attempt.')
  }finally{setBusy(false)}
 }
 return <section aria-label="Signed retailer model import and human review" style={{display:'grid',gap:10,padding:12,border:'1px solid #aaa',borderRadius:10}}>
  <h4>Private model registration and independent review</h4>
  <p>Use your own fictional adult-model PNG. This uploads to private shop Storage and registers an UNVERIFIED original. Import creates PENDING_REVIEW only; separate trusted byte/license evidence and independent review are mandatory. GPU is off.</p>
  <label style={field}>Model UUID<input value={modelId} onChange={e=>setModelId(e.target.value.toLowerCase())} disabled={blocked}/></label>
  <button type="button" disabled={blocked} onClick={()=>setModelId(globalThis.crypto.randomUUID())}>Create new model UUID</button>
  <fieldset disabled={blocked} style={{display:'grid',gap:6}}>
   <legend>Private original PNG upload (no approval or GPU)</legend>
   <label style={field}>Original synthetic adult model PNG
    <input type="file" accept="image/png" onChange={e=>setSourceFile(e.target.files?.[0]||null)}/>
   </label>
   <label style={field}>Source rights declaration
    <select value={sourceLicense} onChange={e=>setSourceLicense(e.target.value)}>
     <option value="owned">Owned synthetic creation</option>
     <option value="cc0">CC0</option><option value="commercial">Commercial license</option>
     <option value="royalty_free">Royalty free</option>
    </select>
   </label>
   {sourceLicense!=='owned'&&<label style={field}>HTTPS source-license evidence URL
    <input type="url" value={sourceLicenseUrl} onChange={e=>setSourceLicenseUrl(e.target.value)}/>
   </label>}
   <label><input type="checkbox" checked={confirmedRights}
     onChange={e=>setConfirmedRights(e.target.checked)}/>
    I declare I can upload this fictional adult model image. This is not independent rights verification.</label>
   <button type="button" disabled={blocked||!uploadReady} onClick={submitUpload}>
    Upload privately and register unverified original
   </button>
  </fieldset>
  <label style={field}>Registered private PNG media UUID<input value={mediaId} onChange={e=>setMediaId(e.target.value.toLowerCase())} disabled={blocked}/></label>
  <label style={field}>Original PNG SHA-256<input value={imageSha} onChange={e=>setImageSha(e.target.value.toLowerCase())} disabled={blocked}/></label>
  <label style={field}>Independent license-evidence SHA-256<input value={licenseSha} onChange={e=>setLicenseSha(e.target.value.toLowerCase())} disabled={blocked}/></label>
  <label style={field}>Source model label<input maxLength={64} value={label} onChange={e=>setLabel(e.target.value)} disabled={blocked}/></label>
  <label style={field}>Attribution<input maxLength={200} value={attribution} onChange={e=>setAttribution(e.target.value)} disabled={blocked}/></label>
  <label style={field}>Source provenance<select value={kind} onChange={e=>setKind(e.target.value)} disabled={blocked}>
   <option value="retailer_licensed">Retailer licensed</option><option value="created_ai">Created AI</option><option value="opensource_render">Open-source render</option>
  </select></label>
  <label style={field}>Verified license ID<select value={license} onChange={e=>setLicense(e.target.value)} disabled={blocked}>
   <option value="REVIEWED-COMMERCIAL">Reviewed commercial</option><option value="CC0-1.0">CC0</option><option value="CC-BY-4.0">CC BY 4.0</option>
  </select></label>
  <fieldset disabled={blocked}><legend>Requested uses (not approval)</legend>{['poster','try_on','video_reference'].map(k=><label key={k} style={{display:'block'}}>
   <input type="checkbox" checked={uses.includes(k)} onChange={()=>toggleUse(k)}/>{k}
  </label>)}</fieldset>
  <button type="button" disabled={blocked||!importReady} onClick={()=>submit('import')}>Register PENDING model</button>
  <fieldset disabled={blocked}><legend>Independent human checks — do not infer them from synthetic fixtures</legend>{FIELDS.map(([k,title])=><label key={k} style={{display:'block'}}>
   <input type="checkbox" checked={checks[k]===true} onChange={e=>setChecks(v=>({...v,[k]:e.target.checked}))}/>{title}
  </label>)}</fieldset>
  <label style={field}>Verified current model rights revision<input type="number" min="1" step="1" value={revision} onChange={e=>setRevision(e.target.value)} disabled={blocked}/></label>
  <label style={field}>Independently committed evidence revision<input type="number" min="1" step="1" value={evidence} onChange={e=>setEvidence(e.target.value)} disabled={blocked}/></label>
  <label style={field}>Reviewer notes/revocation reason (min 12 characters)<textarea maxLength={500} value={notes} onChange={e=>setNotes(e.target.value)} disabled={blocked}/></label>
  <div style={{display:'flex',gap:8,flexWrap:'wrap'}}>
   <button type="button" disabled={blocked||!reviewReady||!verified} onClick={()=>submit('approve')}>Approve after independent evidence</button>
   <button type="button" disabled={blocked||!reviewReady} onClick={()=>submit('reject')}>Reject model</button>
   <button type="button" disabled={blocked||!reviewReady} onClick={()=>submit('revoke')}>Revoke rights</button>
  </div>
  {receipt&&<p role="status">Model {receipt.model_id}: {receipt.status}. Revision {receipt.rights_revision}.</p>}
  {status&&<p role="status">{status}</p>}
 </section>
}
