/** Feature #3 isolated creation UX — host supplies JWT-authorized tenant context.
 *
 * NOT mounted in App.jsx until coordinator pins react-konva/konva and freezes
 * v2 authenticated draft/queue APIs. All generated images and virtual try-on
 * require backend approval; this CPU panel only composes versioned layers.
 */
import { useMemo, useState } from 'react'
import { FEATURE3_FORMATS, FEATURE3_TEMPLATES } from './feature3-design.mjs'
import { composeFeature3Poster } from './feature3-compose.mjs'
import Feature3KonvaEditor from './Feature3KonvaEditor.jsx'

const fieldStyle = { display: 'grid', gap: 6, minWidth: 0 }
const inputStyle = { width: '100%', maxWidth: '100%', boxSizing: 'border-box' }
const rootStyle = { display: 'grid', gap: 16, width: '100%', minWidth: 0 }

export default function Feature3StudioPanel({
  shopId, brandKit, imageMap = {}, approvedContent = null,
  onSaveDesign = null, disabled = false,
}) {
  const [mode, setMode] = useState('text')
  const [prompt, setPrompt] = useState('')
  const [template, setTemplate] = useState('auto')
  const [format, setFormat] = useState('square')
  const [assetId, setAssetId] = useState('')
  const [version, setVersion] = useState(0)
  const [design, setDesign] = useState(null)
  const [error, setError] = useState('')

  // These are pre-authorized/private media previews supplied by the
  // authenticated host. The server must still recheck rights and RLS.
  const authorized = useMemo(() => Object.keys(imageMap).filter(id =>
    /^[a-zA-Z0-9_-]{1,100}$/.test(id) &&
    imageMap[id]?.complete &&
    imageMap[id]?.naturalWidth > 0 &&
    imageMap[id]?.naturalHeight > 0
  ), [imageMap])
  const approved = !!(approvedContent?.review_state === 'APPROVED' &&
    approvedContent?.shop_id === shopId &&
    Number.isInteger(approvedContent?.approved_version) &&
    approvedContent.approved_version >= 1)
  const businessName = brandKit?.businessName || ''
  const brandLogo = brandKit?.logoAssetId && authorized.includes(brandKit.logoAssetId)
    ? brandKit.logoAssetId : null

  const create = () => {
    setError('')
    if (disabled) return
    try {
      if (!shopId || !businessName) throw Error('Select an authorized business first')
      if (mode === 'image' && !authorized.includes(assetId)) {
        throw Error('Choose a registered shop product photo')
      }
      // Caller-provided merchant-side approval is only a UX hint.
      // The server MUST separately reload and validate original approved
      // campaign copy and merchant offers, then reconcile the design hash.
      const next = composeFeature3Poster({
        shopId, mode, prompt,
        businessName,
        headline: approved ? approvedContent.headline : null,
        cta: approved ? approvedContent.cta : 'Visit our store',
        approvedOffer: approved ? approvedContent.offer_text : null,
        sourceAssetId: mode === 'image' ? assetId : null,
        authorizedAssetIds: authorized,
        logoAssetId: brandLogo,
        template: template === 'auto' ? null : template,
        format,
        accent: brandKit?.accentColor || '#C05F43',
        background: brandKit?.backgroundColor || '#FCF4EC',
      })
      setDesign(next)
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
          onChange={() => {setMode('image'); setError('')}}/> Image-to-Poster</label>
      </div>
      <label style={fieldStyle}>Describe the advertisement
        <textarea style={inputStyle} maxLength={800} rows={3} value={prompt}
          onChange={event => setPrompt(event.target.value)}
          placeholder="Premium Diwali boutique advertisement in warm gold lighting" />
      </label>
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
        disabled={!prompt.trim() || !businessName || (mode === 'image' && !assetId)}>
        Generate editable poster
      </button>
      {error && <p role="alert">{error}</p>}
    </fieldset>
    {design && <Feature3KonvaEditor key={version} initialDesign={design}
      imageMap={imageMap} onSaveDraft={onSaveDesign} />}
  </section>
}
