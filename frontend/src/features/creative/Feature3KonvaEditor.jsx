/** Feature #3 isolated React Konva editor.
 * Integration requires coordinator-approved react-konva/konva dependency pins,
 * a reviewed v2 save API and Pillow browser/server visual parity test.
 * This component deliberately is NOT mounted in the live Part 1 PosterStudio.
 * imageMap must contain *already authorized* HTMLImageElements from private
 * shop media; this module never fetches URLs or accepts image src strings.
 */
import { useEffect, useRef, useState } from 'react'
import { Stage, Layer, Group, Rect, Text, Image as KonvaImage, Transformer } from 'react-konva'
import {
  FEATURE3_FORMATS, newFeature3History, editFeature3, updateFeature3Layer,
  moveFeature3Layer, undoFeature3, redoFeature3,
  addFeature3Layer, removeFeature3Layer, replaceFeature3Image, validateFeature3Design,
} from './feature3-design.mjs'

export default function Feature3KonvaEditor({
  initialDesign, imageMap = {}, onSaveDraft = null,
}) {
  const [history, setHistory] = useState(() => newFeature3History(initialDesign))
  const [selected, setSelected] = useState(null)
  const [viewport, setViewport] = useState(480)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [imageChoice, setImageChoice] = useState('')
  const authorizedIds = Object.keys(imageMap).filter(key =>
    /^[a-zA-Z0-9_-]{1,100}$/.test(key) &&
    imageMap[key]?.complete && imageMap[key]?.naturalWidth > 0 &&
    imageMap[key]?.naturalHeight > 0)

  const hostRef = useRef(null)
  const refs = useRef({})
  const transformerRef = useRef(null)
  const design = history.present
  const [width, height] = FEATURE3_FORMATS[design.format]
  const scale = Math.min(viewport / width, 1)
  const active = design.layers.find(layer => layer.id === selected)

  useEffect(() => {
    const host = hostRef.current
    if (!host) return
    const observer = new ResizeObserver(entries => {
      setViewport(Math.max(220, Math.floor(entries[0].contentRect.width)))
    })
    observer.observe(host)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    const target = refs.current[selected]
    if (!transformerRef.current) return
    transformerRef.current.nodes(target ? [target] : [])
    transformerRef.current.getLayer()?.batchDraw()
  }, [selected, design])

  const apply = mutation => {
    try {
      setHistory(mutation(history))
      setError('')
    } catch (problem) {
      setError(problem.message || 'Poster change was rejected')
    }
  }
  const edit = callback => apply(current => editFeature3(current, callback))
  const setLayer = (id, patch) => apply(current =>
    updateFeature3Layer(current, id, patch))

  function downloadLocalVersion() {
    // Optional local backup, not cloud persistence or approval.
    const blob = new Blob([JSON.stringify(design, null, 2)], {type:'application/json'})
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'retailgrowth-poster-local-design-v2.json'
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  async function restoreLocalVersion(event) {
    const file = event.target.files?.[0]
    if (!file) return
    if (file.size < 1 || file.size > 25_000 || file.type &&
        !['application/json', 'text/plain'].includes(file.type)) {
      setError('Choose a local poster JSON design under 25 KB')
      return
    }
    try {
      const parsed = validateFeature3Design(JSON.parse(await file.text()))
      if (parsed.shop_id !== initialDesign.shop_id ||
          parsed.layers.some(layer => layer.type === 'image' &&
            !authorizedIds.includes(layer.asset_id))) {
        throw Error('Draft tenant or image authorization has changed')
      }
      setHistory(newFeature3History(parsed))
      setSelected(null)
      setError('')
    } catch (problem) {
      setError('Could not verify this local design for the selected shop')
    } finally {
      event.target.value = ''
    }
  }

  const place = (layer, node) => {
    const normalized = {
      x: Math.max(0, Math.min(1 - layer.w, node.x() / (width * scale))),
      y: Math.max(0, Math.min(1 - layer.h, node.y() / (height * scale))),
    }
    setLayer(layer.id, normalized)
  }
  const resize = (layer, node) => {
    const x = Math.max(0, Math.min(.98, node.x() / (width * scale)))
    const y = Math.max(0, Math.min(.98, node.y() / (height * scale)))
    const w = Math.max(.01, Math.min(1 - x, layer.w * node.scaleX()))
    const h = Math.max(.01, Math.min(1 - y, layer.h * node.scaleY()))
    node.scaleX(1)
    node.scaleY(1)
    setLayer(layer.id, { x, y, w, h })
  }
  const save = async () => {
    if (typeof onSaveDraft !== 'function' || saving) return
    setSaving(true)
    setError('')
    try {
      // Caller owns authenticated v2 draft persistence; never fall back to
      // existing v1 schema by silently dropping editable layer information.
      await onSaveDraft(design)
    } catch (e) {
      setError('Could not save this versioned design.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section aria-label="Advanced versioned poster editor">
      <p role="note">Preview only: server-rendered artwork must be checked before approval or publishing.</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(min(100%,280px),1fr))', gap: 16 }}>
        <div ref={hostRef} style={{ width: '100%', maxWidth: 520, overflow: 'hidden' }}>
          <Stage width={width * scale} height={height * scale}
            onMouseDown={e => { if (e.target === e.target.getStage()) setSelected(null) }}
            onTouchStart={e => { if (e.target === e.target.getStage()) setSelected(null) }}>
            <Layer>
              <Rect x={0} y={0} width={width * scale} height={height * scale}
                fill={design.background} listening={false}/>
              {design.layers.map(layer => {
                const pos = {
                  x: layer.x * width * scale, y: layer.y * height * scale,
                  width: layer.w * width * scale, height: layer.h * height * scale,
                }
                const props = {
                  key: layer.id, ...pos, draggable: true,
                  ref: node => { refs.current[layer.id] = node },
                  onClick: () => setSelected(layer.id),
                  onTap: () => setSelected(layer.id),
                  onDragEnd: e => place(layer, e.target),
                  onTransformEnd: e => resize(layer, e.target),
                }
                if (layer.type === 'rect')
                  return <Rect {...props} fill={layer.color}/>
                if (layer.type === 'text')
                  return <Text {...props} text={layer.text} fill={layer.color}
                    fontSize={layer.font_size * scale}
                    fontStyle={layer.bold ? 'bold' : 'normal'} wrap="word"/>
                // Never construct or load a URL here. A missing auth-scoped
                // image is intentionally invisible rather than fetched.
                const image = imageMap[layer.asset_id]
                if (!authorizedIds.includes(layer.asset_id)) return null
                // Use the SAME center-cover crop rule as Pillow ImageOps.fit,
                // rather than stretching retail products out of proportion.
                if (layer.id === 'logo') {
                  const fit = Math.min(pos.width / image.naturalWidth,
                                       pos.height / image.naturalHeight)
                  const innerW = image.naturalWidth * fit
                  const innerH = image.naturalHeight * fit
                  return <Group {...props}>
                    <Rect x={0} y={0} width={pos.width} height={pos.height}
                      opacity={0} listening={false}/>
                    <KonvaImage image={image} width={innerW} height={innerH}
                      x={(pos.width - innerW) / 2} y={(pos.height - innerH) / 2}/>
                  </Group>
                }
                const ratio = Math.max(pos.width / image.naturalWidth,
                                       pos.height / image.naturalHeight)
                const cropWidth = pos.width / ratio
                const cropHeight = pos.height / ratio
                return <KonvaImage {...props} image={image}
                  cropX={(image.naturalWidth - cropWidth) / 2}
                  cropY={(image.naturalHeight - cropHeight) / 2}
                  cropWidth={cropWidth} cropHeight={cropHeight}/>
              })}
              <Transformer ref={transformerRef} rotateEnabled={false}
                flipEnabled={false} keepRatio={false}
                boundBoxFunc={(oldBox, newBox) =>
                  newBox.width < 12 || newBox.height < 12 ? oldBox : newBox}/>
            </Layer>
          </Stage>
        </div>
        <div style={{ display: 'grid', alignContent: 'start', gap: 12 }}>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button type="button" onClick={() => {setHistory(h => undoFeature3(h));setError('')}}
              disabled={!history.past.length}>Undo</button>
            <button type="button" onClick={() => {setHistory(h => redoFeature3(h));setError('')}}
              disabled={!history.future.length}>Redo</button>
            <button type="button" onClick={() => apply(h => moveFeature3Layer(h, selected, 1))}
              disabled={!active}>Bring forward</button>
            <button type="button" onClick={() => apply(h => moveFeature3Layer(h, selected, -1))}
              disabled={!active}>Send backward</button>
            <button type="button" onClick={() => {
              apply(h => removeFeature3Layer(h, selected)); setSelected(null)
            }} disabled={!active || design.layers.length <= 1}>Remove layer</button>
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button type="button" disabled={design.layers.length >= 24}
              onClick={() => apply(h => addFeature3Layer(h, 'text'))}>Add text</button>
            <button type="button" disabled={design.layers.length >= 24}
              onClick={() => apply(h => addFeature3Layer(h, 'rect'))}>Add promo badge</button>
          </div>
          <label>Approved product image
            <select value={imageChoice} onChange={e => setImageChoice(e.target.value)}>
              <option value="">Select authorized shop media</option>
              {authorizedIds.map(id =>
                <option key={id} value={id}>{id.slice(0, 8)} · Registered</option>)}
            </select>
          </label>
          <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
            <button type="button" disabled={!imageChoice || design.layers.length >= 24}
              onClick={() => apply(h => addFeature3Layer(h, 'image',
                imageChoice, authorizedIds))}>Add photo</button>
            <button type="button"
              disabled={!imageChoice || active?.type !== 'image'}
              onClick={() => apply(h => replaceFeature3Image(
                h, selected, imageChoice, authorizedIds))}>Replace selected photo</button>
          </div>
          <label>Selected layer
            <select value={selected || ''} onChange={e => setSelected(e.target.value || null)}>
              <option value="">None</option>
              {design.layers.map(layer =>
                <option key={layer.id} value={layer.id}>{layer.id} ({layer.type})</option>)}
            </select>
          </label>
          {active?.type === 'text' && <>
            <label>Text
              <textarea value={active.text} maxLength={160}
                onChange={e => setLayer(active.id, { text: e.target.value })}/>
            </label>
            <label>Font size
              <input type="number" min="12" max="150" value={active.font_size}
                onChange={e => setLayer(active.id, {
                  font_size: Math.max(12, Math.min(150, Number(e.target.value) || 12)),
                })}/>
            </label>
          </>}
          {active && (active.type === 'text' || active.type === 'rect') && (
            <label>Layer color
              <input type="color" value={active.color}
                onChange={e => setLayer(active.id, { color: e.target.value })}/>
            </label>
          )}
          {active?.type === 'image' && <p>Replace images through authorized shop-media selection in the host workspace.</p>}
          <label>Canvas background
            <input type="color" value={design.background}
              onChange={e => edit(doc => ({...doc, background: e.target.value}))}/>
          </label>
          <button type="button" onClick={save} disabled={!onSaveDraft || saving}>
            {saving ? 'Saving…' : 'Save private draft'}
          </button>
          <button type="button" onClick={downloadLocalVersion}>
            Download local editable JSON
          </button>
          <label>Reopen local draft
            <input type="file" accept=".json,application/json" onChange={restoreLocalVersion}/>
          </label>
          {!onSaveDraft && <p>Local draft only. Authenticated versioned cloud save requires
            the coordinator-owned v2 API; existing v1 cloud drafts are unchanged.</p>}
          {error && <p role="alert">{error}</p>}
        </div>
      </div>
    </section>
  )
}
