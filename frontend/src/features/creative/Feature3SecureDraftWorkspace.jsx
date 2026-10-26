/** Optional, authenticated v2 drafts wrapper. Isolated from v1 saved posters.
 * Source-only: requires coordinator to supply feature3Api + registered private images.
 * No blind POST retries, no browser status promotion and no signed PNG claims.
 */
import { useRef, useState } from 'react'
import Feature3StudioPanel from './Feature3StudioPanel.jsx'
import { validateFeature3Design } from './feature3-design.mjs'

export default function Feature3SecureDraftWorkspace({
  shopId, campaignId, dayId, brandKit, imageMap = {}, approvedModels = [],
  approvedContent = null, feature3Api, disabled = false,
}) {
  const [saved, setSaved] = useState([])
  const [reopened, setReopened] = useState(null)
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const ticket = useRef({designId:null,revision:0})
  const pending = useRef(false)

  const loadHistory = async () => {
    if (disabled || busy || pending.current) return
    setBusy(true); setMessage('')
    try {
      const rows = await feature3Api.listDesigns(shopId, campaignId, dayId)
      setSaved(rows)
      setMessage(rows.length ? 'Private draft history loaded.' :
        'No v2 private poster drafts exist for this day.')
    } catch {
      setMessage('Could not read this day’s authorized v2 draft history.')
    } finally {
      setBusy(false)
    }
  }

  const restore = event => {
    const chosen = saved.find(d => d.id === event.target.value)
    if (!chosen) return
    try {
      if (chosen.status !== 'DRAFT') throw Error('Only editable drafts reopen')
      const design = validateFeature3Design(chosen.design)
      if (design.shop_id !== shopId ||
          design.layers.some(layer => layer.type === 'image' &&
            (!imageMap[layer.asset_id]?.complete ||
             !imageMap[layer.asset_id]?.naturalWidth ||
             !imageMap[layer.asset_id]?.naturalHeight))) {
        throw Error('Shop media grant must be refreshed first')
      }
      ticket.current = {designId:chosen.id,revision:chosen.revision}
      setReopened({id:chosen.id,revision:chosen.revision,design})
      setMessage('Authorized editable draft reopened. Saving uses revision CAS.')
    } catch {
      setMessage('Draft is no longer editable or private media access changed.')
    }
  }

  const saveDesign = async design => {
    if (disabled || pending.current) throw Error('Draft save already in progress')
    pending.current = true
    setBusy(true); setMessage('')
    try {
      const submitted = validateFeature3Design(design)
      if (submitted.shop_id !== shopId ||
          submitted.layers.some(layer => layer.type === 'image' &&
            (!imageMap[layer.asset_id]?.complete ||
             !imageMap[layer.asset_id]?.naturalWidth ||
             !imageMap[layer.asset_id]?.naturalHeight))) {
        throw Error('Registered media must still be authorized')
      }
      const response = await feature3Api.saveDesign(
        shopId,campaignId,dayId,submitted,{
          designId:ticket.current.designId,
          expectedRevision:ticket.current.revision,
        })
      ticket.current={designId:response.design_id,revision:response.revision}
      setMessage('Private v2 design metadata saved at revision '+response.revision+
        '. Not a rendered, reviewed or publishable poster.')
      return response
    } catch (error) {
      setMessage(error?.status === 409
        ? 'This revision is stale or no longer authorized. Refresh history; do not resend automatically.'
        : 'Save not confirmed. Do not retry blindly: it may already have committed. Read private history first.')
      throw error
    } finally {
      pending.current=false
      setBusy(false)
    }
  }
  if (!feature3Api || typeof feature3Api.listDesigns !== 'function' ||
      typeof feature3Api.saveDesign !== 'function') {
    return <p role="note">Authenticated v2 draft API not connected. Local
      CPU editor and day-bound JSON backup remain available.</p>
  }
  return <section aria-label="Private v2 poster drafts">
    <p role="note">Poster v2 saving requires authenticated shop membership and the
      new reviewed database migration. This does not use the v1 poster API.</p>
    <button type="button" disabled={disabled || busy} onClick={loadHistory}>
      Load privately saved v2 designs
    </button>
    {saved.length>0 && <label>Reopen editable v2 design
      <select defaultValue="" disabled={disabled || busy} onChange={restore}>
        <option value="">Select saved DRAFT</option>
        {saved.filter(d=>d.status==='DRAFT').map(d=>
          <option key={d.id} value={d.id}>Revision {d.revision} / {d.id.slice(0,8)}</option>)}
      </select>
    </label>}
    <Feature3StudioPanel
      key={reopened ? reopened.id+':'+reopened.revision : 'new-'+shopId+dayId}
      shopId={shopId} campaignId={campaignId} dayId={dayId}
      brandKit={brandKit} imageMap={imageMap} approvedModels={approvedModels}
      approvedContent={approvedContent} restoredDesign={reopened}
      disabled={disabled || busy} onSaveDesign={saveDesign}/>
    {message && <p role="status">{message}</p>}
  </section>
}
