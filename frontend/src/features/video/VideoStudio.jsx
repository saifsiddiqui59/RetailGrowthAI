import { useEffect, useMemo, useRef, useState } from 'react'
import {
  VIDEO_MODES, VIDEO_TEMPLATES, VIDEO_ANIMATIONS, VIDEO_TRANSITIONS, compatibleMedia, makeVideoDraft,
  shiftVideoScene, retimeVideoDraft, validateVideoDraft, sourceClipPlaybackWindow,
  sourceClipTimeForPlayhead,
} from './video-model.mjs'
import { privateMediaPreviewUrl } from './video-transport.mjs'
import TimelineStudioSurface from './TimelineStudioSurface.jsx'
import { inspectCreativeDirection } from './creative-direction-adapter.mjs'
import './VideoStudio.css'

// Feature-owned panel. Feature #1 must mount it in the shared authenticated layout.
// mediaAssets/musicAssets MUST be server-authorized private-media objects.
// onRender MUST call the existing authenticated API after coordinator v2 contract approval.
export default function VideoStudio({
  shopId, mediaAssets = [], musicAssets = [], onRender = null,
  renderStatus = null, signedVideoUrl = null, onPrivateDownload = null,
  creativeDirection = null,
}) {
  const [draft, setDraft] = useState(() => makeVideoDraft({ shopId, mediaAssets }))
  const approvedRead = useMemo(() => {
    if (!creativeDirection) return null
    try { return inspectCreativeDirection(creativeDirection, {shopId, mediaAssets, musicAssets}) }
    catch(error) { return {error: error.message} }
  }, [creativeDirection, shopId, mediaAssets, musicAssets])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [selectedSceneIndex, setSelectedSceneIndex] = useState(0)
  const [timelinePlayhead, setTimelinePlayhead] = useState(null)
  const previewVideo = useRef(null)
  // A login/shop switch cannot retain the previous tenant's composition draft.
  useEffect(() => {
    setDraft(makeVideoDraft({ shopId, mediaAssets }))
    setSelectedSceneIndex(0)
    setTimelinePlayhead(null)
    setSubmitted(false)
    setError('')
  }, [shopId])
  useEffect(() => {
    if (approvedRead?.draft) {
      setDraft(approvedRead.draft)
      setSelectedSceneIndex(0)
      setTimelinePlayhead(null)
      setSubmitted(false)
    }
  }, [approvedRead])
  const assets = useMemo(() => compatibleMedia(draft.mode, mediaAssets, shopId), [draft.mode, mediaAssets, shopId])
  const approvedPosters = useMemo(() => (Array.isArray(mediaAssets) ? mediaAssets : [])
    .filter(asset => asset?.authorized === true && asset?.kind === 'poster' &&
      asset?.shop_id === shopId), [mediaAssets, shopId])
  const issues = useMemo(
    () => [...validateVideoDraft(draft, mediaAssets, musicAssets), ...(approvedRead?.error ? [approvedRead.error] : [])],
    [draft, mediaAssets, musicAssets, approvedRead],
  )
  const patch = (changes) => { if (creativeDirection) return; setDraft(prev => ({ ...prev, ...changes })); setSubmitted(false) }
  const selectedScene = draft.scenes[Math.min(selectedSceneIndex, draft.scenes.length - 1)]
  const sceneSource = (Array.isArray(mediaAssets) ? mediaAssets : [])
    .find(item => item?.authorized === true && item?.shop_id === shopId &&
      item.id === selectedScene?.asset_id)
  let previewSource = null
  let sourceWindow = null
  try {
    if (sceneSource?.kind === 'video') {
      sourceWindow = sourceClipPlaybackWindow(selectedScene, sceneSource)
    }
    if (sceneSource?.shop_id === shopId && sceneSource?.preview_url) {
      previewSource = privateMediaPreviewUrl(
        sceneSource.preview_url, import.meta.env?.VITE_SUPABASE_URL, shopId)
    }
  } catch { /* Invalid or cross-tenant source previews are never rendered. */ }
  // Scrubbing selects an exact approved source excerpt position; it never
  // synthesizes the final edited/transitioned Reel or grants media access.
  useEffect(() => {
    if (!previewSource || !previewVideo.current || !sourceWindow) return
    const target = sourceClipTimeForPlayhead(selectedScene, sceneSource, timelinePlayhead)
    if (target === null || previewVideo.current.readyState < 1) return
    if (Math.abs(previewVideo.current.currentTime - target) > .015) {
      previewVideo.current.currentTime = target
    }
  }, [timelinePlayhead, selectedScene, sceneSource, previewSource, sourceWindow?.start, sourceWindow?.end])
  function changeDuration(next) {
    if (creativeDirection) return
    try {
      patch(retimeVideoDraft(draft, next))
      setError('')
    } catch (exc) {
      setError(exc.message || 'This timeline cannot be retimed safely')
    }
  }
  const patchScene = (index, changes) => patch({ scenes: draft.scenes.map((item, i) =>
    i === index ? { ...item, ...changes } : item,
  ) })

  function newDraft({ mode = draft.mode, template = draft.template, duration = draft.duration_seconds } = {}) {
    if (creativeDirection) return
    setDraft(makeVideoDraft({ shopId, mode, template, duration, mediaAssets }))
    setError('')
    setSubmitted(false)
    setSelectedSceneIndex(0)
    setTimelinePlayhead(null)
  }
  async function submit(event) {
    event.preventDefault()
    setError('')
    if (issues.length || !onRender || (creativeDirection && !approvedRead?.draft)) return
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
  // The coordinator must return the trusted tenant identity with an output.
  // Never show a previously selected shop's signed video after a shop switch.
  // A prior job's signed artifact MUST NOT be presented as the preview of an
  // edited/new composition. Editing resets 'submitted'; the next valid submit
  // creates a new immutable job. This is only UI parity, not a server grant.
  // Encode success does not override an explicit owner QUALITY REJECTION.
  // The reviewed private artifact may still exist on the server for an audit,
  // but the UI must not surface it as an acceptable current Reel.
  const ownerRejected = renderStatus?.shop_id === shopId &&
    renderStatus?.visual_quality_status === 'OWNER_REJECTED'
  const ready = submitted && !ownerRejected && renderStatus?.status === 'SUCCEEDED' &&
    renderStatus?.shop_id === shopId &&
    typeof signedVideoUrl === 'string' && signedVideoUrl.length > 0
  return (
    <section className="f4-studio" aria-labelledby="f4-title">
      <header className="f4-head">
        <div>
          <p className="f4-eyebrow">RETAILGROWTHAI / CREATIVE STUDIO</p>
          <h2 id="f4-title">Professional Video Studio</h2>
          <p>Design a branded 9:16 Reel from your approved shop media.</p>
        </div>
        <span className="f4-status">{renderStatus?.shop_id === shopId ? renderStatus.status : 'LOCAL DRAFT'}</span>
      </header>
      <div className="f4-layout">
        <form className="f4-controls" onSubmit={submit} aria-label="Approved render options">
          {creativeDirection && <p className="f4-guidance" role="status">Feature #2 approved copy, scenes and camera direction are locked. Editing needs renewed creative approval.</p>}
          <div className="f4-two">
            <label>Video type
              <select disabled={Boolean(creativeDirection)} value={draft.mode} onChange={e => newDraft({ mode: e.target.value })}>
                {VIDEO_MODES.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
              </select>
            </label>
            <label>Professional style
              <select disabled={Boolean(creativeDirection)} value={draft.template} onChange={e => patch({ template: e.target.value })}>
                {VIDEO_TEMPLATES.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
              </select>
            </label>
          </div>
          <div className="f4-two">
            <label>Duration
              <select disabled={Boolean(creativeDirection)} value={draft.duration_seconds} onChange={e => changeDuration(Number(e.target.value))}>
                {[15, 30, 60].map(n => <option key={n} value={n}>{n} seconds</option>)}
              </select>
            </label>
            <label>Approved full-Reel narration
              <select disabled={Boolean(creativeDirection)} value={draft.voiceover_asset_id || ''}
                onChange={e => patch({ voiceover_asset_id: e.target.value || null })}>
                <option value="">No reviewed narration audio</option>
                {musicAssets.filter(a => a?.authorized === true && a?.shop_id === shopId &&
                  a?.kind === 'audio').map(a => <option key={a.id} value={a.id}>{a.title || a.id}</option>)}
              </select>
            </label>
            <label>Approved soundtrack
              <select disabled={Boolean(creativeDirection)} value={draft.music_asset_id || ''} onChange={e => patch({ music_asset_id: e.target.value || null })}>
                <option value="">No licensed music / silent export</option>
                {musicAssets.filter(track => track?.authorized === true && track?.shop_id === shopId &&
                  track?.kind === 'audio').map(track =>
                  <option key={track.id} value={track.id}>{track.title || track.id}</option>)}
              </select>
            </label>
          </div>
          {draft.mode === 'music_sync' && (
            <p className="f4-guidance">Only server-approved, same-shop music can render with a measured beat grid. Offline waveform detection and editor beat navigation are implemented; hosted soundtrack licensing and approved beat attachment remain required.</p>
          )}
          <h3 className="f4-subtitle">Storyboard <span>{draft.scenes.length} scenes</span></h3>
          <div className="f4-scenes">
            {draft.scenes.map((scene, index) => (
              <fieldset key={index} className="f4-scene">
                <legend>SCENE {String(index + 1).padStart(2, '0')} · {scene.start}s – {scene.start + scene.duration}s</legend>
                <div className="f4-reorder">
                  <button type="button" onClick={() => patch({ scenes: shiftVideoScene(draft.scenes, index, -1) })}
                    disabled={Boolean(creativeDirection) || index === 0} aria-label={'Move scene ' + (index + 1) + ' earlier'}>↑ Earlier</button>
                  <button type="button" onClick={() => patch({ scenes: shiftVideoScene(draft.scenes, index, 1) })}
                    disabled={Boolean(creativeDirection) || index === draft.scenes.length - 1}
                    aria-label={'Move scene ' + (index + 1) + ' later'}>↓ Later</button>
                </div>
                {draft.mode !== 'text' && (
                  <label>Approved product, poster or footage
                    <select disabled={Boolean(creativeDirection)} value={scene.asset_id || ''} onChange={e => patchScene(index, { asset_id: e.target.value || undefined })}>
                      <option value="">Select an authorized asset</option>
                      {assets.map(media => <option key={media.id} value={media.id}>{media.name || media.id} · {media.kind}</option>)}
                    </select>
                  </label>
                )}
                <label>Animated headline
                  <input disabled={Boolean(creativeDirection)} value={scene.headline} maxLength={110} onChange={e => patchScene(index, { headline: e.target.value })} />
                </label>
                <div className="f4-two">
                  <label>Motion
                    <select disabled={Boolean(creativeDirection)} value={scene.animation_preset || 'subtle_zoom'}
                      onChange={e => patchScene(index, { animation_preset: e.target.value })}>
                      {VIDEO_ANIMATIONS.map(value => <option key={value} value={value}>{value.replace('_', ' ')}</option>)}
                    </select>
                  </label>
                  <label>Scene transition
                    <select disabled={Boolean(creativeDirection)} value={scene.transition || 'fade'}
                      onChange={e => patchScene(index, { transition: e.target.value })}>
                      {VIDEO_TRANSITIONS.map(value => <option key={value} value={value}>{value}</option>)}
                    </select>
                  </label>
                </div>
                {draft.mode !== 'text' && approvedPosters.length > 0 && (
                  <label>Reviewed promotion poster overlay (optional)
                    <select disabled={Boolean(creativeDirection)} value={scene.poster_overlay_asset_id || ''}
                      onChange={e => patchScene(index, { poster_overlay_asset_id: e.target.value || undefined })}>
                      <option value="">No poster on this scene</option>
                      {approvedPosters.filter(poster => poster.id !== scene.asset_id).map(poster =>
                        <option key={poster.id} value={poster.id}>{poster.name || poster.id}</option>)}
                    </select>
                  </label>
                )}
                <label>Reviewed scene sound effect · first 2 seconds
                  <select disabled={Boolean(creativeDirection)} value={scene.sfx_asset_id || ''}
                    onChange={e => patchScene(index, { sfx_asset_id: e.target.value || undefined })}>
                    <option value="">No scene sound effect</option>
                    {musicAssets.filter(track => track?.authorized === true && track?.shop_id === shopId
                      && track?.kind === 'audio').map(track =>
                      <option key={track.id} value={track.id}>{track.title || track.id}</option>)}
                  </select>
                </label>
                <label>Approved offer (optional)
                  <input disabled={Boolean(creativeDirection)} value={scene.offer || ''} maxLength={70}
                    placeholder="Only real retailer-approved claims"
                    onChange={e => patchScene(index, { offer: e.target.value || undefined })} />
                </label>
                {draft.mode === 'media' && assets.some(asset => asset.id === scene.asset_id && asset.kind === 'video') && (
                  <div className="f4-two">
                    <label>Start source at (seconds)
                      <input disabled={Boolean(creativeDirection)} type="number" min="0" max="180" step=".1" value={scene.trim_start || 0}
                        onChange={e => patchScene(index, { trim_start: Number(e.target.value) })} />
                    </label>
                    <label className="f4-switch">
                      <input disabled={Boolean(creativeDirection)} type="checkbox" checked={scene.mute_source === true}
                        onChange={e => patchScene(index, { mute_source: e.target.checked })} />
                      Explicitly mute original clip audio
                    </label>
                  </div>
                )}
              </fieldset>
            ))}
          </div>
          <label>Final call to action
            <input disabled={Boolean(creativeDirection)} value={draft.cta} maxLength={110} onChange={e => patch({ cta: e.target.value })} />
          </label>
          {issues.length > 0 && <div role="alert" className="f4-issues">
            {issues.map(issue => <p key={issue}>{issue}</p>)}
          </div>}
          {error && <p role="alert" className="f4-issues">{error}</p>}
          {submitted && <p className="f4-guidance" role="status">Request submitted. The backend must confirm a durable render job and private artifact.</p>}
          <button className="f4-submit" type="submit" disabled={busy || issues.length > 0 || !onRender || Boolean(creativeDirection && !approvedRead?.draft)}>
            {busy ? 'Submitting…' : onRender ? 'Submit authorized render' : 'Backend v2 connection pending'}
          </button>
          <p className="f4-fine">Visual preview is a storyboard mock, not a rendered MP4. Nothing here bypasses backend shop access, media rights, usage limits or human approval.</p>
        </form>
        <aside className="f4-view" aria-label="Video storyboard preview">
          <nav className="f4-timeline" aria-label="Choose a storyboard scene to preview">
            {draft.scenes.map((scene, index) => (
              <button key={index} type="button" className={index === selectedSceneIndex ? 'f4-selected' : ''}
                aria-pressed={index === selectedSceneIndex} onClick={() => setSelectedSceneIndex(index)}
                style={{ flexGrow: scene.duration }} title={scene.headline}>
                {String(index + 1).padStart(2, '0')}
              </button>
            ))}
          </nav>
          {ownerRejected && <p role="alert" className="f4-issues">
            Owner rejected this Reel for visual quality. It is not a showcase or an approved commercial video.
          </p>}
          {ready ? (
            <>
              <video controls playsInline preload="metadata" src={signedVideoUrl} aria-label="Signed private rendered video" />
              {onPrivateDownload && <button onClick={onPrivateDownload} className="f4-submit">Download authorized MP4</button>}
            </>
          ) : (
            <div className={'f4-phone f4-' + draft.template}>
              <span className="f4-kicker">{VIDEO_TEMPLATES.find(([id]) => id === draft.template)?.[1]}</span>
              {previewSource && sceneSource?.kind === 'video' ? (
                <video key={selectedSceneIndex + ':' + sourceWindow?.start + ':' + previewSource}
                  ref={previewVideo} className="f4-source-preview" src={previewSource} controls playsInline muted
                  preload="metadata" aria-label="Authorized source footage excerpt; muted preview, not rendered advertisement"
                  onLoadedMetadata={event => {
                    if (sourceWindow) {
                      try { event.currentTarget.currentTime = sourceClipTimeForPlayhead(
                          selectedScene, sceneSource, timelinePlayhead) ?? sourceWindow.start } catch { /* unavailable seek is not a render approval */ }
                    }
                  }}
                  onPlay={event => {
                    if (sourceWindow && (event.currentTarget.currentTime < sourceWindow.start ||
                        event.currentTarget.currentTime >= sourceWindow.end)) {
                      event.currentTarget.currentTime = sourceWindow.start
                    }
                  }}
                  onTimeUpdate={event => {
                    if (sourceWindow && event.currentTarget.currentTime >= sourceWindow.end - .02) {
                      event.currentTarget.pause()
                    }
                  }} />
              ) : previewSource && ['image', 'poster'].includes(sceneSource?.kind) ? (
                <img className="f4-source-preview" src={previewSource}
                  alt="Authorized retailer product or poster source; not rendered advertisement" />
              ) : (
                <div className="f4-media-placeholder" aria-hidden="true">
                  <span>{selectedScene?.asset_id ? 'PRIVATE SOURCE PREVIEW NOT AVAILABLE' : 'SELECT MEDIA TO PREVIEW'}</span>
                </div>
              )}
              <div className="f4-preview-copy">
                <span>SCENE {selectedSceneIndex + 1} / {draft.scenes.length} · {selectedScene?.start ?? 0}–{(selectedScene?.start ?? 0) + (selectedScene?.duration ?? 0)}s</span>
                <strong>{selectedScene?.headline || 'Your product story'}</strong>
                <em>{selectedScene?.offer || (selectedSceneIndex === draft.scenes.length - 1 ? draft.cta : 'Approved media storyboard')}</em>
              </div>
              <span className="f4-mock-label">{previewSource && sourceWindow
                ? 'SOURCE ' + sourceWindow.start + '–' + sourceWindow.end + 's · MUTED PREVIEW ONLY'
                : previewSource ? 'SOURCE ASSET · FINAL REEL NOT RENDERED'
                : 'STORYBOARD ONLY · NO VIDEO GENERATED'}</span>
            </div>
          )}
          <p className="f4-view-note">{ready ? 'Signed output from the existing authenticated job workflow' :
            'Storyboard planning only—not footage of a real model. Saved jobs and private downloads require coordinator-enabled backend v2.'}</p>
        </aside>
      </div>
      <TimelineStudioSurface draft={draft} mediaAssets={mediaAssets} musicAssets={musicAssets}
        selectedSceneIndex={selectedSceneIndex} onSelectScene={setSelectedSceneIndex}
        onSeek={setTimelinePlayhead}
        approvedDirection={Boolean(creativeDirection)}
        spokenCaptions={approvedRead?.captionCues || []}
        onChange={next => { setDraft(next); setSubmitted(false) }} />
    </section>
  )
}
