/** Read-only client-side representation of trusted-shaped poster metadata.
 * No remote media fetch, public image link, upload, or review mutation.
 */
import {FEATURE3_FORMATS} from './feature3-design.mjs'

export default function Feature3ReadOnlyReview({snapshot}) {
  if(!snapshot || !Object.hasOwn(FEATURE3_FORMATS,snapshot.format) ||
     !Array.isArray(snapshot.layers))return null
  const [width,height]=FEATURE3_FORMATS[snapshot.format]
  const scale=320/width
  const base={position:'absolute',overflow:'hidden',boxSizing:'border-box'}
  const place=layer=>({
    ...base,left:(layer.x*100)+'%',top:(layer.y*100)+'%',
    width:(layer.w*100)+'%',height:(layer.h*100)+'%',
  })
  return <figure aria-label="Read-only poster layout preview">
    <div style={{width:'min(100%,320px)',aspectRatio:String(width)+' / '+String(height),
      position:'relative',overflow:'hidden',background:snapshot.background,
      border:'1px solid #aaa'}} role="img"
      aria-label="Offline layout approximation, not a validated poster output">
      {snapshot.layers.map(layer=>
        layer.type==='rect'
          ? <div key={layer.id} style={{...place(layer),background:layer.color}}/>
          : layer.type==='text'
            ? <div key={layer.id} style={{...place(layer),color:layer.color,
                fontWeight:layer.bold?700:400,
                fontSize:Math.max(10,Math.round(layer.fontSize*scale)),
                lineHeight:1.2,overflowWrap:'anywhere'}}>{layer.text}</div>
            : <div key={layer.id} style={{...place(layer),
                background:'#ddd',color:'#333',fontSize:11,
                display:'flex',alignItems:'center',justifyContent:'center',
                textAlign:'center',padding:4}}>
                {layer.mediaLabel} (image withheld)
              </div>
      )}
    </div>
    <figcaption>
      Poster revision {snapshot.revision} · {snapshot.status} (server status only).
      Read-only metadata preview; no image download, commercial rights,
      publishing approval or pixel-perfect server render.
    </figcaption>
  </figure>
}
