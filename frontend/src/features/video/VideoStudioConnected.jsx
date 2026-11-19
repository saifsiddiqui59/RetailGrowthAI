import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import VideoStudio from './VideoStudio.jsx'
import { canonicalVideoId, createVideoTransport, privateMediaPreviewUrl } from './video-transport.mjs'

// Feature #4-owned authenticated bridge, NOT a mounted application route.
// Feature #1/coordinator must supply a selected RLS-authorized shop,
// persistent campaign and approved-script revision, AND register the additive
// backend routes before setting enabled=true. Never adapt old v1 render jobs.
// The user must see "integration pending" until all those gates are met.
export default function VideoStudioConnected({
  shopId, campaignId, approvalId, mediaAssets = [], musicAssets = [],
  enabled = false, routes = null, pollMs = 3500, creativeDirection = null,
}) {
  const { client, user, configured, recoveryMode } = useRetailAuth()
  const [job, setJob] = useState(null)
  const [signedUrl, setSignedUrl] = useState(null)
  const [error, setError] = useState('')
  const context = useRef(0)
  const routeReady = enabled === true && Boolean(configured && user && !recoveryMode && routes &&
    typeof shopId === 'string' && typeof campaignId === 'string' &&
    typeof approvalId === 'string')
  // A selected shop must be an RLS-verified membership from Feature #1, not
  // a browser URL parameter. The server rechecks membership for every action.
  const api = useMemo(() => createVideoTransport({
    enabled: routeReady,
    baseUrl: import.meta.env?.VITE_CAMPAIGN_API_BASE_URL,
    tokenProvider: () => client.accessToken(),
    supabaseOrigin: import.meta.env?.VITE_SUPABASE_URL,
    routes,
  }), [routeReady, client, routes])
  // The integration bridge is stricter than the local draft editor:
  // never even offer an asset belonging to a different selected shop.
  const shopMedia = useMemo(() => (Array.isArray(mediaAssets) ? mediaAssets : [])
    .filter(asset => asset?.shop_id === shopId && asset?.authorized === true)
    .map(asset => {
      // The source image/movie is displayed only when it has a validated,
      // per-shop Supabase Storage signed URL. Invalid external URLs are never
      // rendered as <img> or <video>. Server retains actual media authority.
      let preview_url
      try {
        preview_url = privateMediaPreviewUrl(
          asset.preview_url, import.meta.env?.VITE_SUPABASE_URL, shopId)
      } catch { preview_url = null }
      return { ...asset, preview_url }
    }),
  [mediaAssets, shopId])
  const shopMusic = useMemo(() => (Array.isArray(musicAssets) ? musicAssets : [])
    .filter(asset => asset?.shop_id === shopId && asset?.authorized === true),
  [musicAssets, shopId])
  const shopKey = shopId + ':' + campaignId + ':' + (user?.id || '')
  useEffect(() => {
    context.current += 1
    setJob(null)
    setSignedUrl(null)
    setError('')
  }, [shopKey, api])

  const submit = useCallback(async (draft) => {
    if (!api) throw Error('Coordinator-approved Video Studio API is not connected')
    const epoch = context.current
    const receipt = await api.create({ shopId, campaignId, approvalId, draft })
    if (epoch !== context.current) throw Error('Business changed while render was submitted. Check that business’s job history.')
    setSignedUrl(null)
    setError('')
    setJob(receipt)
    // An idempotent create may return an already-SUCCEEDED job. Obtain its
    // current tenant-private signed URL without replaying the POST.
    if (receipt.status === 'SUCCEEDED') {
      try {
        const url = await api.download({ jobId: receipt.job_id, shopId })
        if (epoch === context.current) setSignedUrl(url)
      } catch {
        if (epoch === context.current) {
          setError('Completed render found, but the private download could not be renewed.')
        }
      }
    }
    return receipt
  }, [api, shopId, campaignId, approvalId])

  // Poll only GET, never POST. The existing Azure #249 ingress issue can time
  // out even healthy requests; do not automatically resubmit an uncertain job.
  useEffect(() => {
    if (!api || !job?.job_id || job.shop_id !== shopId ||
        ['SUCCEEDED', 'FAILED'].includes(job.status)) return
    const epoch = context.current
    let cancelled = false
    let timer = null
    let activeController = null
    let consecutiveFailures = 0
    const delay = Number.isInteger(pollMs) && pollMs >= 1000 && pollMs <= 30000 ? pollMs : 3500
    async function refresh() {
      activeController = new AbortController()
      try {
        const updated = await api.status({ jobId: job.job_id, shopId, signal: activeController.signal })
        if (cancelled || context.current !== epoch) return
        consecutiveFailures = 0
        setJob(updated)
        setError('')
        if (updated.status === 'SUCCEEDED') {
          // A new signed URL must be requested using the CURRENT JWT and job.
          const url = await api.download({ jobId: job.job_id, shopId, signal: activeController.signal })
          if (!cancelled && context.current === epoch) setSignedUrl(url)
          return
        }
        if (updated.status === 'FAILED') {
          setError('Video render failed. Check the approved content and retry through job history.')
          return
        }
      } catch (exc) {
        if (cancelled || context.current !== epoch) return
        consecutiveFailures += 1
        if (consecutiveFailures >= 3) {
          setError('Render status could not be verified. Do not submit again; check this job in your history.')
          return
        }
        setError('Render is still pending. Status service is temporarily unavailable.')
      }
      if (!cancelled) timer = setTimeout(refresh, delay)
    }
    timer = setTimeout(refresh, delay)
    return () => {
      cancelled = true
      if (timer !== null) clearTimeout(timer)
      activeController?.abort()
    }
  }, [api, job?.job_id, shopId, pollMs])
  // Do not keep or download stale signed URLs after the session/shop changes.
  const ready = job?.shop_id === shopId && job?.status === 'SUCCEEDED'
  const download = useCallback(async () => {
    if (!api || !ready) return
    const epoch = context.current
    try {
      const url = await api.download({ jobId: job.job_id, shopId })
      if (epoch !== context.current) return
      setSignedUrl(url)
      // Authoritative server-provided, tenant+job-bound HTTPS signed link.
      const link = document.createElement('a')
      link.href = url
      link.download = 'retailgrowthai-' + job.job_id + '.mp4'
      link.rel = 'noopener noreferrer'
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch {
      if (epoch === context.current) setError('Unable to renew the private video download. Try again after reauthentication.')
    }
  }, [api, job, shopId, ready])

  return (
    <div className="f4-connected-workspace">
      {!api && (
        <p className="f4-guidance" role="status">
          Video Studio backend v2 is not enabled. The editor remains a local storyboard;
          no cloud render, quota charge or private upload is started.
        </p>
      )}
      {error && <p className="f4-issues" role="alert">{error}</p>}
      <VideoStudio key={shopKey} shopId={shopId} creativeDirection={creativeDirection}
        mediaAssets={shopMedia} musicAssets={shopMusic}
        onRender={api ? submit : null} renderStatus={job}
        signedVideoUrl={ready ? signedUrl : null}
        onPrivateDownload={ready ? download : null} />
    </div>
  )
}
