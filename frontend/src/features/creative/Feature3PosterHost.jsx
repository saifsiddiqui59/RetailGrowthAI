/** Feature3 opt-in authenticated host, OFF unless independently released.
 * Existing Part1 PosterStudio remains authoritative. Never loads model media
 * without a user action, signed JWT, same-shop RLS media checks and private
 * Storage binary validation. No public images, inferred rights or paid GPU.
 */
import { useEffect, useMemo, useRef, useState } from 'react'
import PosterStudio from './PosterStudio.jsx'
import { createFeature3Api } from './feature3-api.mjs'

const enabled = import.meta.env?.VITE_FEATURE3_V2_ENABLED === 'true'
const MAX_MODEL_PREVIEWS = 5
const IMAGE_TYPES = new Set(['image/png','image/jpeg','image/webp'])

function decodeObjectUrl(url) {
  return new Promise((resolve, reject) => {
    const picture = new Image()
    picture.onload = () => picture.naturalWidth > 0 && picture.naturalHeight > 0
      ? resolve(picture) : reject(Error('Invalid private image dimensions'))
    picture.onerror = () => reject(Error('Private image decode failed'))
    picture.src = url
  })
}

export default function Feature3PosterHost({ client, shopId, ...posterProps }) {
  const api = useMemo(() => enabled && client?.configured &&
    import.meta.env?.VITE_CAMPAIGN_API_BASE_URL
    ? createFeature3Api({
        baseUrl: import.meta.env.VITE_CAMPAIGN_API_BASE_URL,
        tokenProvider: () => client.getAccessToken(),
      }) : null, [client])
  const [models, setModels] = useState([])
  const [imageMap, setImageMap] = useState({})
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const nonce = useRef(0)
  const urls = useRef([])
  const release = () => {
    for (const url of urls.current) URL.revokeObjectURL(url)
    urls.current = []
  }
  useEffect(() => {
    // Active shop and component lifetime govern all previously decoded pixels.
    return () => { nonce.current += 1; release() }
  }, [shopId])

  async function loadPrivateModels() {
    if (!api || !shopId || busy) return
    const request = ++nonce.current
    release()
    setModels([])
    setImageMap({})
    setMessage('')
    setBusy(true)
    const opened = []
    try {
      const rows = await api.listModels(shopId)
      const accepted = []
      const loaded = {}
      for (const model of rows.slice(0, MAX_MODEL_PREVIEWS)) {
        if (request !== nonce.current) break
        try {
          const result = await client.downloadPrivateImage(shopId, model.media_asset_id)
          if (!result?.blob || !IMAGE_TYPES.has(result.blob.type) ||
              result.blob.size < 100 || result.blob.size > 25*1024*1024) continue
          const local = URL.createObjectURL(result.blob)
          opened.push(local)
          const picture = await decodeObjectUrl(local)
          if (request !== nonce.current) break
          loaded[model.media_asset_id] = picture
          accepted.push(model)
        } catch {
          // An absent, revoked or non-owned private image is never displayed.
        }
      }
      if (request !== nonce.current) return
      urls.current = opened
      setModels(accepted)
      setImageMap(loaded)
      setMessage(accepted.length
        ? 'Private shop models loaded for local preview. Server approval and rights are rechecked on save.'
        : 'No currently accessible approved shop models. Other shops’ media remains private.')
    } catch {
      if (request === nonce.current)
        setMessage('Private model library unavailable; existing poster tools remain usable.')
    } finally {
      if (request !== nonce.current) {
        opened.forEach(url => URL.revokeObjectURL(url))
      } else {
        setBusy(false)
      }
    }
  }

  if (!api || !shopId) return <PosterStudio {...posterProps}/>
  return <section aria-label="Feature3 private poster workspace">
    <div style={{display:'flex',flexWrap:'wrap',alignItems:'center',gap:8}}>
      <button type="button" disabled={busy} onClick={loadPrivateModels}>
        {busy ? 'Loading private models…' : 'Load my approved AI model library'}
      </button>
      <small>No paid AI or background downloads. Limited to five private previews.</small>
    </div>
    {message && <p role="status">{message}</p>}
    <PosterStudio {...posterProps} feature3Api={api}
      approvedModels={models} authenticatedModelImageMap={imageMap}/>
  </section>
}
