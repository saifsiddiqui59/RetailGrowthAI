import { useState } from 'react'
import { DEFAULT_VIDEO_ENGINE, premiumVideoChoices, PREMIUM_VIDEO_STATUS,
         validatePremiumRequest } from './premium-video-model.mjs'

/**
 * Part 3 additive UI. Never posts to a provider or to a billing API.
 * In Part 1 this panel is intentionally not mounted. When Part 3 reaches the
 * final coordinator, mount beside the FFmpeg button and pass server-verified
 * entitlement AND backend capability as separate values.
 */
export default function PremiumVideoPanel({
  dayId, authorizedImageIds = [], entitlement = false,
  endpointReady = false, featureEnabled = false, onCreate,
}) {
  const [engine, setEngine] = useState(DEFAULT_VIDEO_ENGINE)
  const [mode, setMode] = useState('text')
  const [duration, setDuration] = useState(5)
  const [resolution, setResolution] = useState('720P')
  const [assetId, setAssetId] = useState('')
  const [status, setStatus] = useState('')
  const [pending, setPending] = useState(false)
  const options = premiumVideoChoices({ entitlement, endpointReady, featureEnabled })
  const canUsePremium = options[1].available && typeof onCreate === 'function'

  async function requestPremium() {
    if (!canUsePremium || pending) return
    setPending(true)
    setStatus('')
    try {
      const body = validatePremiumRequest({
        day_id: dayId, mode, resolution, duration_seconds: duration,
        input_asset_id: mode === 'image' ? assetId : null,
      }, { entitlement, endpointReady, featureEnabled })
      const job = await onCreate(body)
      if (!job || typeof job.job_id !== 'string' || job.status !== 'QUEUED') {
        throw new Error('Premium video was not confirmed by the backend')
      }
      setStatus('Premium job queued. Credits are reserved by the server, not the browser.')
    } catch (err) {
      setStatus(err?.message || 'Premium request could not be accepted')
    } finally {
      setPending(false)
    }
  }

  return (
    <section aria-label="Video generator selection" className="rg-panel" data-premium-status={PREMIUM_VIDEO_STATUS}>
      <h3>Choose your video generator</h3>
      <p>Standard FFmpeg rendering remains the default and uses your existing render quota.</p>
      <fieldset>
        <legend>Video engine</legend>
        {options.map(item => (
          <label key={item.id} style={{ display: 'block', marginBottom: '.6rem' }}>
            <input type="radio" name="rg-video-engine" value={item.id}
              checked={engine === item.id} disabled={!item.available || (item.id === 'wan' && !canUsePremium)}
              onChange={() => setEngine(item.id)} />
            <strong> {item.label}</strong>
            <small style={{ display: 'block' }}>{item.cost}</small>
          </label>
        ))}
      </fieldset>
      {!canUsePremium && (
        <p role="status">Premium Wan videos are not active. Provider approval, private media import, and server-controlled credits are required. You can still generate standard FFmpeg Reels above.</p>
      )}
      {engine === 'wan' && canUsePremium && <>
        <label>Generation source
          <select value={mode} onChange={event => setMode(event.target.value)}>
            <option value="text">Text-to-video</option>
            <option value="image">Animate an approved business image</option>
          </select>
        </label>
        {mode === 'image' && <label>Approved source image
          <select value={assetId} onChange={event => setAssetId(event.target.value)}>
            <option value="">Choose an authorized image</option>
            {authorizedImageIds.map(id => <option key={id} value={id}>{id.slice(0, 8)}…</option>)}
          </select>
        </label>}
        <label>Duration
          <select value={duration} onChange={event => setDuration(Number(event.target.value))}>
            {[5,10,15].map(seconds => <option key={seconds} value={seconds}>{seconds} seconds</option>)}
          </select>
        </label>
        <label>Resolution
          <select value={resolution} onChange={event => setResolution(event.target.value)}>
            <option value="720P">720p</option>
            <option value="1080P">1080p</option>
          </select>
        </label>
        <p>Final premium credit estimate and permission must be confirmed by the server before submitting. Content may be transferred to an approved external provider.</p>
        <button type="button" disabled={pending} onClick={requestPremium}>
          {pending ? 'Submitting…' : 'Request premium AI video'}
        </button>
      </>}
      {status && <p role="status">{status}</p>}
    </section>
  )
}
