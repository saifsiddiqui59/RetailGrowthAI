import { useState } from 'react'
import { SOCIAL_PUBLISHING_SAMPLES } from './social-publishing-samples.mjs'
import './SocialSampleGallery.css'

/**
 * A view-only publisher preview. No backend API, campaign mutation or provider
 * SDK is imported here. These examples can be inspected without an account.
 */
export function SocialSampleGallery() {
  const [sampleId, setSampleId] = useState(SOCIAL_PUBLISHING_SAMPLES[0].id)
  const [copied, setCopied] = useState(false)
  const sample = SOCIAL_PUBLISHING_SAMPLES.find(item => item.id === sampleId)
    || SOCIAL_PUBLISHING_SAMPLES[0]

  async function copyText() {
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Unavailable')
      await navigator.clipboard.writeText(sample.copy)
      setCopied(true)
    } catch {
      setCopied(false)
    }
  }

  function select(id) {
    setSampleId(id)
    setCopied(false)
  }

  return <section className="panel social-samples" aria-labelledby="social-samples-title">
    <div className="social-samples-header">
      <div>
        <span className="social-samples-eyebrow">PUBLISHING PREVIEW LAB · OFFLINE</span>
        <h2 id="social-samples-title">Four sample platform posts</h2>
        <p>Inspect what a reviewed publishing draft would look like on each platform.
          Colors and sample copy refer to the supplied three-shirt reference. No poster or video is generated here; all account connections, scheduling and
          publishing are disabled in this sample.</p>
      </div>
      <span className="social-samples-pill">Samples only</span>
    </div>

    <div className="social-samples-tabs" role="tablist" aria-label="Sample publishing platform">
      {SOCIAL_PUBLISHING_SAMPLES.map(item =>
        <button key={item.id} type="button" role="tab"
          aria-selected={sample.id === item.id}
          aria-controls="social-sample-panel" id={'sample-tab-' + item.id}
          className={sample.id === item.id ? 'social-samples-tab selected' : 'social-samples-tab'}
          onClick={() => select(item.id)}>
          <strong>{item.name}</strong>
          <small>{item.mediaKind === 'text' ? 'Text post' : item.provider === 'instagram' ? 'Reel video' : 'Short video'}</small>
        </button>)}
    </div>

    <div role="tabpanel" className="social-samples-details" id="social-sample-panel"
      aria-labelledby={'sample-tab-' + sample.id}>
      <div className="social-samples-post">
        <div className="social-samples-profile">
          <span className="social-samples-avatar" aria-hidden="true">D</span>
          <span><strong>Demo Boutique</strong><small>{sample.name} · {sample.channel} · not published</small></span>
        </div>
        <div className="social-samples-shirt-swatches" aria-label="Sample clothing palette: soft yellow, black, forest green">
          <span className="social-shirt-swatch swatch-yellow" title="Soft yellow shirt" />
          <span className="social-shirt-swatch swatch-black" title="Black shirt" />
          <span className="social-shirt-swatch swatch-green" title="Forest green shirt" />
          <small>Shirt colors from reference · not the uploaded photograph</small>
        </div>
        {sample.mediaKind === 'video' && <div className="social-samples-portrait"
          role="img" aria-label="Vertical video placeholder. No media generated or attached.">
          <span className="social-samples-play" aria-hidden="true">▶</span>
          <strong>{sample.title}</strong>
          <small>9:16 · 30s · NO VIDEO ATTACHED</small>
        </div>}
        {sample.provider === 'youtube' && <h3>{sample.title}</h3>}
        <p className="social-samples-copy">{sample.copy}</p>
        <button type="button" className="social-samples-copy-button" onClick={copyText}>
          {copied ? 'Copied sample text' : 'Copy sample text'}
        </button>
      </div>
      <div className="social-samples-review">
        <span className="social-samples-eyebrow">SAMPLE WORKFLOW · NOT EXECUTED</span>
        <h3>Publish readiness</h3>
        <p><strong>State:</strong> DRAFT SAMPLE — no shop, account, approval or publish job.</p>
        <p><strong>Schedule:</strong> {sample.schedule}</p>
        <p><strong>API:</strong> {sample.adapter}</p>
        <p><strong>Media:</strong> {sample.mediaKind === 'video'
          ? 'Placeholder only; requires a reviewed existing Part 1 MP4'
          : 'Text only; no image or video'}</p>
        <h4>Required before a real post</h4>
        <ol>{sample.required.map(item => <li key={item}>{item}</li>)}</ol>
        <p className="social-samples-warning">{sample.warning}</p>
      </div>
    </div>
    <p className="social-samples-footnote">This gallery is local sample data, not customer content.
      It makes no API request, reserves no quota, and produces no provider receipt. Banners/poster
      creation belongs to the separate campaign-creation workstream.</p>
  </section>
}
