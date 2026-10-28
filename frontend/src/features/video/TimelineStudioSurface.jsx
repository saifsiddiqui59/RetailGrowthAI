import { useEffect, useMemo, useRef, useState } from 'react'
import { getVisualSegmentTimeline, formatTime } from './vendor/timeline.js'
import { getTimelineRulerTicks, getTimelineAutoFitZoom } from './vendor/timelineScale.js'
import { TimelineCaptionClip, TimelineAudioClip } from './vendor/TimelineClips.jsx'
import { createEditorHistory, pushEditorHistory, undoEditorHistory, redoEditorHistory } from './vendor/editorHistoryCore.mjs'
import { studioReorder, studioSplit, studioTrimPair, studioSourceTrim, studioValidatedDraft } from './timeline-studio-bridge.mjs'
import './TimelineStudioSurface.css'

// Actual upstream Timeline Studio editing/history/clip components, modified for
// the existing approved rg_video_v2 and trusted HyperFrames renderer.
// No upstream localStorage account, cloud upload or independent video exporter.
export default function TimelineStudioSurface({ draft, onChange, onSelectScene, mediaAssets = [], musicAssets = [],
  selectedSceneIndex = 0, approvedDirection = false }) {
  const [history, setHistory] = useState(() => createEditorHistory(draft))
  const [playhead, setPlayhead] = useState(0)
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
  const selected = Math.min(Math.max(selectedSceneIndex,0), Math.max(0,draft.scenes.length - 1))
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
      if(approvedDirection || index === draft.scenes.length - 1) return
      event.stopPropagation()
      const target=event.currentTarget.closest('.f4-studio-track-body')
      const width=target?.getBoundingClientRect().width || 1
      const startX=event.clientX
      const original=draft
      const release=e=>{
        window.removeEventListener('pointerup',release)
        const delta=(e.clientX - startX)*draft.duration_seconds/width*(edge==='start'?-1:1)
        if(Math.abs(delta)>0.03) change(() => studioTrimPair(original,index,Math.round(delta*10)/10))
      }
      window.addEventListener('pointerup',release,{once:true})
    },
    startAudioSegmentMove: () => {},
    selectAudioClip: () => {},
    setAudioSegments: () => setFeedback('Audio gain automation is not supported by the current HyperFrames contract'),
  }
  const captions = draft.scenes.map((s,i)=>({id:'caption-'+i,text:s.headline,start:s.start,
    end:s.start+s.duration,hidden:false}))
  const trackMusic = draft.music_asset_id && musicAssets.some(m=>m.id===draft.music_asset_id &&
    m.shop_id===draft.shop_id && m.authorized===true)
    ? [{id:'licensed-audio',start:0,duration:draft.duration_seconds,volume:1}] : []
  return <section className="f4-ts-editor" aria-label="Professional multi-track video timeline">
    <div className="f4-ts-toolbar">
      <strong>Timeline Studio <small>MIT upstream · HyperFrames output</small></strong>
      <div className="f4-ts-tools">
        <button type="button" onClick={()=>applyHistory(undoEditorHistory)}
          disabled={approvedDirection||!history.past.length} aria-label="Undo timeline edit">Undo</button>
        <button type="button" onClick={()=>applyHistory(redoEditorHistory)}
          disabled={approvedDirection||!history.future.length} aria-label="Redo timeline edit">Redo</button>
        <button type="button" disabled={approvedDirection||draft.scenes.length>=12}
          onClick={split} aria-label="Split video at playhead">Split at playhead</button>
        <button type="button" disabled={approvedDirection||selected<=0}
          onClick={()=>{move(selected,selected-1);onSelectScene(selected-1)}}>Earlier</button>
        <button type="button" disabled={approvedDirection||selected===draft.scenes.length-1}
          onClick={()=>{move(selected,selected+1);onSelectScene(selected+1)}}>Later</button>
        <label>Zoom <input aria-label="Timeline zoom" type="range" min=".25" max="4" step=".25"
          value={zoom} onChange={e=>setZoom(Number(e.target.value))} /></label>
      </div>
    </div>
    <div className="f4-ts-track-scroll">
      <div className="f4-ts-ruler" aria-label="Timeline ruler">
        {ticks.map(t=><span key={t.id} style={{left:t.left+'%'}}>{t.label}</span>)}
      </div>
      <div className="f4-ts-row">
        <span className="f4-ts-track-name">VIDEO</span>
        <div className="f4-studio-track-body" onClick={e=>{
          if(e.target===e.currentTarget) setPlayhead(
            Math.round(Math.max(0,Math.min(1,e.nativeEvent.offsetX/e.currentTarget.clientWidth))*draft.duration_seconds*100)/100)
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
      <div className="f4-ts-row">
        <span className="f4-ts-track-name">MUSIC</span>
        <div className="f4-studio-track-body f4-ts-audio">
          {trackMusic.length ? trackMusic.map(m=><TimelineAudioClip key={m.id} segment={m}
            laneIndex={0} timelineDuration={draft.duration_seconds} selected={false}
            rangeSelected={false} waveformVisible={false} gainDisabled t={x=>x}
            handlersRef={handlers} />) : <span className="f4-ts-empty">No licensed soundtrack selected</span>}
        </div>
      </div>
      <div className="f4-ts-row">
        <span className="f4-ts-track-name">VOICE / SFX</span>
        <div className="f4-studio-track-body"><span className="f4-ts-empty">
          Server-approved voice/SFX only · independent gain disabled until renderer parity</span></div>
      </div>
      <div className="f4-ts-playhead" style={{left:(playhead/draft.duration_seconds*100)+'%'}}
        aria-hidden="true" />
    </div>
    <div className="f4-ts-inspector">
      <label>Playhead <input type="range" min="0" max={draft.duration_seconds} step=".1"
        value={playhead} onChange={e=>{const t=Number(e.target.value);setPlayhead(t);const i=spans.findIndex(s=>t>=s.start&&t<s.end);if(i>=0)onSelectScene(i)}} />
        <output>{formatTime(playhead)}</output></label>
      {source?.kind==='video'&&<label>Source trim (s) <input type="number" min="0" max="180"
        step=".1" disabled={approvedDirection} value={draft.scenes[selected].trim_start||0}
        onChange={e=>change(d=>studioSourceTrim(d,selected,Number(e.target.value),mediaAssets))}/></label>}
      <span className="f4-ts-parity">Only fade/slide/cut, approved animation presets and native
        video trims can be exported. Unsupported effects, caption rewriting and gain automation are disabled.</span>
    </div>
    {approvedDirection && <p role="status" className="f4-ts-note">Approved Feature #2 direction locked. Timeline is preview-only until a coordinator-authorized revised approval exists.</p>}
    {feedback && <p role="alert" className="f4-ts-error">{feedback}</p>}
  </section>
}
