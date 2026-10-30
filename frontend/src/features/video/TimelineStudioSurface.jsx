import { useEffect, useMemo, useRef, useState } from 'react'
import { getVisualSegmentTimeline, formatTime } from './vendor/timeline.js'
import { getTimelineRulerTicks, getTimelineAutoFitZoom, getTimelineVisibleDuration } from './vendor/timelineScale.js'
import { TimelineCaptionClip, TimelineAudioClip } from './vendor/TimelineClips.jsx'
import { fixedAudioMixDisplay } from './audio-mix-display.mjs'
import { createEditorHistory, pushEditorHistory, undoEditorHistory, redoEditorHistory } from './vendor/editorHistoryCore.mjs'
import { studioReorder, studioSplit, studioDuplicate, studioTrimPair, studioSourceTrim, studioValidatedDraft } from './timeline-studio-bridge.mjs'
import { FrameTimecodeInput } from './vendor/openreel/FrameTimecodeInput.jsx'
import { OpenReelClipSnapper } from './vendor/openreel/clip-snap.mjs'
import { proposedBeatMarkers } from './beat-preview.mjs'
import { getTimelineItemRanges, getTimelineTrackSelection, getSplittableTimelineItemIds } from './vendor/openreel/timeline-item-actions.mjs'
import './TimelineStudioSurface.css'

// Actual upstream Timeline Studio editing/history/clip components, modified for
// the existing approved rg_video_v2 and trusted HyperFrames renderer.
// No upstream localStorage account, cloud upload or independent video exporter.
export default function TimelineStudioSurface({ draft, onChange, onSelectScene, mediaAssets = [], musicAssets = [],
  selectedSceneIndex = 0, approvedDirection = false, spokenCaptions = [] }) {
  const [history, setHistory] = useState(() => createEditorHistory(draft))
  const [playhead, setPlayhead] = useState(0)
  const [snapEnabled, setSnapEnabled] = useState(true)
  const [zoom, setZoom] = useState(() => getTimelineAutoFitZoom(draft.duration_seconds))
  const [feedback, setFeedback] = useState('')
  const dragFrom = useRef(null)
  const lastSent = useRef(null)
  const handlers = useRef({})
  useEffect(() => {
    if (draft !== lastSent.current) {
      setHistory(createEditorHistory(draft))
      setPlayhead(0)
    }
  }, [draft])
  // Media/account changes invalidate history even when a signed preview URL is stale.
  useEffect(() => { setHistory(createEditorHistory(draft)); setPlayhead(0); lastSent.current = null }, [draft.shop_id])
  const spans = useMemo(() => getVisualSegmentTimeline(draft.scenes.map((s,i) =>
    ({ id: String(i), duration: s.duration }))), [draft.scenes])
  const ticks = useMemo(() => getTimelineRulerTicks(draft.duration_seconds, zoom, 0, draft.duration_seconds)
    .filter(tick => tick.isMajor), [draft.duration_seconds, zoom])
  // Zoom changes the actual edit-track pixel scale, not only the ruler labels.
  // Content stays within a horizontally scrollable workspace on narrow screens.
  const trackPixels = Math.min(18000, Math.max(560,
    Math.round(900 * draft.duration_seconds / getTimelineVisibleDuration(zoom))))
  const selected = Math.min(Math.max(selectedSceneIndex,0), Math.max(0,draft.scenes.length - 1))
  const previewFps = draft.output?.fps === 24 ? 24 : 30
  // Minimal projection of approved scenes; OpenReel only reads layout metadata.
  // No client media grants, signed URLs, backend data or effect authority enter it.
  const timelineProject = useMemo(() => ({timeline: {tracks: [{
    id: 'video', type: 'video', locked: approvedDirection,
    clips: draft.scenes.map((scene, i) => ({
      id: 'scene-'+i, startTime: scene.start, duration: scene.duration,
    })),
  }]}}), [draft.scenes, approvedDirection])
  const clipRanges = getTimelineItemRanges(timelineProject)
  const cutPositions = getTimelineTrackSelection(timelineProject, 'video')
    .map(item => clipRanges.find(clip => clip.id === item.id)?.startTime)
    .filter(Number.isFinite)
  const beatMarkers = useMemo(() => proposedBeatMarkers(draft, musicAssets), [draft, musicAssets])
  const previousCut = cutPositions.filter(cut => cut < playhead - .0001).at(-1)
  const nextCut = cutPositions.find(cut => cut > playhead + .0001)
  const canSplit = getSplittableTimelineItemIds(
    timelineProject, ['scene-'+selected], playhead).length > 0 &&
    spans[selected] && playhead - spans[selected].start >= .5 &&
    spans[selected].end - playhead >= .5
  const seekToFrame = (seconds, withSnap = false) => {
    let requested = seconds
    if (withSnap && snapEnabled) {
      const nearest = beatMarkers.length ? beatMarkers.reduce((a,b) =>
        Math.abs(b-seconds)<Math.abs(a-seconds)?b:a) : null
      if (nearest !== null && Math.abs(nearest-seconds) <= 8*draft.duration_seconds/trackPixels) {
        requested = nearest // UI-only; never authorizes the soundtrack or edit
      } else {
        const snap = new OpenReelClipSnapper({snapThreshold: 8, gridSize: 1})
          .snapToGrid(seconds, timelineProject.timeline, 'video',
            trackPixels / draft.duration_seconds)
        if (snap.didSnap) requested = snap.snappedTime
      }
    }
    const position = Math.min(draft.duration_seconds,
      Math.max(0, Math.round(requested * previewFps) / previewFps))
    setPlayhead(position)
    const index = spans.findIndex(span => position >= span.start && position < span.end)
    if (index >= 0) onSelectScene(index)
  }
  const change = (fn) => {
    if (approvedDirection) { setFeedback('Approved Feature #2 direction is read-only. Request a revised approval to change edit timing.'); return }
    try {
      const updated = studioValidatedDraft(fn(draft), mediaAssets, musicAssets)
      if (updated === draft) return
      lastSent.current = updated
      setHistory(p => pushEditorHistory(p, updated))
      onChange(updated)
      setFeedback('')
    } catch(e) { setFeedback(e.message || 'Timeline operation is unsupported') }
  }
  const move = (from,to) => change(d => studioReorder(d,from,to))
  const split = () => {
    const span = spans[selected]
    const offset = Number((playhead - span.start).toFixed(3))
    change(d => studioSplit(d,selected,offset,mediaAssets))
  }
  const applyHistory = action => {
    if (approvedDirection) return
    const t = action(history)
    if (!t.changed) return
    lastSent.current = t.value
    setHistory(t.history)
    onChange(t.value)
    setFeedback('')
  }
  const source = mediaAssets.find(a => a.authorized === true && a.shop_id === draft.shop_id &&
    a.id === draft.scenes[selected]?.asset_id)
  handlers.current = {
    startTimelineClipDrag: (_event,track,_id,index) => { if(track==='caption')onSelectScene(index) },
    showTrackContextMenu: event => event.preventDefault(),
    selectCaptionClip: (_event,_id,index,start) => { onSelectScene(index); setPlayhead(start) },
    startCaptionResize: (event,_id,index,edge) => {
      const boundary = edge === 'start' ? index - 1 : index
      if (approvedDirection || boundary < 0 || boundary >= draft.scenes.length - 1) return
      event.stopPropagation()
      const target = event.currentTarget.closest('.f4-studio-track-body')
      const width = target?.getBoundingClientRect().width || 1
      const startX = event.clientX
      const original = draft
      const release = e => {
        window.removeEventListener('pointerup', release)
        const delta = (e.clientX - startX) * draft.duration_seconds / width
        if (Math.abs(delta) > 0.03) {
          change(() => studioTrimPair(original, boundary, Math.round(delta * 10) / 10, mediaAssets))
        }
      }
      window.addEventListener('pointerup', release, { once: true })
    },
    startAudioSegmentMove: () => {},
    selectAudioClip: () => {},
    setAudioSegments: () => setFeedback('Audio gain automation is not supported by the current HyperFrames contract'),
  }
  const captions = draft.scenes.map((s,i)=>({id:'caption-'+i,text:s.headline,start:s.start,
    end:s.start+s.duration,hidden:false}))
  const audioMix = fixedAudioMixDisplay(draft, mediaAssets, musicAssets)
  const trackMusic = audioMix.music
    ? [{id:'licensed-audio',start:0,duration:draft.duration_seconds,
        ...(audioMix.musicGain !== null ? {volume:audioMix.musicGain} : {})}] : []
  const shortcuts = event => {
    // Read-only one-frame navigation on the focused video track also works
    // for immutable Feature2-approved directions; it never changes the draft.
    // Do not steal cursor keys from timecode, text, buttons or zoom controls.
    const editingField = event.target?.closest?.(
      'input,textarea,select,[contenteditable="true"]')
    if (editingField || event.altKey) return
    const onTracks = event.target?.closest?.('.f4-ts-track-scroll')
    if (onTracks && !event.target?.closest?.('button,[role="button"],a[href]') &&
        !event.ctrlKey && !event.metaKey &&
        (event.key === 'ArrowLeft' || event.key === 'ArrowRight')) {
      event.preventDefault()
      const direction = event.key === 'ArrowRight' ? 1 : -1
      seekToFrame(playhead + direction * (event.shiftKey ? 10 : 1) / previewFps)
      return
    }
    if (approvedDirection || (!event.ctrlKey && !event.metaKey) ||
        event.key.toLowerCase() !== 'z') return
    event.preventDefault()
    applyHistory(event.shiftKey ? redoEditorHistory : undoEditorHistory)
  }
  return <section className="f4-ts-editor" aria-label="Professional multi-track video timeline"
    onKeyDown={shortcuts}>
    <div className="f4-ts-toolbar">
      <strong>Timeline Studio <small>OpenReel frame controls · HyperFrames output</small></strong>
      <FrameTimecodeInput position={playhead} duration={draft.duration_seconds}
        frameRate={previewFps} onSeek={seekToFrame} />
      <div className="f4-ts-tools">
        <button type="button" onClick={()=>applyHistory(undoEditorHistory)}
          disabled={approvedDirection||!history.past.length} aria-label="Undo timeline edit"
          aria-keyshortcuts="Control+Z Meta+Z">Undo</button>
        <button type="button" onClick={()=>applyHistory(redoEditorHistory)}
          disabled={approvedDirection||!history.future.length} aria-label="Redo timeline edit"
          aria-keyshortcuts="Control+Shift+Z Meta+Shift+Z">Redo</button>
        <button type="button" disabled={approvedDirection||draft.scenes.length>=12||!canSplit}
          onClick={split} aria-label="Split video at playhead">Split at playhead</button>
        <button type="button"
          disabled={approvedDirection||draft.scenes.length>=12||!draft.scenes[selected]||
            draft.scenes[selected].duration<1||
            (draft.scenes[selected].sfx_asset_id!=null&&draft.scenes[selected].duration<4)}
          onClick={()=>change(d=>studioDuplicate(d,selected,mediaAssets))}
          aria-label="Duplicate selected clip with two half-length replays"
          title="Replay the selected visual twice within its original timeline duration">Duplicate clip</button>
        <button type="button" disabled={previousCut == null}
          onClick={()=>seekToFrame(previousCut)} aria-label="Previous scene cut">Previous cut</button>
        <button type="button" disabled={nextCut == null}
          onClick={()=>seekToFrame(nextCut)} aria-label="Next scene cut">Next cut</button>
        <label><input type="checkbox" checked={snapEnabled}
          onChange={event=>setSnapEnabled(event.target.checked)}
          aria-label="Snap to scene cuts and grid" /> Snap</label>
        <button type="button" disabled={approvedDirection||selected<=0}
          onClick={()=>{move(selected,selected-1);onSelectScene(selected-1)}}>Earlier</button>
        <button type="button" disabled={approvedDirection||selected===draft.scenes.length-1}
          onClick={()=>{move(selected,selected+1);onSelectScene(selected+1)}}>Later</button>
        <label>Zoom <input aria-label="Timeline zoom" type="range" min=".25" max="4" step=".25"
          value={zoom} onChange={e=>setZoom(Number(e.target.value))} /></label>
      </div>
    </div>
    <div className="f4-ts-track-scroll" role="region" tabIndex={0}
      aria-label="Scrollable video tracks"
      aria-keyshortcuts="ArrowLeft ArrowRight Shift+ArrowLeft Shift+ArrowRight"
      title="Focus tracks: left/right jog one frame; Shift+left/right jog ten frames">
      <div className="f4-ts-timeline-content" style={{width:(74 + trackPixels)+'px'}}>
      <div className="f4-ts-ruler" aria-label="Timeline ruler">
        {ticks.map(t=><span key={t.id} style={{left:t.left+'%'}}>{t.label}</span>)}
      </div>
      {beatMarkers.length > 0 && <div className="f4-ts-row f4-ts-beat-row">
        <span className="f4-ts-track-name">BEATS</span>
        <div className="f4-studio-track-body f4-ts-beat-track"
          aria-label="Proposed music beat positions; server verification required">
          {beatMarkers.map((beat,i)=><button type="button" key={beat}
            className="f4-ts-beat-marker" style={{left:beat/draft.duration_seconds*100+'%'}}
            aria-label={'Seek to proposed beat '+(i+1)+' at '+beat.toFixed(3)+'s'}
            title={'Beat proposal '+beat.toFixed(3)+'s'}
            onClick={()=>seekToFrame(beat)} />)}
        </div>
      </div>}
      <div className="f4-ts-row">
        <span className="f4-ts-track-name">VIDEO</span>
        <div className="f4-studio-track-body" onClick={e=>{
          if(e.target===e.currentTarget) seekToFrame(
            Math.max(0,Math.min(1,e.nativeEvent.offsetX/e.currentTarget.clientWidth))*draft.duration_seconds, true)
        }}>
          {spans.map((span,i)=><button key={i} type="button" draggable={!approvedDirection}
            data-timeline-segment-track="image" data-timeline-segment-index={i}
            className={'f4-ts-clip '+(selected===i?'is-selected':'')}
            style={{left:span.start/draft.duration_seconds*100+'%',
              width:span.duration/draft.duration_seconds*100+'%'}}
            onDragStart={()=>{dragFrom.current=i}}
            onDragOver={e=>e.preventDefault()}
            onDrop={e=>{e.preventDefault();if(dragFrom.current!==null){move(dragFrom.current,i);onSelectScene(i)}dragFrom.current=null}}
            onClick={()=>{onSelectScene(i);setPlayhead(span.start+span.duration/2)}}
            aria-label={'Scene '+(i+1)+': '+(draft.scenes[i].headline)}>
            <span className="f4-ts-clip-index">{i+1}</span>
            <span className="f4-ts-clip-title">{draft.scenes[i].headline}</span>
            <small>{formatTime(span.duration)}</small>
          </button>)}
        </div>
      </div>
      <div className="f4-ts-row">
        <span className="f4-ts-track-name">CAPTIONS</span>
        <div className="f4-studio-track-body f4-ts-captions">
          {captions.map((caption,i)=><TimelineCaptionClip key={caption.id}
            segment={caption} index={i} laneIndex={0} start={caption.start}
            duration={caption.end-caption.start} timelineDuration={draft.duration_seconds}
            current={playhead>=caption.start&&playhead<caption.end} selected={selected===i}
            dragging={false} reorderTarget={false} rangeSelected={false} placeholder={false}
            handlersRef={handlers} />)}
        </div>
      </div>
      {spokenCaptions.length > 0 && <div className="f4-ts-row">
        <span className="f4-ts-track-name">SPOKEN SUBTITLES</span>
        <div className="f4-studio-track-body f4-ts-captions"
          aria-label="Approved spoken subtitles" style={{pointerEvents:'none'}}>
          {spokenCaptions.map((cue,i)=><TimelineCaptionClip key={'spoken-'+i}
            segment={{id:'approved-spoken-'+i,text:cue.text,hidden:false}}
            index={i} laneIndex={1} start={cue.start} duration={cue.duration}
            timelineDuration={draft.duration_seconds}
            current={playhead>=cue.start&&playhead<cue.start+cue.duration}
            selected={false} dragging={false} reorderTarget={false}
            rangeSelected={false} placeholder={false} handlersRef={handlers} />)}
        </div>
      </div>}
      <div className="f4-ts-row">
        <span className="f4-ts-track-name">MUSIC</span>
        <div className="f4-studio-track-body f4-ts-audio">
          {trackMusic.length ? <>
            {trackMusic.map(m=><TimelineAudioClip key={m.id} segment={m}
              laneIndex={0} timelineDuration={draft.duration_seconds} selected={false}
              rangeSelected={false} waveformVisible={false} gainDisabled
              hideGain={audioMix.musicGain === null} t={x=>x}
              handlersRef={handlers} />)}
            <span className="f4-ts-empty" role="note">
              {audioMix.musicGainUnknownUntilServerProbe
                ? 'Music level is not previewed: final gain depends on decoded source audio.'
                : 'Renderer-fixed music gain: '+Math.round(audioMix.musicGain*100)+'%; not editable.'}
            </span>
          </> : <span className="f4-ts-empty">No licensed soundtrack selected</span>}
        </div>
      </div>
      <div className="f4-ts-row">
        <span className="f4-ts-track-name">NARRATION</span>
        <div className="f4-studio-track-body f4-ts-audio">
          {draft.voiceover_asset_id && musicAssets.some(a =>
            a.id === draft.voiceover_asset_id && a.shop_id === draft.shop_id &&
            a.kind === 'audio' && a.authorized === true)
            ? <TimelineAudioClip segment={{id:'approved-voice',start:0,
                duration:draft.duration_seconds,volume:1}}
                laneIndex={0} timelineDuration={draft.duration_seconds}
                selected={false} rangeSelected={false} waveformVisible={false}
                gainDisabled t={x=>x} handlersRef={handlers} />
            : <span className="f4-ts-empty">No approved full-Reel voice recording</span>}
        </div>
      </div>
      <div className="f4-ts-row">
        <span className="f4-ts-track-name">SCENE SFX</span>
        <div className="f4-studio-track-body f4-ts-audio">
          {draft.scenes.some(scene => scene.sfx_asset_id) ? draft.scenes.flatMap((scene,i) => {
            if (!scene.sfx_asset_id || !musicAssets.some(asset =>
              asset.id === scene.sfx_asset_id && asset.shop_id === draft.shop_id &&
              asset.kind === 'audio' && asset.authorized === true)) return []
            const segment = {id:'sfx-'+i,start:scene.start,duration:Math.min(2,scene.duration),
              volume:0.25,name:scene.sfx_asset_id}
            return [<TimelineAudioClip key={segment.id} segment={segment} laneIndex={0}
              timelineDuration={draft.duration_seconds} selected={selected===i}
              rangeSelected={false} waveformVisible={false} gainDisabled t={x=>x}
              handlersRef={handlers} />]
          }) : <span className="f4-ts-empty">Reviewed scene effects only · 2s max at fixed 25% gain</span>}
        </div>
      </div>
      <div className="f4-ts-playhead" style={{left:(74 + playhead/draft.duration_seconds*trackPixels)+'px'}}
        aria-hidden="true" />
      </div>
    </div>
    <div className="f4-ts-inspector">
      <label>Playhead <input type="range" min="0" max={draft.duration_seconds} step="any"
        value={playhead} onChange={e=>seekToFrame(Number(e.target.value), true)} />
        <output>{formatTime(playhead)}</output></label>
      {source?.kind==='video'&&<label>Source trim (s) <input type="number" min="0" max="180"
        step=".1" disabled={approvedDirection} value={draft.scenes[selected].trim_start||0}
        onChange={e=>change(d=>studioSourceTrim(d,selected,Number(e.target.value),mediaAssets))}/></label>}
      <span className="f4-ts-parity">Only fade/slide/cut, approved animation presets and native
        video trims can be exported. Audio mix levels are fixed by the renderer after media probing;
        this timeline does not audition the final soundtrack. Unsupported effects, caption rewriting
        and gain automation are disabled.</span>
    </div>
    {approvedDirection && <p role="status" className="f4-ts-note">Approved Feature #2 direction locked. Timeline is preview-only until a coordinator-authorized revised approval exists.</p>}
    {feedback && <p role="alert" className="f4-ts-error">{feedback}</p>}
  </section>
}
