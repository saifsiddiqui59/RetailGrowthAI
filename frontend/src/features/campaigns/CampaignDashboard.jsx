import { useEffect, useMemo, useRef, useState } from 'react'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import { createCampaignApi, validateSignedVideoUrl, P0249_NODE_PREVIEW_ORIGIN } from './campaign-api.mjs'
import sampleCampaign from './fixtures/sample-campaign.json'
import {
  buildCampaignRequest, cloneCampaign, formatDayDate, linkedInText,
  serializeDraftDay, timelineErrors, updateCampaignDay, updateScene, withAuthorizedMedia,
} from './campaign-model.mjs'
import PosterStudio from '../creative/PosterStudio.jsx'
import Feature3PosterHost from '../creative/Feature3PosterHost.jsx'
import './CampaignDashboard.css'

const INITIAL_BRIEF = 'Create seven days of helpful style inspiration for my clothing boutique, with LinkedIn posts and Instagram Reel concepts.'
const MOCK_NOTICE = 'Demo only · Sample drafts and synthetic asset IDs. No AI, saving, rendering or publishing is connected.'
const GENERATION_MODE = import.meta.env?.VITE_CAMPAIGN_GENERATION_MODE === 'foundry' ? 'foundry' : 'mock'
function recentCampaignKey(userId, shopId) {
  return 'retailgrowthai-last-campaign:' + userId + ':' + shopId
}
function isCampaignId(value) {
  return typeof value === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value)
}

function saveLocalFile(filename, contents, mimeType) {
  const url = URL.createObjectURL(new Blob([contents], { type: mimeType }))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}

function CampaignPrompt({ campaign, onRequest, live = false, liveShopId = '', liveAssetIds = [] }) {
  const [brief, setBrief] = useState(INITIAL_BRIEF)
  const [startDate, setStartDate] = useState(campaign.days[0].scheduled_date)
  const [offer, setOffer] = useState('')
  const [expiry, setExpiry] = useState('')
  const [error, setError] = useState('')
  const [showRequest, setShowRequest] = useState(false)
  const [request, setRequest] = useState(null)

  function submit(event) {
    event.preventDefault()
    try {
      const sampleRequest = buildCampaignRequest({
        brief, start_date: startDate, offer_description: offer,
        offer_valid_until: expiry,
      }, campaign)
      const next = live
        ? withAuthorizedMedia(sampleRequest, liveShopId, liveAssetIds)
        : sampleRequest
      setRequest(next)
      setError('')
      setShowRequest(true)
      onRequest(next)
    } catch (problem) {
      setError(problem.message)
      setShowRequest(false)
    }
  }

  return (
    <section className="rg-panel rg-brief" aria-labelledby="rg-brief-title">
      <div className="rg-section-head">
        <div>
          <span className="rg-kicker">01 / THE CREATIVE BRIEF</span>
          <h2 id="rg-brief-title">What should we create?</h2>
          <p>{live ? 'Submit an authorized seven-day planning job with selected business media.' : 'Build a local API request preview before any AI connection.'}</p>
        </div>
        <span className="rg-mini-pill">7-day plan</span>
      </div>
      <form onSubmit={submit} className="rg-brief-form">
        <label className="rg-field rg-wide" htmlFor="rg-prompt">
          <span>Campaign instructions</span>
          <textarea id="rg-prompt" value={brief} onChange={event => setBrief(event.target.value)}
            minLength={10} maxLength={2000} rows={3} required
            placeholder="e.g. Plan seven days of summer looks using my approved products..." />
          <small>{brief.length}/2000 characters · {live ? 'Authenticated API when submitted' : 'No AI request is sent'}</small>
        </label>
        <label className="rg-field" htmlFor="rg-start">
          <span>Start date</span>
          <input id="rg-start" type="date" value={startDate} onChange={event => setStartDate(event.target.value)} required />
        </label>
        <label className="rg-field" htmlFor="rg-offer">
          <span>Offer (optional)</span>
          <input id="rg-offer" value={offer} onChange={event => setOffer(event.target.value)}
            placeholder="Only enter real, approved offers" />
        </label>
        <label className="rg-field" htmlFor="rg-expiry">
          <span>Offer ends (if specified)</span>
          <input id="rg-expiry" type="date" value={expiry} onChange={event => setExpiry(event.target.value)} />
        </label>
        <div className="rg-prompt-actions">
          <div className="rg-platforms" aria-label="Planned channels">
            <span>LinkedIn</span><span>Instagram Reels</span>
          </div>
          <button className="rg-button rg-primary" type="submit">{live ? 'Submit campaign job' : 'Preview campaign request'} <span aria-hidden="true">→</span></button>
        </div>
      </form>
      {error && <p className="rg-validation" role="alert">{error}</p>}
      {showRequest && request && (
        <div className="rg-request-preview" aria-live="polite">
          <div className="rg-inline-title">
            <strong>Contract v1 request · {live ? 'submitted for authorization' : 'local preview only'}</strong>
            <button type="button" className="rg-button rg-quiet"
              onClick={() => saveLocalFile('campaign-request.json', JSON.stringify(request, null, 2) + '\n', 'application/json')}>
              Export request JSON
            </button>
          </div>
          <p>{live ? 'A backend job must report DRAFT before new content replaces these samples.' : 'No campaign was generated; the seven sample days below are unchanged.'}</p>
          <pre>{JSON.stringify(request, null, 2)}</pre>
        </div>
      )}
    </section>
  )
}

function Calendar({ days, selectedId, onSelect, live = false }) {
  return (
    <section className="rg-calendar-section" aria-labelledby="rg-calendar-title">
      <div className="rg-inline-title rg-calendar-heading">
        <div>
          <span className="rg-kicker">02 / CONTENT CALENDAR</span>
          <h2 id="rg-calendar-title">Your week, at a glance</h2>
        </div>
        <span className="rg-subtle">{live ? 'Authorized drafts · not published' : '7 sample days · not scheduled'}</span>
      </div>
      <div className="rg-calendar" aria-label="Choose a campaign day">
        {days.map(day => (
          <button type="button" key={day.id} onClick={() => onSelect(day.id)}
            className={'rg-calendar-day' + (selectedId === day.id ? ' is-selected' : '')}
            aria-pressed={selectedId === day.id} aria-label={'Day ' + day.day_index + ': ' + day.topic}>
            <span className="rg-calendar-index">DAY {String(day.day_index).padStart(2, '0')}</span>
            <strong>{formatDayDate(day.scheduled_date)}</strong>
            <span className="rg-calendar-topic">{day.topic}</span>
            <span className="rg-calendar-status"><i aria-hidden="true" />Draft preview</span>
          </button>
        ))}
      </div>
    </section>
  )
}

function LinkedInEditor({ day, onChange }) {
  const [copied, setCopied] = useState(false)
  async function copy() {
    if (!navigator.clipboard?.writeText) return
    try {
      await navigator.clipboard.writeText(linkedInText(day))
      setCopied(true)
    } catch {
      setCopied(false)
    }
  }
  const wordCount = day.linkedin.post_text.trim().split(/\s+/).filter(Boolean).length
  return (
    <div className="rg-editor-pane" aria-label="LinkedIn content editor">
      <div className="rg-input-meta"><span>LINKEDIN POST · EDITABLE DRAFT</span><span>{wordCount} words</span></div>
      <label className="rg-field" htmlFor="rg-linkedin-copy">
        <span>Post body</span>
        <textarea id="rg-linkedin-copy" rows={8} value={day.linkedin.post_text}
          onChange={event => onChange(current => ({
            ...current, linkedin: { ...current.linkedin, post_text: event.target.value },
          }))} />
      </label>
      <label className="rg-field" htmlFor="rg-tags">
        <span>Hashtags (comma separated)</span>
        <input id="rg-tags" value={day.linkedin.hashtags.join(', ')}
          onChange={event => onChange(current => ({
            ...current, linkedin: { ...current.linkedin,
              hashtags: event.target.value.split(',').map(tag => tag.trim()).filter(Boolean).map(tag => tag.startsWith('#') ? tag : '#' + tag),
            },
          }))} />
      </label>
      <div className="rg-editor-actions">
        <button className="rg-button rg-secondary" type="button" onClick={() => saveLocalFile(
          'day-' + day.day_index + '-linkedin.txt', linkedInText(day), 'text/plain;charset=utf-8'
        )}>Download post .txt</button>
        <button className="rg-button rg-quiet" type="button" onClick={copy}>{copied ? 'Copied' : 'Copy text'}</button>
      </div>
    </div>
  )
}

function ReelPreview({ day }) {
  return (
    <div className="rg-preview-pane">
      <div className="rg-phone-wrap">
        <div className="rg-phone" role="img" aria-label="Illustrative Instagram Reel layout. No images or video have been rendered.">
          <div className="rg-phone-top"><span>▰▰</span><span>REEL CONCEPT</span><span>⋮</span></div>
          <div className="rg-phone-graphic"><span className="rg-orbit rg-orbit-one"/><span className="rg-orbit rg-orbit-two"/></div>
          <div className="rg-phone-center">
            <small>DAY {String(day.day_index).padStart(2, '0')} / 07</small>
            <strong>{day.instagram.reel.storyboard[1]?.overlay_text || day.topic}</strong>
            <em>{day.instagram.reel.cta}</em>
          </div>
          <div className="rg-phone-bottom"><span>@your_brand · illustrative mock</span><span>♡  ◻  ↗</span></div>
        </div>
        <div className="rg-video-caption">9:16 concept frame · no actual media</div>
      </div>
      <div className="rg-field">
        <span>Instagram caption</span>
        <p className="rg-caption-preview">{day.instagram.caption}</p>
      </div>
    </div>
  )
}

function StoryboardEditor({ day, onChange }) {
  const scenes = day.instagram.reel.storyboard
  const errors = useMemo(() => timelineErrors(scenes), [scenes])
  const duration = scenes.reduce((total, scene) => total + (Number.isFinite(scene.duration_seconds) ? scene.duration_seconds : 0), 0)
  function changeScene(index, field, value) {
    onChange(current => ({
      ...current,
      instagram: {
        ...current.instagram,
        reel: {
          ...current.instagram.reel,
          storyboard: updateScene(current.instagram.reel.storyboard, index, field, value),
        },
      },
    }))
  }
  return (
    <section className="rg-storyboard" aria-labelledby="rg-storyboard-title">
      <div className="rg-inline-title">
        <div><span className="rg-kicker">03 / REEL STORYBOARD</span><h3 id="rg-storyboard-title">Frame by frame</h3></div>
        <span className={'rg-timing' + (errors.length ? ' rg-timing-bad' : '')}>{duration}s / 30s</span>
      </div>
      <p className="rg-subtle">Edit scene text and duration. Starts are recalculated automatically; synthetic asset IDs remain read-only.</p>
      <div className="rg-scene-list">
        {scenes.map((scene, index) => (
          <div className="rg-scene" key={scene.asset_id + '-' + index}>
            <div className="rg-scene-number">0{index + 1}</div>
            <div className="rg-scene-body">
              <label className="rg-field" htmlFor={'rg-scene-text-' + index}>
                <span>Overlay text</span>
                <input id={'rg-scene-text-' + index} value={scene.overlay_text}
                  onChange={event => changeScene(index, 'overlay_text', event.target.value)} />
              </label>
              <span className="rg-asset-id" title={scene.asset_id}>Sample asset · {scene.asset_id.slice(0, 8)}…</span>
            </div>
            <label className="rg-field rg-duration" htmlFor={'rg-scene-time-' + index}>
              <span>Seconds</span>
              <input id={'rg-scene-time-' + index} type="number" min="1" max="30" step="1"
                value={scene.duration_seconds} onChange={event => changeScene(index, 'duration_seconds', event.target.value)} />
              <small>Starts {scene.start_seconds}s</small>
            </label>
          </div>
        ))}
      </div>
      {errors.length > 0 && <div className="rg-validation" role="alert">{errors.map(error => <p key={error}>{error}</p>)}</div>}
      {errors.length === 0 && <div className="rg-valid-timeline">✓ Continuous 30-second timeline (metadata only)</div>}
    </section>
  )
}

function RenderStatus({ day, valid, live, dirty, job, onRender, onDownload }) {
  return (
    <section className="rg-render" aria-labelledby="rg-render-title">
      <div className="rg-inline-title">
        <div><span className="rg-kicker">04 / RENDER & EXPORT</span><h3 id="rg-render-title">Production queue</h3></div>
        <span className="rg-status-pill">{job?.status || 'Not queued'}</span>
      </div>
      <p>{live ? 'Render only the saved, authorized draft. Unsaved browser edits are not sent.' : 'Video rendering is not connected. No render job ID or MP4 exists for this sample.'}</p>
      <div className="rg-render-actions">
        <button type="button" className="rg-button rg-secondary" disabled={!live || !valid || dirty || (job && !['FAILED', 'SUCCEEDED'].includes(job.status))} onClick={onRender}>{live ? 'Render saved Reel' : 'Render Reel · unavailable'}</button>
        <button type="button" className="rg-button rg-secondary" disabled={!live || job?.status !== 'SUCCEEDED'} onClick={onDownload}>Download signed MP4</button>
        <button type="button" className="rg-button rg-quiet" disabled={!valid}
          onClick={() => saveLocalFile('day-' + day.day_index + '-draft.json', serializeDraftDay(day), 'application/json')}>
          Export day JSON
        </button>
      </div>
      <span className="rg-subtle">JSON export includes edited storyboard metadata, not any media file.</span>
    </section>
  )
}

function LiveMediaSelection({ shops, shopId, onShop, assets, assetIds, onAssets, error }) {
  return (
    <section className="rg-panel" aria-label="Authorized business and media">
      <div className="rg-inline-title">
        <div><span className="rg-kicker">SECURE WORKSPACE</span><h2>Business and registered media</h2></div>
        <span className="rg-status-pill">Signed-in account</span>
      </div>
      <label className="rg-field" htmlFor="rg-shop">
        <span>Business</span>
        <select id="rg-shop" value={shopId} onChange={event => onShop(event.target.value)}>
          <option value="">Select your business</option>
          {shops.map(shop => <option key={shop.id} value={shop.id}>{shop.name} · {shop.membership.role}</option>)}
        </select>
      </label>
      <div className="rg-media-list" aria-label="Approved media assets">
        {assets.length === 0 ? <p>No images registered for this shop. Upload a private, rights-declared image first.</p> :
          assets.map(asset => <label key={asset.id}>
            <input type="checkbox" checked={assetIds.includes(asset.id)}
              onChange={event => onAssets(event.target.checked
                ? [...assetIds, asset.id].slice(0, 21)
                : assetIds.filter(id => id !== asset.id))} />
            <span>{asset.mime_type} · {asset.license_name} · {asset.id.slice(0, 8)}…</span>
          </label>)}
      </div>
      <p className="rg-subtle">Use 1–21 registered tenant-owned assets. Rights evidence is self-declared until reviewed. Synthetic IDs are never submitted.</p>
      {error && <p className="rg-validation" role="alert">{error}</p>}
    </section>
  )
}

function LiveImageUploader({ client, shopId, onUploaded }) {
  const [file, setFile] = useState(null)
  const [licenseName, setLicenseName] = useState('owned')
  const [licenseUrl, setLicenseUrl] = useState('')
  const [attribution, setAttribution] = useState('')
  const [confirmedRights, setConfirmedRights] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')
  const [uploadError, setUploadError] = useState('')
  const active = useRef(true)
  useEffect(() => {
    active.current = true
    return () => { active.current = false }
  }, [])

  async function submit(event) {
    event.preventDefault()
    if (!file || uploading || !confirmedRights) return
    setUploading(true)
    setUploadError('')
    setMessage('')
    try {
      const asset = await client.uploadImageAsset(shopId, {
        file, licenseName, licenseUrl, attribution, confirmedRights,
      })
      if (!active.current) return
      onUploaded(asset)
      setFile(null)
      setMessage('Image stored privately and registered. Rights declarations require review before publishing.')
      setConfirmedRights(false)
    } catch (error) {
      if (active.current) setUploadError(error.message)
    } finally {
      if (active.current) setUploading(false)
    }
  }

  return (
    <form className="rg-panel" onSubmit={submit} aria-label="Upload private campaign image">
      <div className="rg-inline-title">
        <div><span className="rg-kicker">REAL MEDIA / PRIVATE STORAGE</span>
          <h2>Upload your product image</h2></div>
      </div>
      <label className="rg-field" htmlFor="rg-private-photo"><span>PNG, JPEG or WebP · max 25 MB</span>
        <input id="rg-private-photo" type="file" accept="image/png,image/jpeg,image/webp"
          onChange={event => setFile(event.target.files?.[0] || null)} />
      </label>
      <label className="rg-field" htmlFor="rg-license-type"><span>Commercial use rights</span>
        <select id="rg-license-type" value={licenseName} onChange={event => setLicenseName(event.target.value)}>
          <option value="owned">I own the image</option>
          <option value="cc0">CC0 / public domain</option>
          <option value="royalty_free">Licensed royalty-free</option>
          <option value="commercial">Commercial license</option>
        </select>
      </label>
      {licenseName !== 'owned' && <label className="rg-field" htmlFor="rg-license-url">
        <span>HTTPS license evidence link</span>
        <input id="rg-license-url" type="url" value={licenseUrl} required
          placeholder="https://provider.example/license" onChange={event => setLicenseUrl(event.target.value)} />
      </label>}
      <label className="rg-field" htmlFor="rg-media-evidence">
        <span>Source and ownership evidence / attribution</span>
        <textarea id="rg-media-evidence" rows={2} value={attribution}
          onChange={event => setAttribution(event.target.value)}
          placeholder="Example: Original product photo created by our team" required />
      </label>
      <label className="rg-field">
        <span><input type="checkbox" checked={confirmedRights}
          onChange={event => setConfirmedRights(event.target.checked)} />
          I confirm I have commercial rights to use this image</span>
      </label>
      <button className="rg-button rg-secondary" type="submit"
        disabled={uploading || !file || !confirmedRights}>
        {uploading ? 'Uploading privately…' : 'Upload image'}
      </button>
      {message && <p role="status">{message}</p>}
      {uploadError && <p className="rg-validation" role="alert">{uploadError}</p>}
      <p className="rg-subtle">Evidence is user-declared, not independently verified. Never upload media you lack rights to use.</p>
    </form>
  )
}

export default function CampaignDashboard() {
  const { user, client } = useRetailAuth()
  // OFF unless this frontend build is deliberately deployed into the exact
  // isolated DEV named-preview origin. The normal customer site stays on Python.
  const nodePreview = import.meta.env?.VITE_P0249_NODE_TRANSPORT_ENABLED === 'true'
  const api = useMemo(() => createCampaignApi({
    baseUrl: nodePreview ? P0249_NODE_PREVIEW_ORIGIN :
      (import.meta.env?.VITE_CAMPAIGN_API_BASE_URL || ''),
    transport: nodePreview ? 'node-preview' : 'python',
    browserOrigin: typeof window === 'undefined' ? '' : window.location.origin,
    tokenProvider: () => client.getAccessToken(),
    supabaseOrigin: import.meta.env?.VITE_SUPABASE_URL || '',
    supabasePublishableKey: import.meta.env?.VITE_SUPABASE_PUBLISHABLE_KEY || '',
  }), [client, nodePreview])
  const [shops, setShops] = useState([])
  const [shopId, setShopId] = useState('')
  const [assets, setAssets] = useState([])
  const [assetIds, setAssetIds] = useState([])
  const [liveError, setLiveError] = useState('')
  const [campaignId, setCampaignId] = useState('')
  const [campaignStatus, setCampaignStatus] = useState('')
  const [baseline, setBaseline] = useState(() => cloneCampaign(sampleCampaign))
  const [renderJob, setRenderJob] = useState(null)
  const [savingDay, setSavingDay] = useState(false)
  const live = Boolean(api && user && client.configured && shopId)
  const loaded = live && campaignId && campaignStatus === 'DRAFT'
  const [campaign, setCampaign] = useState(() => cloneCampaign(sampleCampaign))
  const [selectedId, setSelectedId] = useState(sampleCampaign.days[0].id)
  const [tab, setTab] = useState('linkedin')
  const [notice, setNotice] = useState('')
  const day = campaign.days.find(entry => entry.id === selectedId) || campaign.days[0]
  const storyErrors = timelineErrors(day.instagram.reel.storyboard)
  const original = baseline.days.find(entry => entry.id === day.id) || day
  const changed = JSON.stringify(original) !== JSON.stringify(day)

  useEffect(() => {
    let cancelled = false
    if (!api || !user || !client.configured) {
      setShops([]); setShopId(''); setAssets([]); setAssetIds([])
      setCampaignId(''); setCampaignStatus('')
      return () => { cancelled = true }
    }
    client.listShops().then(items => {
      if (cancelled) return
      setShops(items.filter(item => ['OWNER', 'EDITOR'].includes(item.membership?.role)))
    }).catch(error => { if (!cancelled) setLiveError(error.message) })
    return () => { cancelled = true }
  }, [api, user, client])

  useEffect(() => {
    let cancelled = false
    setAssets([]); setAssetIds([])
    setCampaignId(''); setCampaignStatus(''); setRenderJob(null)
    setCampaign(cloneCampaign(sampleCampaign)); setBaseline(cloneCampaign(sampleCampaign))
    if (shopId && user && api) {
      client.listMediaAssets(shopId).then(list => {
        if (!cancelled) setAssets(list)
      }).catch(error => { if (!cancelled) setLiveError(error.message) })
      // Store only a per-user, per-shop UUID hint. The backend ALWAYS rechecks
      // JWT, membership and returned tenant before showing any remote content.
      const saved = window.sessionStorage.getItem(recentCampaignKey(user.id, shopId))
      if (isCampaignId(saved)) {
        api.getCampaign(saved).then(result => {
          if (cancelled || result.shop_id !== shopId || result.id !== saved) return
          if (result.status === 'DRAFT' && Array.isArray(result.days) && result.days.length) {
            setBaseline(cloneCampaign(result))
            setCampaign(cloneCampaign(result))
            setSelectedId(result.days[0].id)
          }
          if (['DRAFT', 'PLANNING', 'FAILED'].includes(result.status)) {
            setCampaignId(saved)
            setCampaignStatus(result.status)
          }
        }).catch(error => {
          window.sessionStorage.removeItem(recentCampaignKey(user.id, shopId))
          if (!cancelled && error.status === 401) setLiveError(error.message)
        })
      }
    }
    return () => { cancelled = true }
  }, [shopId, user, client, api])

  useEffect(() => {
    if (!campaignId || !live || campaignStatus !== 'PLANNING') return
    let cancelled = false
    async function poll() {
      try {
        const result = await api.getCampaign(campaignId)
        if (cancelled) return
        if (result.shop_id !== shopId) throw new Error('Campaign tenant mismatch')
        setCampaignStatus(result.status)
        if (result.status === 'DRAFT' && Array.isArray(result.days) && result.days.length > 0) {
          setBaseline(cloneCampaign(result))
          setCampaign(cloneCampaign(result))
          setSelectedId(result.days[0].id)
          setNotice('Authenticated campaign draft loaded. Publishing is still unavailable.')
        }
        if (result.status === 'FAILED') setNotice('Campaign planning failed. No draft was generated.')
      } catch (error) { if (!cancelled) setLiveError(error.message) }
    }
    poll()
    const timer = window.setInterval(poll, 5000)
    return () => { cancelled = true; window.clearInterval(timer) }
  }, [api, live, campaignId, campaignStatus, shopId])

  useEffect(() => {
    if (!live || !renderJob?.job_id || !['QUEUED', 'RUNNING'].includes(renderJob.status)) return
    let cancelled = false
    async function poll() {
      try {
        const job = await api.getRenderJob(renderJob.job_id)
        if (!cancelled) setRenderJob(job)
      } catch (error) { if (!cancelled) setLiveError(error.message) }
    }
    const timer = window.setInterval(poll, 5000)
    return () => { cancelled = true; window.clearInterval(timer) }
  }, [api, live, renderJob?.job_id, renderJob?.status])

  async function submitLive(request) {
    if (!live) {
      setNotice('API request preview built locally; sample content is unchanged.')
      return
    }
    if (assetIds.length < 1 || assetIds.length > 21) {
      setLiveError('Select 1–21 licensed assets before submitting.')
      return
    }
    setLiveError('')
    try {
      const accepted = await api.createCampaign(request)
      if (accepted.status !== 'PLANNING') throw new Error('Campaign was not queued')
      if (!isCampaignId(accepted.campaign_id)) throw new Error('Invalid campaign receipt')
      window.sessionStorage.setItem(recentCampaignKey(user.id, shopId), accepted.campaign_id)
      setCampaignId(accepted.campaign_id)
      setCampaignStatus('PLANNING')
      setNotice('Campaign queued. Waiting for an authorized draft.')
    } catch (error) { setLiveError(error.message) }
  }

  async function saveDay() {
    if (!loaded || !changed || storyErrors.length || savingDay) return
    const snapshot = cloneCampaign(day)
    const currentCampaignId = campaignId
    const snapshotShopId = shopId
    setSavingDay(true)
    setLiveError('')
    try {
      const response = await api.saveDay(currentCampaignId, snapshot.id, snapshot)
      const saved = response?.day
      if (!saved || saved.id !== snapshot.id ||
          saved.campaign_id !== currentCampaignId || saved.shop_id !== snapshotShopId) {
        throw new Error('Saved draft identity mismatch')
      }
      setBaseline(current => current.id === currentCampaignId
        ? updateCampaignDay(current, snapshot.id, () => saved) : current)
      setCampaign(current => {
        if (current.id !== currentCampaignId) return current
        const latest = current.days.find(item => item.id === snapshot.id)
        return updateCampaignDay(current, snapshot.id, () =>
          JSON.stringify(latest) === JSON.stringify(snapshot) ? saved : latest)
      })
      setRenderJob(null)
      setNotice('Draft day saved to your secure workspace.')
    } catch (error) {
      setLiveError(error.status === 409
        ? 'Draft changed or rendering is active. Reload before trying again.'
        : error.message)
    } finally {
      setSavingDay(false)
    }
  }

  async function startRender() {
    if (!loaded || changed || storyErrors.length || savingDay) return
    setLiveError('')
    try {
      const job = await api.createRender(campaignId, day.id)
      setRenderJob(job)
      setNotice('Render request accepted. Waiting for job status.')
    } catch (error) { setLiveError(error.message) }
  }

  async function downloadRender() {
    if (!loaded || renderJob?.status !== 'SUCCEEDED') return
    try {
      const reply = await api.getDownload(renderJob.job_id)
      const link = validateSignedVideoUrl(reply.url, import.meta.env.VITE_SUPABASE_URL)
      const anchor = document.createElement('a')
      anchor.href = link
      anchor.rel = 'noopener noreferrer'
      anchor.target = '_blank'
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
    } catch (error) { setLiveError(error.message) }
  }

  function editDay(transform) {
    setCampaign(current => updateCampaignDay(current, day.id, transform))
    setNotice('Edits are unsaved. Save this day before rendering.')
  }
  function restoreDay() {
    setCampaign(current => updateCampaignDay(current, day.id, () => cloneCampaign(original)))
    setNotice((loaded ? 'Saved' : 'Sample') + ' draft restored for day ' + day.day_index + '.')
  }

  return (
    <div className="rg-dashboard">
      <div className="rg-hero">
        <div><span className="rg-kicker">RETAILGROWTHAI / CAMPAIGN STUDIO</span>
          <h1>Make every day <span>worth sharing.</span></h1>
          <p>From a simple idea to a seven-day content plan. Shape your story across LinkedIn and Instagram.</p>
          <span className="rg-demo-notice" role="status">{loaded
            ? (GENERATION_MODE === 'foundry'
              ? 'Authenticated draft · Foundry integration configured · Human review required; not published.'
              : 'Authenticated DEV mock draft · Not AI-generated, scheduled or published.')
            : MOCK_NOTICE}</span>
        </div>
        <div className="rg-hero-art" aria-hidden="true"><span>01</span><span>PLAN / CREATE / REVIEW</span><b>↗</b></div>
      </div>
      <div className="rg-stats" aria-label="Campaign summary">
        <div><strong>07</strong><span>Draft campaign days</span></div>
        <div><strong>14</strong><span>Channel draft concepts</span></div>
        <div><strong>30<span>s</span></strong><span>Reel storyboard target</span></div>
        <div><strong>{renderJob?.status === 'SUCCEEDED' ? '1' : '0'}</strong><span>Verified render jobs completed</span></div>
      </div>
      {api && user && client.configured &&
        <LiveMediaSelection shops={shops} shopId={shopId} onShop={(id) => { setShopId(id); setLiveError('') }}
          assets={assets} assetIds={assetIds} onAssets={setAssetIds} error={liveError} />}
      {live && <LiveImageUploader key={shopId} client={client} shopId={shopId}
        onUploaded={asset => {
          setAssets(current => [asset, ...current.filter(item => item.id !== asset.id)])
          setAssetIds(current => current.includes(asset.id) || current.length >= 21
            ? current : [...current, asset.id])
        }} />}
      <CampaignPrompt key={shopId || 'demo'} campaign={campaign} live={live}
        liveShopId={shopId} liveAssetIds={assetIds} onRequest={submitLive} />
      {live && <p role="status" className="rg-subtle">{GENERATION_MODE === 'foundry'
        ? 'Azure Foundry inference configured for deployment; confirm runtime settings before treating new drafts as model-generated.'
        : 'DEV planning mode: explicitly labeled mock generator. These are not AI-written posts.'}</p>}
      {live && campaignStatus === 'PLANNING' && <p role="status">Campaign planning in progress. No new draft is available yet.</p>}
      {live && campaignStatus === 'FAILED' && <p className="rg-validation" role="alert">Campaign planning failed. Check the worker and model configuration; no draft was saved.</p>}
      {api && !user && client.configured && <p className="rg-validation" role="status">Sign in on Account to load your businesses and begin real campaign creation. The sample below is demo only.</p>}
      {renderJob?.status === 'FAILED' && <p className="rg-validation" role="alert">Render failed ({renderJob.error_code || 'unknown reason'}). Retry only after checking media rights and the saved storyboard.</p>}
      <Calendar days={campaign.days} live={loaded} selectedId={day.id} onSelect={(id) => { setSelectedId(id); setRenderJob(null); setNotice('') }} />
      <section className="rg-editor rg-panel" aria-labelledby="rg-editor-title">
        <div className="rg-inline-title rg-editor-heading">
          <div><span className="rg-kicker">CONTENT WORKSPACE / DAY {String(day.day_index).padStart(2, '0')}</span>
            <h2 id="rg-editor-title">Refine your draft</h2><p>{formatDayDate(day.scheduled_date)} · {loaded ? 'Authenticated draft · save changes before rendering' : 'Local sample campaign'}</p>
          </div>
          <div className="rg-editor-actions">
            {changed && <span className="rg-changed">Unsaved changes</span>}
            {loaded && <button className="rg-button rg-secondary" type="button"
              disabled={!changed || storyErrors.length > 0 || savingDay}
              onClick={saveDay}>{savingDay ? 'Saving…' : 'Save day'}</button>}
            <button className="rg-button rg-quiet" type="button" disabled={savingDay}
              onClick={restoreDay}>Reset day</button>
          </div>
        </div>
        <label className="rg-field rg-topic" htmlFor="rg-topic">
          <span>Content topic</span>
          <input id="rg-topic" value={day.topic} onChange={event => editDay(current => ({ ...current, topic: event.target.value }))} />
        </label>
        <div className="rg-tab-bar" role="group" aria-label="Content editor section">
          <button type="button" className={tab === 'linkedin' ? 'rg-tab is-active' : 'rg-tab'}
            aria-pressed={tab === 'linkedin'} onClick={() => setTab('linkedin')}>LinkedIn post</button>
          <button type="button" className={tab === 'instagram' ? 'rg-tab is-active' : 'rg-tab'}
            aria-pressed={tab === 'instagram'} onClick={() => setTab('instagram')}>Instagram concept</button>
        </div>
        {tab === 'linkedin'
          ? <div className="rg-editor-content rg-linkedin-layout">
              <LinkedInEditor key={day.id} day={day} onChange={editDay} />
              <div className="rg-linkedin-preview">
                <div className="rg-social-profile"><div>R</div><span><strong>Your business</strong><small>Post preview · not published</small></span><b>•••</b></div>
                <p>{day.linkedin.post_text}</p>
                <div className="rg-hashtag-preview">{day.linkedin.hashtags.join(' ')}</div>
                <div className="rg-social-footer">Like <span>Comment</span> Repost <span>Send</span></div>
              </div>
            </div>
          : <div className="rg-editor-content rg-instagram-layout">
              <div className="rg-instagram-controls">
                <label className="rg-field" htmlFor="rg-caption"><span>Instagram caption</span>
                  <textarea id="rg-caption" rows={5} value={day.instagram.caption}
                    onChange={event => editDay(current => ({
                      ...current, instagram: { ...current.instagram, caption: event.target.value },
                    }))} /></label>
                <label className="rg-field" htmlFor="rg-cta"><span>Reel call-to-action</span>
                  <input id="rg-cta" value={day.instagram.reel.cta} onChange={event => editDay(current => ({
                    ...current, instagram: { ...current.instagram, reel: { ...current.instagram.reel, cta: event.target.value } },
                  }))} /></label>
                <StoryboardEditor day={day} onChange={editDay} />
              </div>
              <ReelPreview day={day} />
            </div>}
        <RenderStatus day={day} valid={storyErrors.length === 0} live={loaded} dirty={changed || savingDay}
          job={renderJob} onRender={startRender} onDownload={downloadRender} />
      </section>
      {(!client.configured || (shopId && shops.some(shop => shop.id === shopId))) && (
        <Feature3PosterHost client={client} shopId={shopId}>
        <PosterStudio key={shopId || 'demo'} day={day}
          businessName={shops.find(shop => shop.id === shopId)?.name || 'Your business'}
          api={api} campaignId={campaignId} authorizedAssets={assets}
          persisted={Boolean(loaded && !changed && !savingDay)}
          supabaseOrigin={import.meta.env?.VITE_SUPABASE_URL || ''}
          onSelected={async () => {
            if (!loaded || !api) return
            const refreshed = await api.getCampaign(campaignId)
            if (refreshed.shop_id !== shopId) throw new Error('Campaign tenant mismatch')
            setBaseline(cloneCampaign(refreshed))
            setCampaign(cloneCampaign(refreshed))
            setNotice('Reviewed promotional poster attached to your saved day. Not published.')
          }} />
        </Feature3PosterHost>
      )}
      {notice && <p className="rg-session-notice" role="status">{notice}</p>}
      <p className="rg-footnote">{loaded
        ? 'Live drafts and private image uploads use authenticated APIs. Publishing and independent rights verification remain unavailable.'
        : 'Sample data only. No remote save, uploads, model output or published media is implied.'}</p>
    </div>
  )
}
