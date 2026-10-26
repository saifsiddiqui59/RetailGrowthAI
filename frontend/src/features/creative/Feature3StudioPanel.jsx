/** Feature #3 isolated creation UX — host supplies JWT-authorized tenant context.
 *
 * NOT mounted in App.jsx until coordinator pins react-konva/konva and freezes
 * v2 authenticated draft/queue APIs. All generated images and virtual try-on
 * require backend approval; this CPU panel only composes versioned layers.
 */
import { useMemo, useState } from 'react'
import { FEATURE3_FORMATS, FEATURE3_TEMPLATES } from './feature3-design.mjs'
import { composeFeature3Poster } from './feature3-compose.mjs'
import { approvedFeature3Inputs, feature3ContextKey } from './feature3-context.mjs'
import Feature3CpuEditor from './Feature3CpuEditor.jsx'
import Feature3ModelLibraryReview from './Feature3ModelLibraryReview.jsx'
import { availableApprovedModels, selectedApprovedModel } from './feature3-approved-models.mjs'

const fieldStyle = { display: 'grid', gap: 6, minWidth: 0 }
const inputStyle = { width: '100%', maxWidth: '100%', boxSizing: 'border-box' }
const rootStyle = { display: 'grid', gap: 16, width: '100%', minWidth: 0 }

export default function Feature3StudioPanel({
  shopId, campaignId, dayId, brandKit, imageMap = {}, approvedContent = null,
  onSaveDesign = null, approvedModels = [], restoredDesign = null, disabled = false,
}) {
  const [mode, setMode] = useState('text')
  const [prompt, setPrompt] = useState('')
  const [template, setTemplate] = useState('auto')
  const [format, setFormat] = useState('square')
  const [assetId, setAssetId] = useState('')
  const [modelId, setModelId] = useState('')
  const [designModelRef, setDesignModelRef] = useState(null)
  const [version, setVersion] = useState(restoredDesign?.revision || 0)
  const [design, setDesign] = useState(() => restoredDesign?.design || null)
  const [showModelLibrary, setShowModelLibrary] = useState(false)
  const [designContext, setDesignContext] = useState(() =>
    restoredDesign ? feature3ContextKey({shopId,campaignId,dayId}) : '')
  const [error, setError] = useState('')

  // These are pre-authorized/private media previews supplied by the
  // authenticated host. The server must still recheck rights and RLS.
  const authorized = useMemo(() => Object.keys(imageMap).filter(id =>
    /^[a-zA-Z0-9_-]{1,100}$/.test(id) &&
    imageMap[id]?.complete &&
    imageMap[id]?.naturalWidth > 0 &&
    imageMap[id]?.naturalHeight > 0
  ), [imageMap])
  // Catalog rows are signed-in host data only. They never authorize saving or
  // spending by themselves; private media and server rights must be rechecked.
  const readyModels = availableApprovedModels(approvedModels, shopId, imageMap)
  const selectedModel = selectedApprovedModel(readyModels, modelId)
  const designModelStillReady = !designModelRef || readyModels.some(model =>
    model.modelId === designModelRef.modelId &&
    model.mediaAssetId === designModelRef.mediaAssetId &&
    model.imageSha256 === designModelRef.imageSha256)
  const context = { shopId, campaignId, dayId }
  const currentContext = feature3ContextKey(context)
  const checked = approvedFeature3Inputs(approvedContent, context, brandKit)
  const approved = checked.approved
  const businessName = checked.brand?.businessName || ''
  const brandLogo = checked.brand?.logoAssetId &&
    authorized.includes(checked.brand.logoAssetId)
    ? checked.brand.logoAssetId : null

  const create = () => {
    setError('')
    if (disabled) return
    try {
      if (!currentContext || !businessName) throw Error('Select a verified business and campaign day first')
      if (mode === 'image' && !authorized.includes(assetId)) {
        throw Error('Choose a registered shop product photo')
      }
      if (mode === 'model' && !selectedModel) {
        throw Error('Select an approved, currently accessible saved AI model')
      }
      const sourceAssetId = mode === 'model' ? selectedModel.mediaAssetId :
        mode === 'image' ? assetId : null
      // Caller-provided merchant-side approval is only a UX hint.
      // The server MUST separately reload and validate original approved
      // campaign copy and merchant offers, then reconcile the design hash.
      const next = composeFeature3Poster({
        shopId, mode: mode === 'model' ? 'image' : mode, prompt,
        businessName,
        headline: approved ? approved.headline : null,
        cta: approved ? approved.cta : 'Visit our store',
        approvedOffer: approved ? approved.offer_text : null,
        sourceAssetId,
        authorizedAssetIds: authorized,
        logoAssetId: brandLogo,
        template: template === 'auto' ? null : template,
        format,
        accent: checked.brand?.accentColor || '#C05F43',
        background: checked.brand?.backgroundColor || '#FCF4EC',
      })
      setDesign(next)
      setDesignModelRef(mode === 'model' ? {
        modelId: selectedModel.modelId, mediaAssetId: selectedModel.mediaAssetId,
        imageSha256: selectedModel.imageSha256,
      } : null)
      setDesignContext(currentContext)
      setVersion(v => v + 1)
    } catch (cause) {
      setError(cause.message || 'Could not prepare this poster')
    }
  }

  return <section aria-label="AI Poster Studio creation modes" style={rootStyle}>
    <header>
      <h2>Professional Poster Studio</h2>
      <p>Start with CPU templates and approved business assets. AI fashion-model
        generation and virtual try-on remain unavailable until licensed GPU
        inference has been enabled for your business.</p>
    </header>
    <fieldset disabled={disabled} style={{ display: 'grid', gap: 10 }}>
      <legend>Choose a creation mode</legend>
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <label><input type="radio" name="feature3-mode" checked={mode === 'text'}
          onChange={() => {setMode('text'); setError('')}}/> Text-to-Poster</label>
        <label><input type="radio" name="feature3-mode" checked={mode === 'image'}
          disabled={!authorized.length}
          onChange={() => {setMode('image'); setError('')}}/> Image-to-Poster</label>
        <label><input type="radio" name="feature3-mode" checked={mode === 'model'}
          disabled={!readyModels.length}
          onChange={() => {setMode('model'); setError('')}}/> Saved AI model poster (CPU)</label>
      </div>
      <label style={fieldStyle}>Describe the advertisement
        <textarea style={inputStyle} maxLength={800} rows={3} value={prompt}
          onChange={event => setPrompt(event.target.value)}
          placeholder="Premium Diwali boutique advertisement in warm gold lighting" />
      </label>
      {!authorized.length && <p role="note">Image-to-Poster requires the host to
        supply an already-authorized, loaded private product image. This local
        mode cannot register uploads or fetch remote product URLs.</p>}
      {mode === 'model' && <label style={fieldStyle}>Approved saved fashion model
        <select style={inputStyle} value={selectedModel ? modelId : ''}
          onChange={event => setModelId(event.target.value)}>
          <option value="">Choose an approved model</option>
          {readyModels.map(model => <option key={model.modelId} value={model.modelId}>
            {model.label} · {model.scope === 'platform' ? 'Shared catalog' : 'Shop private'}
          </option>)}
        </select>
        <small>Uses an already-approved still image. It does not change the model's clothes,
          generate try-on or spend GPU credits. Server must revalidate media and model rights.</small>
      </label>}
      {!readyModels.length && <p role="note">No approved, currently accessible saved models are
        supplied by the authenticated library. Source-review candidates are not selectable.</p>}
      {mode === 'image' && <label style={fieldStyle}>Registered product image
        <select style={inputStyle} value={assetId}
          onChange={event => setAssetId(event.target.value)}>
          <option value="">Choose your authorized photo</option>
          {authorized.map(id => <option key={id} value={id}>
            Shop asset {id.slice(0, 8)}
          </option>)}
        </select>
      </label>}
      <div style={{ display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit,minmax(min(100%,180px),1fr))',
        gap: 12 }}>
        <label style={fieldStyle}>Layout
          <select value={template} onChange={e => setTemplate(e.target.value)}>
            <option value="auto">Auto-select suitable template</option>
            {FEATURE3_TEMPLATES.map(t => <option key={t} value={t}>
              {t.replaceAll('_', ' ')}
            </option>)}
          </select>
        </label>
        <label style={fieldStyle}>Canvas format
          <select value={format} onChange={e => setFormat(e.target.value)}>
            {Object.entries(FEATURE3_FORMATS).map(([id, [w, h]]) =>
              <option key={id} value={id}>{id} · {w} × {h}</option>)}
          </select>
        </label>
      </div>
      {!approved && <p role="note">No approved campaign copy is linked to this design.
        Discounts and prices mentioned only in the prompt will not be printed.
        You can still make a template draft for review.</p>}
      {approved && <p role="status">Using retailer-approved campaign headline and offer.
        AI-generated imagery is not included.</p>}
      <button type="button" onClick={create}
        disabled={!currentContext || !prompt.trim() || !businessName ||
          (mode === 'image' && !assetId) || (mode === 'model' && !selectedModel)}>
        Generate editable poster
      </button>
      {error && <p role="alert">{error}</p>}
    </fieldset>
    {!designModelStillReady &&
      <p role="alert">The saved model is no longer accessible. This local model draft is hidden;
        select another approved model.</p>}
    {design && designContext === currentContext &&
      designModelStillReady &&
      <Feature3CpuEditor key={version} initialDesign={design}
      imageMap={imageMap} context={context} onSaveDraft={onSaveDesign} />}
    <section aria-label="Reusable AI fashion models">
      <button type="button" disabled={disabled}
        aria-expanded={showModelLibrary}
        onClick={() => setShowModelLibrary(value => !value)}>
        {showModelLibrary ? 'Hide model library review' : 'Explore existing AI fashion models (no GPU)'}
      </button>
      {showModelLibrary && <Feature3ModelLibraryReview disabled={disabled} />}
    </section>
  </section>
}
