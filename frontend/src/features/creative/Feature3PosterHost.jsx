/** Feature3 opt-in authenticated host. No paid AI, public image loading or
 * cross-shop persistence. A late image fetch must never populate a new shop.
 */
import { cloneElement, useEffect, useMemo, useRef, useState } from 'react'
import { createFeature3Api } from './feature3-api.mjs'
import { scopedFeature3Preview } from './feature3-private-preview.mjs'
import Feature3GeneratedHistory from './Feature3GeneratedHistory.jsx'
import {createFeature3PrivatePNGClient} from './feature3-private-png-client.mjs'

const enabled = import.meta.env?.VITE_FEATURE3_V2_ENABLED === 'true'
const MAX_MODEL_PREVIEWS = 5
const IMAGE_TYPES = new Set(['image/png', 'image/jpeg', 'image/webp'])
const empty = scope => ({scope, models:[], imageMap:{}, busy:false, message:''})

function decodeObjectUrl(url) {
  return new Promise((resolve, reject) => {
    const picture = new Image()
    picture.onload = () => picture.naturalWidth > 0 && picture.naturalHeight > 0
      ? resolve(picture) : reject(Error('Invalid private image dimensions'))
    picture.onerror = () => reject(Error('Private image decode failed'))
    picture.src = url
  })
}

export default function Feature3PosterHost({ client, shopId, children }) {
  const api = useMemo(() => enabled && client?.configured &&
    import.meta.env?.VITE_CAMPAIGN_API_BASE_URL
    ? createFeature3Api({
        baseUrl: import.meta.env.VITE_CAMPAIGN_API_BASE_URL,
        signedStorageOrigin: import.meta.env.VITE_SUPABASE_URL,
        tokenProvider: () => client.getAccessToken(),
      }) : null, [client])
  // Existing signed Storage URLs cannot be instantly revoked. New binary
  // preview is separately gated OFF until the reviewed current-rights
  // private PNG backend endpoint is actually live and accepted.
  const binaryClient=useMemo(()=>enabled &&
    import.meta.env?.VITE_FEATURE3_PRIVATE_BINARY_ENABLED==='true' &&
    client?.configured && import.meta.env?.VITE_CAMPAIGN_API_BASE_URL
    ? createFeature3PrivatePNGClient({
        baseUrl:import.meta.env.VITE_CAMPAIGN_API_BASE_URL,
        tokenProvider:()=>client.getAccessToken(),
      }):null,[client])
  const [preview, setPreview] = useState(() => empty(shopId))
  // Guard on RENDER too: useEffect cleanup happens after the first paint.
  const scoped = scopedFeature3Preview(preview, shopId)
  const nonce = useRef(0)
  const current = useRef({shopId, api})
  current.current = {shopId, api}
  const urls = useRef([])
  const release = () => {
    for (const url of urls.current) URL.revokeObjectURL(url)
    urls.current = []
  }
  useEffect(() => {
    setPreview(empty(shopId))
    return () => { nonce.current += 1; release() }
  }, [shopId, api])

  async function loadPrivateModels() {
    if (!api || !shopId || scoped.busy) return
    const scope = shopId
    const provider = api
    const request = ++nonce.current
    const isCurrent = () => request === nonce.current &&
      current.current.shopId === scope && current.current.api === provider
    release()
    setPreview({...empty(scope), busy:true})
    const opened = []
    try {
      const rows = await api.listModels(scope)
      const accepted = []
      const loaded = {}
      for (const model of rows.slice(0, MAX_MODEL_PREVIEWS)) {
        if (!isCurrent()) break
        // Track each candidate separately: a failed image decode must not
        // leave an unused private object URL alive until the next shop reload.
        let candidateURL = null
        try {
          const result = await client.downloadPrivateImage(scope, model.media_asset_id)
          if (!isCurrent()) break
          if (!result?.blob || !IMAGE_TYPES.has(result.blob.type) ||
              result.blob.size < 100 || result.blob.size > 25*1024*1024) continue
          if (!globalThis.crypto?.subtle || !/^[a-f0-9]{64}$/.test(model.image_sha256)) continue
          const digest = await globalThis.crypto.subtle.digest('SHA-256', await result.blob.arrayBuffer())
          if (!isCurrent()) break
          const fingerprint = Array.from(new Uint8Array(digest), byte =>
            byte.toString(16).padStart(2, '0')).join('')
          if (fingerprint !== model.image_sha256) continue
          candidateURL = URL.createObjectURL(result.blob)
          opened.push(candidateURL)
          const picture = await decodeObjectUrl(candidateURL)
          if (!isCurrent()) break
          loaded[model.media_asset_id] = picture
          accepted.push(model)
        } catch {
          // Absent, corrupt, revoked or non-owned private media is never
          // displayed. Revoke even if decoding failed after URL allocation.
          if (candidateURL !== null) {
            const index = opened.indexOf(candidateURL)
            if (index !== -1) opened.splice(index, 1)
            URL.revokeObjectURL(candidateURL)
          }
        }
      }
      if (!isCurrent()) return
      // The current session exclusively owns these object URLs until cleanup.
      urls.current = opened.slice()
      setPreview({scope, models:accepted, imageMap:loaded, busy:false,
        message:accepted.length
          ? 'Private shop models loaded. Rights are checked again on save.'
          : 'No accessible approved shop models. Other shops’ media remains private.'})
    } catch {
      if (isCurrent()) {
        opened.forEach(url => URL.revokeObjectURL(url))
        setPreview({...empty(scope),
          message:'Private model library unavailable; existing poster tools remain usable.'})
      }
    } finally {
      if (!isCurrent()) opened.forEach(url => URL.revokeObjectURL(url))
    }
  }

  if (!api || !shopId) return children
  return <section aria-label="Feature3 private poster workspace">
    <div style={{display:'flex',flexWrap:'wrap',alignItems:'center',gap:8}}>
      <button type="button" disabled={scoped.busy} onClick={loadPrivateModels}>
        {scoped.busy ? 'Loading private models…' : 'Load my approved AI model library'}
      </button>
      <small>No paid AI or background downloads. Limited to five private previews.</small>
    </div>
    {scoped.message && <p role="status">{scoped.message}</p>}
    <Feature3GeneratedHistory key={shopId} shopId={shopId} api={api}
      binaryClient={binaryClient} />
    {cloneElement(children, {feature3Api:api, approvedModels:scoped.models,
      authenticatedModelImageMap:scoped.imageMap})}
  </section>
}
