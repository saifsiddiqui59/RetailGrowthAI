/** Dependency-free CPU starter editor for v2 private poster documents.
 *
 * Drag/drop enhancements remain in optional React Konva. This React-only
 * editor needs no new frontend packages or GPU. It never fetches media; the
 * signed-in host supplies already-loaded, current shop-authorized images.
 * CSS is a DRAFT preview only, never evidence of exact Pillow text wrapping.
 */
import { useRef, useState } from 'react'
import {
  FEATURE3_FORMATS, newFeature3History, editFeature3,
  addFeature3Layer, removeFeature3Layer, moveFeature3Layer,
  updateFeature3Layer, undoFeature3, redoFeature3,
  replaceFeature3Image,
} from './feature3-design.mjs'

import { renderFeature3LocalDraft } from './feature3-local-png.mjs'
import { encodeFeature3LocalBackup, decodeFeature3LocalBackup } from './feature3-local-backup.mjs'

const SIZE = { boxSizing: 'border-box', maxWidth: '100%', width: '100%' }
const COLOR = /^#[0-9a-fA-F]{6}$/

export default function Feature3CpuEditor({
  initialDesign, imageMap = {}, context = null, onSaveDraft = null, disabled = false,
}) {
  const [history, setHistory] = useState(() => newFeature3History(initialDesign))
  const current = useRef(history)
  const [selectedId, setSelectedId] = useState(null)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const draft = history.present
  const layer = draft.layers.find(x => x.id === selectedId)
  const [w, h] = FEATURE3_FORMATS[draft.format]
  const imageIds = Object.keys(imageMap).filter(id =>
    /^[a-zA-Z0-9_-]{1,100}$/.test(id) &&
    imageMap[id]?.complete && imageMap[id]?.naturalWidth > 0 &&
    imageMap[id]?.naturalHeight > 0)
  const [imageChoice, setImageChoice] = useState('')
  const mutate = fn => {
    if (disabled) return
    try {
      const updated = fn(current.current)
      current.current = updated
      setHistory(updated)
      setMessage('')
    } catch (error) {
      setMessage(error.message || 'Invalid poster edit')
    }
  }
  const patch = values => mutate(state =>
    updateFeature3Layer(state, selectedId, values))
  const importDraft = async event => {
    const file = event.target.files?.[0]
    if (!file) return
    try {
      if (file.size < 1 || file.size > 25000) throw Error('Invalid local file size')
      const parsed = decodeFeature3LocalBackup(await file.text(),
        context, imageIds)
      const restored = newFeature3History(parsed)
      current.current = restored
      setHistory(restored)
      setSelectedId(null)
      setMessage('Local editable design restored; cloud save is separate.')
    } catch {
      setMessage('Local draft rejected; check format, shop and current image rights.')
    } finally {
      event.target.value = ''
    }
  }
  const downloadDraftPng = () => {
    if (disabled) return
    try {
      // The browser performs exactly one bounded 1080px local render;
      // nothing is posted, uploaded, published or charged to a GPU.
      const local = document.createElement('canvas')
      renderFeature3LocalDraft(local, draft, imageMap)
      if (typeof local.toBlob !== 'function') {
        throw Error('PNG export is unavailable in this browser')
      }
      local.toBlob(blob => {
        if (!blob || blob.type !== 'image/png') {
          setMessage('Browser could not encode the local draft PNG.')
          return
        }
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = 'retailgrowth-unreviewed-local-draft.png'
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.setTimeout(() => URL.revokeObjectURL(url), 1000)
        setMessage('Downloaded local draft PNG. This is not an approved cloud poster.')
      }, 'image/png')
    } catch (error) {
      setMessage(error.message || 'Local draft PNG could not be generated.')
    }
  }

  const exportDraft = () => {
    let data
    try {
      data = encodeFeature3LocalBackup(draft, context)
    } catch {
      setMessage('Verified shop/campaign/day required to export a local backup.')
      return
    }
    const url = URL.createObjectURL(new Blob([data],
      { type: 'application/json' }))
    const a = document.createElement('a')
    a.href = url
    a.download = 'retailgrowth-poster-day-bound-local-v2.json'
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  }
  const save = async () => {
    if (!onSaveDraft || saving || disabled) return
    setSaving(true)
    try {
      await onSaveDraft(draft)
      setMessage('Authenticated save callback accepted the draft.')
    } catch {
      setMessage('Cloud save failed; your unsaved local design remains available.')
    } finally {
      setSaving(false)
    }
  }
  const pct = n => (n * 100) + '%'
  const imageContent = x => {
    const image = imageMap[x.asset_id]
    if (!imageIds.includes(x.asset_id)) {
      return <span style={{fontSize:11}}>Private image unavailable</span>
    }
    // No user URL is accepted; src originates from the host's previously
    // authorized HTMLImageElement and never from design JSON.
    return <img src={image.currentSrc || image.src} alt="Authorized product"
      draggable={false} style={{width:'100%',height:'100%',
        objectFit:x.id==='logo'?'contain':'cover'}} />
  }

  return <section aria-label="CPU poster editor" style={{display:'grid',gap:12}}>
    <p role="note">No-GPU editor. This browser layout is an approximation.
      Review the exact server-rendered PNG before approval or publishing.</p>
    <div style={{display:'grid',
      gridTemplateColumns:'repeat(auto-fit,minmax(min(100%,280px),1fr))',gap:16}}>
      <div>
        <div aria-label="Editable poster preview" style={{
          aspectRatio:`${w} / ${h}`,position:'relative',width:'100%',
          maxWidth:460,background:draft.background,overflow:'hidden',
          border:'1px solid #999',
        }}>
          {draft.layers.map(item => <div key={item.id}
            role="button" tabIndex={0}
            aria-label={`Edit ${item.id} layer`}
            onClick={() => setSelectedId(item.id)}
            onKeyDown={e => {
              if(e.key==='Enter'||e.key===' '){e.preventDefault();setSelectedId(item.id)}
            }}
            style={{position:'absolute',left:pct(item.x),top:pct(item.y),
              width:pct(item.w),height:pct(item.h),overflow:'hidden',
              outline:selectedId===item.id?'2px dashed #111':'none',
              cursor:'pointer',color:item.color,
              background:item.type==='rect'?item.color:'transparent',
              fontWeight:item.bold?'bold':'normal',
              fontSize:item.type==='text'? `${item.font_size / 1080 * 410}px` :undefined,
              lineHeight:1.12,overflowWrap:'anywhere'}}>
            {item.type==='text'?item.text:
              item.type==='image'?imageContent(item):null}
          </div>)}
        </div>
      </div>
      <div style={{display:'grid',gap:10,alignContent:'start'}}>
        <div style={{display:'flex',gap:6,flexWrap:'wrap'}}>
          <button type="button" disabled={disabled||!history.past.length}
            onClick={() => mutate(undoFeature3)}>Undo</button>
          <button type="button" disabled={disabled||!history.future.length}
            onClick={() => mutate(redoFeature3)}>Redo</button>
          <button type="button" disabled={disabled||draft.layers.length>=24}
            onClick={() => mutate(x => addFeature3Layer(x,'text'))}>Add text</button>
          <button type="button" disabled={disabled||draft.layers.length>=24}
            onClick={() => mutate(x => addFeature3Layer(x,'rect'))}>Add badge</button>
        </div>
        <label>Selected layer
          <select style={SIZE} value={selectedId||''}
            onChange={e=>setSelectedId(e.target.value||null)}>
            <option value="">Choose a layer</option>
            {draft.layers.map(x=><option key={x.id} value={x.id}>{x.id}</option>)}
          </select>
        </label>
        {layer && <>
          <div style={{display:'flex',gap:6,flexWrap:'wrap'}}>
            <button type="button" disabled={disabled}
              onClick={()=>mutate(x=>moveFeature3Layer(x,selectedId,-1))}>Move back</button>
            <button type="button" disabled={disabled}
              onClick={()=>mutate(x=>moveFeature3Layer(x,selectedId,1))}>Move forward</button>
            <button type="button" disabled={disabled||draft.layers.length<=1}
              onClick={()=>{
                mutate(x=>removeFeature3Layer(x,selectedId))
                setSelectedId(null)
              }}>Remove</button>
          </div>
          {layer.type==='text' && <>
            <label>Text<input style={SIZE} value={layer.text} disabled={disabled}
              maxLength={160} onChange={e=>patch({text:e.target.value})}/></label>
            <label>Font size<input type="number" style={SIZE} min={12} max={150}
              disabled={disabled} value={layer.font_size}
              onChange={e=>patch({font_size:Math.max(12,Math.min(150,Number(e.target.value)||12))})}/></label>
          </>}
          {(layer.type==='rect'||layer.type==='text') &&
            <label>Layer colour<input type="color" value={layer.color} disabled={disabled}
              onChange={e=>{if(COLOR.test(e.target.value))patch({color:e.target.value})}}/></label>}
          {layer.type==='image' &&
            <label>Replacement authorized photo<select style={SIZE}
              disabled={disabled} value={imageChoice}
              onChange={e=>setImageChoice(e.target.value)}>
              <option value="">Choose registered image</option>
              {imageIds.map(id=><option key={id} value={id}>{id.slice(0,8)}</option>)}
            </select></label>}
          {layer.type==='image' && <button type="button"
            disabled={disabled||!imageChoice}
            onClick={()=>mutate(x=>replaceFeature3Image(x,selectedId,imageChoice,imageIds))}>
            Replace photo
          </button>}
          <div style={{display:'grid',
            gridTemplateColumns:'repeat(2,minmax(0,1fr))',gap:8}}>
            {['x','y','w','h'].map(key => <label key={key}>
              {({x:'Left',y:'Top',w:'Width',h:'Height'})[key]} (%)
              <input style={SIZE} type="number" min={key==='w'||key==='h'?1:0}
                max={100} step={1} disabled={disabled}
                value={Math.round(layer[key]*100)}
                onChange={e=>{
                  const number=Number(e.target.value)/100
                  if(Number.isFinite(number))patch({[key]:number})
                }}/>
            </label>)}
          </div>
        </>}
        <label>Canvas background
          <input type="color" disabled={disabled} value={draft.background}
            onChange={e=>mutate(x=>editFeature3(x,d=>({...d,background:e.target.value})))}/>
        </label>
        <button type="button" disabled={disabled||!onSaveDraft||saving}
          onClick={save}>{saving?'Saving…':'Save private draft'}</button>
        <button type="button" disabled={disabled} onClick={downloadDraftPng}>
          Download local draft PNG (unreviewed)
        </button>
        <button type="button" disabled={disabled} onClick={exportDraft}>Download day-bound editable JSON</button>
        <label>Reopen local JSON
          <input type="file" accept="application/json,.json" disabled={disabled}
            onChange={importDraft}/>
        </label>
        {!onSaveDraft && <p>No authenticated v2 save API is connected.
          Download JSON to retain this local design.</p>}
        {message && <p role="status">{message}</p>}
      </div>
    </div>
  </section>
}
