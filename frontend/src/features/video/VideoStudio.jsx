import { useMemo, useState } from 'react'
import {
  VIDEO_MODES, VIDEO_TEMPLATES, compatibleMedia, makeVideoDraft,
  shiftVideoScene, recalculateScenes, validateVideoDraft,
} from './video-model.mjs'
import './VideoStudio.css'

// Feature-owned panel. Feature #1 must mount it in the shared authenticated layout.
// mediaAssets/musicAssets MUST be server-authorized private-media objects.
// onRender MUST call the existing authenticated API after coordinator v2 contract approval.
export default function VideoStudio({
  shopId, mediaAssets = [], musicAssets = [], onRender = null,
  renderStatus = null, signedVideoUrl = null, onPrivateDownload = null,
}) {
  const [draft, setDraft] = useState(() => makeVideoDraft({ shopId, mediaAssets }))
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const assets = useMemo(() => compatibleMedia(draft.mode, mediaAssets), [draft.mode, mediaAssets])
  const issues = useMemo(
    () => validateVideoDraft(draft, mediaAssets, musicAssets),
    [draft, mediaAssets, musicAssets],
  )
  const patch = (changes) => { setDraft(prev => ({ ...prev, ...changes })); setSubmitted(false) }
  const patchScene = (index, changes) => patch({ scenes: draft.scenes.map((item, i) =>
    i === index ? { ...item, ...changes } : item,
  ) })

  function newDraft({ mode = draft.mode, template = draft.template, duration = draft.duration_seconds } = {}) {
    setDraft(makeVideoDraft({ shopId, mode, template, duration, mediaAssets }))
    setError('')
    setSubmitted(false)
  }
  async function submit(event) {
    event.preventDefault()
    setError('')
    if (issues.length || !onRender) return
    setBusy(true)
    try {
      await onRender(structuredClone(draft))
      setSubmitted(true)
    } catch (exc) {
      setError(exc?.message || 'Video request was not accepted')
    } finally {
      setBusy(false)
    }
  }
  const ready = renderStatus?.status === 'SUCCEEDED' && typeof signedVideoUrl === 'string'
  return (
    <section className="f4-studio" aria-labelledby="f4-title">
      <header className="f4-head">
        <div>
          <p className="f4-eyebrow">RETAILGROWTHAI / CREATIVE STUDIO</p>
          <h2 id="f4-title">Professional Video Studio</h2>
          <p>Design a branded 9:16 Reel from your approved shop media.</p>
        </div>
        <span className="f4-status">{renderStatus?.status || 'LOCAL DRAFT'}</span>
      </header>
      <div className="f4-layout">
        <form className="f4-controls" onSubmit={submit}>
          <div className="f4-two">
            <label>Video type
              <select value={draft.mode} onChange={e => newDraft({ mode: e.target.value })}>
                {VIDEO_MODES.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
              </select>
            </label>
            <label>Professional style
              <select value={draft.template} onChange={e => newDraft({ template: e.target.value })}>
                {VIDEO_TEMPLATES.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
              </select>
            </label>
          </div>
          <div className="f4-two">
            <label>Duration
              <select value={draft.duration_seconds} onChange={e => newDraft({ duration: Number(e.target.value) })}>
                {[15, 30, 60].map(n => <option key={n} value={n}>{n} seconds</option>)}
              </select>
            </label>
            <label>Approved soundtrack
              <select value={draft.music_asset_id || ''} onChange={e => patch({ music_asset_id: e.target.value || null })}>
                <option value="">No licensed music / silent export</option>
                {musicAssets.filter(track => track?.authorized === true).map(track =>
                  <option key={track.id} value={track.id}>{track.title || track.id}</option>)}
              </select>
            </label>
          </div>
          {draft.mode === 'music_sync' && (
            <p className="f4-guidance">Beat grid must come from an approved music analysis service. Beat extraction and automatic alignment are pending; this mode cannot render without the beat contract.</p>
          )}
          <h3 className="f4-subtitle">Storyboard <span>{draft.scenes.length} scenes</span></h3>
          <div className="f4-scenes">
            {draft.scenes.map((scene, index) => (
              <fieldset key={index} className="f4-scene">
                <legend>SCENE {String(index + 1).padStart(2, '0')} · {scene.start}s – {scene.start + scene.duration}s</legend>
                <div className="f4-reorder">
                  <button type="button" onClick={() => patch({ scenes: shiftVideoScene(draft.scenes, index, -1) })}
                    disabled={index === 0} aria-label={'Move scene ' + (index + 1) + ' earlier'}>↑ Earlier</button>
                  <button type="button" onClick={() => patch({ scenes: shiftVideoScene(draft.scenes, index, 1) })}
                    disabled={index === draft.scenes.length - 1}
                    aria-label={'Move scene ' + (index + 1) + ' later'}>↓ Later</button>
                </div>
                {draft.mode !== 'text' && (
                  <label>Approved product, poster or footage
                    <select value={scene.asset_id || ''} onChange={e => patchScene(index, { asset_id: e.target.value || undefined })}>
                      <option value="">Select an authorized asset</option>
                      {assets.map(media => <option key={media.id} value={media.id}>{media.name || media.id} · {media.kind}</option>)}
                    </select>
                  </label>
                )}
                <label>Animated headline
                  <input value={scene.headline} maxLength={110} onChange={e => patchScene(index, { headline: e.target.value })} />
                </label>
                <label>Approved offer (optional)
                  <input value={scene.offer || ''} maxLength={70}
                    placeholder="Only real retailer-approved claims"
                    onChange={e => patchScene(index, { offer: e.target.value || undefined })} />
                </label>
                {draft.mode === 'media' && assets.some(asset => asset.id === scene.asset_id && asset.kind === 'video') && (
                  <div className="f4-two">
                    <label>Start source at (seconds)
                      <input type="number" min="0" max="180" step=".1" value={scene.trim_start || 0}
                        onChange={e => patchScene(index, { trim_start: Number(e.target.value) })} />
                    </label>
                    <label className="f4-switch">
                      <input type="checkbox" checked={scene.mute_source === true}
                        onChange={e => patchScene(index, { mute_source: e.target.checked })} />
                      Explicitly mute original clip audio
                    </label>
                  </div>
                )}
              </fieldset>
            ))}
          </div>
          <label>Final call to action
            <input value={draft.cta} maxLength={110} onChange={e => patch({ cta: e.target.value })} />
          </label>
          {issues.length > 0 && <div role="alert" className="f4-issues">
            {issues.map(issue => <p key={issue}>{issue}</p>)}
          </div>}
          {error && <p role="alert" className="f4-issues">{error}</p>}
          {submitted && <p className="f4-guidance" role="status">Request submitted. The backend must confirm a durable render job and private artifact.</p>}
          <button className="f4-submit" type="submit" disabled={busy || issues.length > 0 || !onRender}>
            {busy ? 'Submitting…' : onRender ? 'Submit authorized render' : 'Backend v2 connection pending'}
          </button>
          <p className="f4-fine">Visual preview is a storyboard mock, not a rendered MP4. Nothing here bypasses backend shop access, media rights, usage limits or human approval.</p>
        </form>
        <aside className="f4-view" aria-label="Video storyboard preview">
          {ready ? (
            <>
              <video controls playsInline preload="metadata" src={signedVideoUrl} aria-label="Signed private rendered video" />
              {onPrivateDownload && <button onClick={onPrivateDownload} className="f4-submit">Download authorized MP4</button>}
            </>
          ) : (
            <div className={'f4-phone f4-' + draft.template}>
              <span className="f4-kicker">{VIDEO_TEMPLATES.find(([id]) => id === draft.template)?.[1]}</span>
              <div className="f4-mock-motion" aria-hidden="true"><span /><span /><span /></div>
              <div className="f4-preview-copy">
                <span>{draft.mode.replace('_', ' ').toUpperCase()} / 9:16</span>
                <strong>{draft.scenes[0]?.headline || 'Your product story'}</strong>
                <em>{draft.scenes[0]?.offer || draft.cta}</em>
              </div>
              <span className="f4-mock-label">STORYBOARD ONLY · NO VIDEO GENERATED</span>
            </div>
          )}
          <p className="f4-view-note">{ready ? 'Signed output from the existing authenticated job workflow' :
            'The real preview, saved render history and signed downloads require coordinator-approved backend integration.'}</p>
        </aside>
      </div>
    </section>
  )
}
