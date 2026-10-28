/** Feature #3 zero-cost source-review gallery for import-first Indian fashion.
 *
 * This panel shows pinned *synthetic* upstream candidates. It never loads
 * their images, calls GitHub from the browser, uploads assets, changes tenant
 * permissions, charges a GPU or declares commercial rights approved.
 *
 * Actual import must be a separate signed-in coordinator-owned flow that
 * independently verifies image bytes, license, human approval and shop RLS.
 */
import { useState } from 'react'
import Feature3SignedModelWorkflow from './Feature3SignedModelWorkflow.jsx'
import {
  INDIAN_MODEL_CANDIDATES, getIndianModelCandidate,
  indianModelReviewUrl, createIndianModelReviewPacket,
} from './feature3-indian-model-review.mjs'

const field = { display: 'grid', gap: 6 }
const controls = { display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }
const card = { border: '1px solid #a8a8a8', borderRadius: 10, padding: 12, display: 'grid', gap: 6 }
const selector = { width: '100%', maxWidth: 360 }

export default function Feature3ModelLibraryReview({ disabled = false, shopId = null, workflowApi = null, workflowEnabled = false }) {
  const [presentation, setPresentation] = useState('all')
  const [personId, setPersonId] = useState('P009')
  const [kind, setKind] = useState('studio_posture')
  const [message, setMessage] = useState('')
  const candidates = INDIAN_MODEL_CANDIDATES.filter(candidate =>
    presentation === 'all' || candidate.metadataPresentation === presentation)
  const selected = getIndianModelCandidate(personId)
  const sourceLink = selected ? indianModelReviewUrl(selected.id, kind) : null

  const downloadReviewPacket = () => {
    if (disabled || !sourceLink || !selected) return
    try {
      const packet = createIndianModelReviewPacket(personId, kind)
      const blob = new Blob([JSON.stringify(packet, null, 2)],
        { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `feature3-review-only-${personId}-${kind}.json`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.setTimeout(() => URL.revokeObjectURL(url), 1000)
      setMessage('Source review packet saved locally. No model has been imported or approved.')
    } catch {
      setMessage('Could not prepare source review packet.')
    }
  }

  const changePresentation = value => {
    setPresentation(value)
    const filtered = INDIAN_MODEL_CANDIDATES.filter(c =>
      value === 'all' || c.metadataPresentation === value)
    setPersonId(filtered[0]?.id || '')
    setMessage('')
  }

  return <section aria-label="Indian AI fashion model library review" style={card}>
    <header>
      <h3>Indian fashion model library — import-first preview</h3>
      <p>Eight fictional AI characters, sourced from the pinned OpenPeople catalog.
        These are profile labels supplied by its generation metadata, not verified
        nationalities or real people.</p>
      <p role="note">Source images and commercial reuse rights are still awaiting
        independent review. Nothing is uploaded, published or billed here.</p>
    </header>
    <div style={{ display: 'grid', gridTemplateColumns:
      'repeat(auto-fit,minmax(min(100%,230px),1fr))', gap: 12 }}>
      <label style={field}>Model category
        <select style={selector} value={presentation} disabled={disabled}
          onChange={e => changePresentation(e.target.value)}>
          <option value="all">All 8 character profiles</option>
          <option value="female">Female-presenting metadata</option>
          <option value="male">Male-presenting metadata</option>
        </select>
      </label>
      <label style={field}>Existing character
        <select style={selector} value={personId} disabled={disabled}
          onChange={e => {setPersonId(e.target.value);setMessage('')}}>
          {candidates.map(c => <option key={c.id} value={c.id}>
            {c.id} · {c.metadataPresentation} · {c.ageRange}
          </option>)}
        </select>
      </label>
      <label style={field}>Existing image
        <select style={selector} value={kind} disabled={disabled}
          onChange={e => {setKind(e.target.value);setMessage('')}}>
          <option value="studio_posture">Full-body model</option>
          <option value="studio_portrait">Portrait reference</option>
        </select>
      </label>
    </div>
    {selected && <>
      <p><strong>Dataset's synthetic profile:</strong> {selected.metadataDescription}.
        This is not verified Indian heritage or a real person's identity.</p>
      <p><strong>Review status:</strong> Commercial license, image quality,
        retailer suitability and private import are all pending.</p>
      <div style={controls}>
        <a href={sourceLink} target="_blank" rel="noopener noreferrer">
          Inspect original {kind === 'studio_posture' ? 'full-body' : 'portrait'} image on GitHub
        </a>
        <button type="button" onClick={downloadReviewPacket} disabled={disabled}>
          Download curator review packet (not approval)
        </button>
      </div>
    </>}
    <div style={card}>
      <strong>Optional: Create New AI Model</strong>
      <p>Custom FLUX generation remains a separate, GPU-paid option.
        It is not activated in this review-only source gallery.</p>
      <button type="button" disabled>Create new model — awaiting approved GPU integration</button>
    </div>
    <p role="note">After approval, one saved model can be reused as a
      poster image, a virtual try-on person reference and a video reference.
      Try-on and AI motion still require separate licensed inference.</p>
    {workflowEnabled && workflowApi && <Feature3SignedModelWorkflow key={shopId} shopId={shopId}
      api={workflowApi} enabled={workflowEnabled} disabled={disabled} />}
    {message && <p role="status">{message}</p>}
  </section>
}
