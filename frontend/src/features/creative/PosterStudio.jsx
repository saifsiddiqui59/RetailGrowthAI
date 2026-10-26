import { useEffect, useRef, useState } from 'react'
import { drawPoster, POSTER_SIZES, POSTER_TEMPLATES } from './poster-canvas.mjs'
import { validateSignedVideoUrl } from '../campaigns/campaign-api.mjs'
import './PosterStudio.css'
import Feature3StudioPanel from './Feature3StudioPanel.jsx'
import Feature3SecureDraftWorkspace from './Feature3SecureDraftWorkspace.jsx'
import { feature3ContextKey } from './feature3-context.mjs'

const MAX_BYTES = 25 * 1024 * 1024
const SUPPORTED = new Set(['image/jpeg', 'image/png', 'image/webp'])

export default function PosterStudio({ day, businessName = 'Your business', api = null,
  campaignId = '', persisted = false, authorizedAssets = [], supabaseOrigin = '', onSelected = null,
  approvedModels = [], authenticatedModelImageMap = {}, feature3Api = null }) {
  const canvas = useRef(null)
  const [brand, setBrand] = useState(businessName || 'Your business')
  const [template, setTemplate] = useState('editorial')
  const [size, setSize] = useState('square')
  const [accent, setAccent] = useState('#B96349')
  const [background, setBackground] = useState('#F6F0E8')
  const [offer, setOffer] = useState('')
  const [photoFile, setPhotoFile] = useState(null)
  const [photo, setPhoto] = useState(null)
  const [rights, setRights] = useState(false)
  const [error, setError] = useState('')
  const [downloadError, setDownloadError] = useState('')
  const [ready, setReady] = useState(false)
  const [sourceAssetId, setSourceAssetId] = useState('')
  const [remoteDraft, setRemoteDraft] = useState('')
  const [remoteJob, setRemoteJob] = useState(null)
  const [remoteBusy, setRemoteBusy] = useState(false)
  const [remoteError, setRemoteError] = useState('')
  const [remoteMessage, setRemoteMessage] = useState('')
  const [savedPosters, setSavedPosters] = useState([])
  const [historyBusy, setHistoryBusy] = useState(false)
  const [showCpuStudio, setShowCpuStudio] = useState(false)

  useEffect(() => {
    setBrand(businessName || 'Your business')
  }, [businessName])
  useEffect(() => {
    // Offers cannot silently carry over from a different campaign day.
    setOffer('')
    setRights(false)
  }, [day.id])
  // Saved assets are drawn only from the authenticated shop media list AND
  // from this persisted campaign day's storyboard. No raw user URL or fixture ID.
  const allowedSources = (day.instagram?.reel?.storyboard || [])
    .map(scene => scene.asset_id)
    .filter((id, index, ids) => ids.indexOf(id) === index)
    .filter(id => authorizedAssets.some(asset => asset.id === id))
  useEffect(() => {
    setSourceAssetId('')
    setRemoteDraft('')
    setRemoteJob(null)
    setRemoteMessage('')
    setRemoteError('')
    setSavedPosters([])
    setShowCpuStudio(false)
  }, [day.id, campaignId])
  // Only intentional edits invalidate the selected cloud draft. Restoring a
  // saved design must not be erased by its own programmatic field updates.
  function updateDesign(setter, value) {
    setter(value)
    setRemoteDraft('')
    setRemoteJob(null)
    setRemoteMessage('')
    setRemoteError('')
  }

  async function refreshSavedPosters() {
    if (!api || !persisted || !campaignId || !day.id) return
    setHistoryBusy(true)
    setRemoteError('')
    try {
      const response = await api.listPosterDrafts(campaignId, day.id)
      if (!response || !Array.isArray(response.posters) || response.posters.length > 21) {
        throw new Error('Saved poster history was not verified')
      }
      setSavedPosters(response.posters)
    } catch (problem) {
      setRemoteError(problem.message)
    } finally { setHistoryBusy(false) }
  }

  function restoreSavedPoster(poster) {
    if (!poster || !allowedSources.includes(poster.source_asset_id)) {
      setRemoteError('The saved design source is no longer in this campaign day. Choose a licensed image.')
      return
    }
    // Source is checked against live tenant-authorized day media; the server
    // rechecks RLS and revoked rights again before render or signed download.
    setTemplate(poster.template)
    setSize(poster.format)
    setBrand(poster.business_name)
    setAccent(poster.accent_color)
    setBackground(poster.background_color)
    setOffer(poster.offer_text || '')
    setSourceAssetId(poster.source_asset_id)
    setRemoteDraft(poster.poster_id)
    setRemoteJob(poster.job_id ? {job_id: poster.job_id, status: poster.job_status} : null)
    setRemoteMessage('Saved design reopened. Cloud output is available only if its job succeeded.')
    setRemoteError('')
  }
  useEffect(() => {
    if (!api || !remoteJob || !['QUEUED', 'RUNNING'].includes(remoteJob.status)) return
    let active = true
    let count = 0
    const interval = window.setInterval(async () => {
      if (!active) return
      count += 1
      if (count > 30) {
        window.clearInterval(interval)
        setRemoteError('Poster is taking longer than expected. Refresh the job status later.')
        return
      }
      try {
        const job = await api.getPosterJob(remoteJob.job_id)
        if (!active) return
        setRemoteJob(job)
        if (!['QUEUED', 'RUNNING'].includes(job.status)) window.clearInterval(interval)
      } catch (problem) {
        if (active) {
          setRemoteError(problem.message)
          window.clearInterval(interval)
        }
      }
    }, 4000)
    return () => { active = false; window.clearInterval(interval) }
  }, [api, remoteJob?.job_id, remoteJob?.status])

  async function saveCloudDraft() {
    if (!api || !persisted || !campaignId || !rights || !allowedSources.includes(sourceAssetId)) return
    setRemoteBusy(true); setRemoteError(''); setRemoteMessage('')
    try {
      const saved = await api.createPosterDraft(campaignId, {
        day_id: day.id, source_asset_id: sourceAssetId,
        template, format: size, business_name: brand,
        accent_color: accent, background_color: background,
        offer_text: offer.trim() || null,
      })
      setRemoteDraft(saved.poster_id)
      setRemoteJob(null)
      setSavedPosters(previous => previous.filter(p => p.poster_id !== saved.poster_id))
      setRemoteMessage('Poster design saved privately. Start secure rendering to generate its PNG.')
    } catch (problem) { setRemoteError(problem.message) }
    finally { setRemoteBusy(false) }
  }

  async function startCloudRender() {
    if (!remoteDraft || !api) return
    setRemoteBusy(true); setRemoteError('')
    try {
      setRemoteJob(await api.createPosterRender(remoteDraft))
      setRemoteMessage('Private poster rendering requested. Checking job status…')
    } catch (problem) { setRemoteError(problem.message) }
    finally { setRemoteBusy(false) }
  }

  async function selectCloudBanner() {
    if (!api || !persisted || remoteJob?.status !== 'SUCCEEDED' || !remoteDraft) return
    setRemoteBusy(true); setRemoteError('')
    try {
      await api.selectPosterBanner(remoteDraft, day.instagram)
      if (typeof onSelected === 'function') await onSelected()
      setRemoteMessage('Reviewed poster attached to this saved campaign day. Publishing is still separate.')
    } catch (problem) { setRemoteError(problem.message) }
    finally { setRemoteBusy(false) }
  }

  async function downloadCloudPoster() {
    if (remoteJob?.status !== 'SUCCEEDED' || !api) return
    setRemoteBusy(true); setRemoteError('')
    try {
      const result = await api.getPosterDownload(remoteJob.job_id)
      const url = validateSignedVideoUrl(result.url, supabaseOrigin)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.target = '_blank'
      anchor.rel = 'noopener noreferrer'
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
      setRemoteMessage('Opened the short-lived private PNG link.')
    } catch (problem) { setRemoteError(problem.message) }
    finally { setRemoteBusy(false) }
  }

  useEffect(() => {
    if (!photoFile) { setPhoto(null); return }
    let active = true
    const url = URL.createObjectURL(photoFile)
    const image = new Image()
    image.onload = () => {
      URL.revokeObjectURL(url)
      if (!active) return
      if (!image.width || !image.height || image.width > 8192 ||
          image.height > 8192 || image.width * image.height > 24_000_000) {
        setPhoto(null)
        setError('Photo dimensions must be within 8,192 pixels per side and 24 megapixels.')
      } else {
        setPhoto(image)
        setError('')
      }
    }
    image.onerror = () => {
      URL.revokeObjectURL(url)
      if (active) { setPhoto(null); setError('Could not decode this image. Try a standard JPG, PNG or WebP.') }
    }
    image.src = url
    return () => { active = false; URL.revokeObjectURL(url) }
  }, [photoFile])

  useEffect(() => {
    if (!canvas.current) return
    try {
      drawPoster(canvas.current, photo, day,
        { template, size, brand, accent, background, offer })
      setReady(true)
      setDownloadError('')
    } catch (problem) {
      setReady(false)
      setDownloadError(problem.message)
    }
  }, [photo, day, template, size, brand, accent, background, offer])

  function chooseFile(event) {
    const file = event.target.files?.[0] || null
    setRights(false)
    setPhoto(null)
    setPhotoFile(null)
    setError('')
    if (!file) return
    if (!SUPPORTED.has(file.type) || file.size <= 0 || file.size > MAX_BYTES) {
      setError('Use a JPG, PNG or WebP image up to 25 MB. HEIC and animated files are not supported.')
      return
    }
    setPhotoFile(file)
  }

  function download() {
    if (!photo || !rights || !ready || !canvas.current) return
    const name = 'retailgrowth-day-' + day.day_index + '-' + template + '-' + size + '.png'
    canvas.current.toBlob(blob => {
      if (!blob) { setDownloadError('Could not export PNG in this browser.'); return }
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = name
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.setTimeout(() => URL.revokeObjectURL(url), 1000)
    }, 'image/png')
  }

  return (
    <section className="rg-creative rg-panel" aria-labelledby="rg-creative-title">
      <div className="rg-inline-title">
        <div><span className="rg-kicker">05 / PROMOTIONAL POSTER</span>
          <h2 id="rg-creative-title">Your brand, ready to share.</h2>
          <p>Compose a promotional graphic from today's campaign draft and your own product photo.</p>
        </div>
        <span className="rg-mini-pill">PNG · Preview</span>
      </div>
      <div className="rg-creative-grid">
        <div className="rg-creative-controls">
          <label className="rg-field">
            <span>Business name</span>
            <input aria-label="Poster business name" value={brand}
              maxLength={70} onChange={event => updateDesign(setBrand, event.target.value)} />
          </label>
          <label className="rg-field">
            <span>Product photo (JPG, PNG or WebP)</span>
            <input aria-label="Poster product photo" type="file"
              accept="image/jpeg,image/png,image/webp" onChange={chooseFile} />
          </label>
          {error && <p role="alert" className="rg-validation">{error}</p>}
          <div className="rg-creative-pairs">
            <label className="rg-field"><span>Layout</span>
              <select aria-label="Poster template" value={template}
                onChange={event => updateDesign(setTemplate, event.target.value)}>
                {POSTER_TEMPLATES.map(value => <option key={value} value={value}>
                  {value[0].toUpperCase() + value.slice(1)}</option>)}
              </select>
            </label>
            <label className="rg-field"><span>Format</span>
              <select aria-label="Poster size" value={size}
                onChange={event => updateDesign(setSize, event.target.value)}>
                <option value="square">Square · 1080 × 1080</option>
                <option value="portrait">Portrait · 1080 × 1350</option>
              </select>
            </label>
          </div>
          <div className="rg-creative-pairs">
            <label className="rg-field"><span>Accent</span>
              <input aria-label="Poster accent color" type="color" value={accent}
                onChange={event => updateDesign(setAccent, event.target.value)} />
            </label>
            <label className="rg-field"><span>Background</span>
              <input aria-label="Poster background color" type="color" value={background}
                onChange={event => updateDesign(setBackground, event.target.value)} />
            </label>
          </div>
          <label className="rg-field"><span>Approved offer (optional)</span>
            <input aria-label="Poster offer" value={offer} maxLength={110}
              onChange={event => updateDesign(setOffer, event.target.value)}
              placeholder="e.g. 20% off through Nov 14" />
            <small>Enter only genuine, approved offers; no offer is invented by the app.</small>
          </label>
          <label className="rg-creative-consent">
            <input type="checkbox" checked={rights} onChange={event => setRights(event.target.checked)} />
            <span>I confirm I have the commercial rights to use this product image.</span>
          </label>
          <button type="button" className="rg-button rg-primary"
            disabled={!ready || !photo || !rights} onClick={download}>
            Download generated PNG
          </button>
          <div className="rg-poster-remote" aria-label="Save poster to RetailGrowthAI">
            <h3>Save to your business</h3>
            {!persisted && <p className="rg-subtle">Cloud saving is available only for an authenticated, saved campaign day. Local poster downloads remain available.</p>}
            {persisted && <p className="rg-subtle">Cloud rendering uses your registered, licensed campaign image—not the temporary local photo preview above.</p>}
            {persisted && <label className="rg-field"><span>Registered campaign product image</span>
              <select aria-label="Saved poster source image" value={sourceAssetId}
                onChange={event => updateDesign(setSourceAssetId, event.target.value)}>
                <option value="">Select a registered image</option>
                {allowedSources.map(id => <option value={id} key={id}>{id.slice(0, 8)} · Approved shop media</option>)}
              </select>
            </label>}
            {persisted && <>
              <button className="rg-button rg-secondary" type="button"
                disabled={!api || historyBusy || remoteBusy}
                onClick={refreshSavedPosters}>Find saved posters</button>
              {historyBusy && <p role="status">Checking private saved designs…</p>}
              {savedPosters.length > 0 && <label className="rg-field">
                <span>Reopen saved design</span>
                <select aria-label="Reopen saved poster" defaultValue=""
                  onChange={event => {
                    const chosen = savedPosters.find(p => p.poster_id === event.target.value)
                    if (chosen) restoreSavedPoster(chosen)
                  }}>
                  <option value="">Select a saved design</option>
                  {savedPosters.map(p => <option key={p.poster_id} value={p.poster_id}>
                    {p.template} · {p.format} · {p.status} · {p.poster_id.slice(0, 8)}
                  </option>)}
                </select>
              </label>}
              {savedPosters.length === 0 && !historyBusy &&
                <p className="rg-subtle">Select “Find saved posters” to reopen designs saved under this campaign day.</p>}
            </>}
            <button className="rg-button rg-secondary" type="button"
              disabled={!persisted || remoteBusy || !rights || !allowedSources.includes(sourceAssetId)}
              onClick={saveCloudDraft}>Save design privately</button>
            <button className="rg-button rg-secondary" type="button"
              disabled={!remoteDraft || remoteBusy}
              onClick={startCloudRender}>Generate cloud PNG</button>
            {remoteJob && <p role="status">Poster job: {remoteJob.status}</p>}
            <button className="rg-button rg-primary" type="button"
              disabled={!remoteJob || remoteJob.status !== 'SUCCEEDED' || remoteBusy}
              onClick={downloadCloudPoster}>Open private PNG download</button>
            <button className="rg-button rg-secondary" type="button"
              disabled={!persisted || !remoteJob || remoteJob.status !== 'SUCCEEDED' || remoteBusy}
              onClick={selectCloudBanner}>Use this poster as campaign banner</button>
            {remoteMessage && <p role="status">{remoteMessage}</p>}
            {remoteError && <p role="alert" className="rg-validation">{remoteError}</p>}
          </div>
          {downloadError && <p className="rg-validation" role="alert">{downloadError}</p>}
          <p className="rg-subtle">The local PNG download remains on this device. Cloud designs are saved only after explicit consent; publishing is a separate process.</p>
        </div>
        <div className="rg-creative-preview">
          <canvas ref={canvas} className="rg-creative-canvas" role="img"
            aria-label={'Live ' + template + ' poster preview for campaign day ' + day.day_index} />
          <p className="rg-subtle">{POSTER_SIZES[size].join(' × ')} pixels · Day {day.day_index} · {photo ? 'Your photo' : 'Add your photo for export'}</p>
        </div>
      </div>
      {persisted && feature3ContextKey({
        shopId: day.shop_id, campaignId, dayId: day.id,
      }) && <div className="rg-poster-remote"
        aria-label="Low-cost poster design (local)">
        <button type="button" className="rg-button rg-secondary"
          aria-expanded={showCpuStudio}
          onClick={() => setShowCpuStudio(open => !open)}>
          {showCpuStudio ? 'Hide' : 'Open'} CPU Poster Studio (local editable draft)
        </button>
        <p className="rg-subtle">Create text-led promotional layouts with
          no new dependency or GPU. This v2 editor is local-only:
          its JSON is not a saved campaign poster, and the live private
          v1 save/render/select controls above remain separate.</p>
        {showCpuStudio && (feature3Api
          ? <Feature3SecureDraftWorkspace
              key={day.id + ':' + campaignId}
              shopId={day.shop_id} campaignId={campaignId} dayId={day.id}
              brandKit={{shopId: day.shop_id, businessName: brand}}
              imageMap={authenticatedModelImageMap}
              approvedModels={approvedModels} feature3Api={feature3Api} />
          : <Feature3StudioPanel
              key={day.id + ':' + campaignId}
              shopId={day.shop_id} campaignId={campaignId} dayId={day.id}
              brandKit={{shopId: day.shop_id, businessName: brand}}
              imageMap={authenticatedModelImageMap}
              approvedModels={approvedModels} />)}
      </div>}
    </section>
  )
}
