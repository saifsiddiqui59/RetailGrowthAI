import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '../../components/ui/button.jsx'
import { Card } from '../../components/ui/card.jsx'
import { createVideoTransport } from './video-transport.mjs'

const REVIEW_ENABLED = import.meta.env?.VITE_FEATURE4_PLAN_REVIEW_ENABLED === 'true'
const ISSUE_ENABLED = import.meta.env?.VITE_FEATURE4_PLAN_ISSUE_ENABLED === 'true'
const CPU_RENDER_ENABLED = import.meta.env?.VITE_FEATURE4_CPU_RENDER_ENABLED === 'true'
const CPU_ROUTES = Object.freeze({
  create: campaign => '/campaigns/' + campaign + '/feature4-renders',
  status: job => '/feature4-render-jobs/' + job,
  download: job => '/feature4-render-jobs/' + job + '/download',
})

// REAL signed source review: no synthetic approval toggles and no generated
// media/sounds/GPU calls. Only an explicit retailer click runs the narrow SQL
// RPC after fetching this business's persisted F2 proposal under RLS.
export default function CreativePlanReview({ client, user, shopId, role }) {
  const [selectedId, setSelectedId] = useState('')
  const [sourceId, setSourceId] = useState('')
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [cpuJob, setCpuJob] = useState(null)
  const [cpuPreview, setCpuPreview] = useState(null)
  const [cpuError, setCpuError] = useState('')
  const cpuApi = useMemo(() => {
    if (!CPU_RENDER_ENABLED || !REVIEW_ENABLED || !user || !shopId) return null
    try {
      return createVideoTransport({
        enabled: true,
        baseUrl: import.meta.env?.VITE_CAMPAIGN_API_BASE_URL,
        tokenProvider: () => client.getAccessToken(),
        supabaseOrigin: import.meta.env?.VITE_SUPABASE_URL,
        routes: CPU_ROUTES,
      })
    } catch { return null }
  }, [client, user?.id, shopId])

  const canReview = role === 'OWNER' || role === 'EDITOR'
  const reviews = useQuery({
    queryKey: ['f4-review', user?.id, shopId],
    queryFn: () => client.listFeature4CreativePlans(shopId),
    enabled: REVIEW_ENABLED && Boolean(user && shopId),
    retry: false, staleTime: 12_000, gcTime: 0,
  })
  const sources = useQuery({
    queryKey: ['f4-saved-days', user?.id, shopId],
    queryFn: () => client.listFeature4SourceDays(shopId),
    enabled: REVIEW_ENABLED && ISSUE_ENABLED && Boolean(user && shopId && canReview),
    retry: false, staleTime: 12_000, gcTime: 0,
  })
  const days = sources.data || []
  const chosen = days.find(day => day.id === sourceId) || days[0] || null
  const plans = reviews.data || []
  const plan = plans.find(item => item.id === selectedId) || plans[0] || null
  const source = plan?.proposal
  const scenes = Array.isArray(source?.scenes) ? source.scenes : []

  async function write(kind) {
    if (!canReview || !plan || working) return
    const shop = shopId
    setWorking(true)
    setError('')
    setNotice('')
    try {
      // Do not retry an ambiguous SQL write, and never mark APPROVED locally.
      const result = kind === 'review'
        ? await client.reviewFeature4CreativePlan(shop, plan.id, plan.proposal_sha256)
        : await client.revokeFeature4CreativePlan(shop, plan.id)
      if (result.shop_id !== shop) throw Error('Business changed during review')
      setNotice(kind === 'review' ? 'Creative approval recorded by your business.' :
        'This creative version was revoked.')
      await reviews.refetch()
    } catch (cause) {
      setError(cause?.message || 'Creative status could not be verified.')
    } finally {
      setWorking(false)
    }
  }
  async function issueSource() {
    if (!chosen || !canReview || working) return
    setWorking(true)
    setError('')
    setNotice('')
    try {
      const result = await client.issueFeature4CreativePlan(
        shopId, chosen.campaign_id, chosen.id)
      setSelectedId(result.plan_id)
      setNotice('Saved campaign storyboard prepared for retailer review.')
      await reviews.refetch()
    } catch (cause) {
      setError(cause?.message || 'Unable to confirm creative proposal; check plan history.')
    } finally {
      setWorking(false)
    }
  }

  // Explicit recovery is GET-only. A timed-out POST can have spent quota;
  // never assume a failed HTTP acknowledgement means the job was absent.
  async function recoverCpuRender() {
    if (!cpuApi || !canReview || !plan || plan.state !== 'APPROVED' ||
        typeof plan.review_sha256 !== 'string' || working) return
    setWorking(true)
    setCpuError('')
    setCpuPreview(null)
    setNotice('')
    try {
      const existing = await client.findFeature4CpuRenderJob(
        shopId, plan.id, plan.review_sha256)
      if (!existing || existing.campaign_id !== plan.campaign_id) {
        if (existing) throw Error('Existing job does not match approved campaign')
        setCpuJob(null)
        setNotice('No confirmed job exists for this approved creative plan.')
        return
      }
      const verified = await cpuApi.status({ jobId: existing.job_id, shopId })
      setCpuJob({ ...verified, planId: plan.id })
      setNotice('Existing private CPU render recovered without a new submission.')
      if (verified.status === 'SUCCEEDED') {
        try {
          setCpuPreview(await cpuApi.download({ jobId: existing.job_id, shopId }))
        } catch {
          setCpuError('Render recovered; private preview link could not be renewed.')
        }
      }
    } catch {
      setCpuError('Existing job could not be verified. Do not resubmit until history is available.')
    } finally {
      setWorking(false)
    }
  }

  async function submitCpuRender() {
    if (!cpuApi || !canReview || !plan || plan.state !== 'APPROVED' ||
        working || typeof plan.review_sha256 !== 'string') return
    setWorking(true)
    setCpuError('')
    setCpuPreview(null)
    try {
      const response = await cpuApi.createReviewedCpu({
        shopId, campaignId: plan.campaign_id, planId: plan.id,
        reviewHash: plan.review_sha256,
      })
      setCpuJob({ ...response, planId: plan.id })
      setNotice('CPU render request confirmed by the server; status is private.')
    } catch (cause) {
      // Do NOT POST again automatically after an uncertain network response.
      setCpuError(cause?.message || 'Render submission unconfirmed. Check your job status.')
    } finally {
      setWorking(false)
    }
  }

  useEffect(() => {
    if (!cpuApi || !cpuJob || cpuJob.shop_id !== shopId ||
        cpuJob.planId !== plan?.id || plan?.state !== 'APPROVED' ||
        ['SUCCEEDED', 'FAILED'].includes(cpuJob.status)) return
    let cancel = false
    let timer = null
    let failures = 0
    const jobId = cpuJob.job_id
    const currentPlan = cpuJob.planId
    async function refresh() {
      try {
        const verified = await cpuApi.status({ jobId, shopId })
        if (cancel) return
        failures = 0
        setCpuJob({ ...verified, planId: currentPlan })
        if (verified.status === 'SUCCEEDED') {
          const url = await cpuApi.download({ jobId, shopId })
          if (!cancel) setCpuPreview(url)
          return
        }
        if (verified.status === 'FAILED') {
          setCpuError('Video rendering failed; check the private job status.')
          return
        }
      } catch {
        if (cancel) return
        failures += 1
        if (failures >= 3) {
          setCpuError('Unable to confirm this render. Check history before requesting another.')
          return
        }
      }
      if (!cancel) timer = setTimeout(refresh, 3500)
    }
    timer = setTimeout(refresh, 3500)
    return () => { cancel = true; if (timer !== null) clearTimeout(timer) }
  }, [cpuApi, cpuJob?.job_id, cpuJob?.planId, cpuJob?.status,
      plan?.id, plan?.state, shopId])

  async function downloadCpu() {
    if (!cpuApi || !cpuJob || cpuJob.shop_id !== shopId ||
        cpuJob.planId !== plan?.id || cpuJob.status !== 'SUCCEEDED' ||
        plan?.state !== 'APPROVED') return
    try {
      const signed = await cpuApi.download({ jobId: cpuJob.job_id, shopId })
      setCpuPreview(signed)
      const link = document.createElement('a')
      link.href = signed
      link.download = 'retailgrowthai-' + cpuJob.job_id + '.mp4'
      link.rel = 'noopener noreferrer'
      document.body.append(link)
      link.click()
      link.remove()
    } catch {
      setCpuPreview(null)
      setCpuError('Private video could not be renewed; sign in and try again.')
    }
  }

  return <Card className="panel rg-creative-review" aria-label="Saved creative approvals">
    <div className="eyebrow">FEATURE 2 → FEATURE 4</div>
    <h2>Saved Creative Director reviews</h2>
    {!REVIEW_ENABLED && <p role="status">
      Editorial review is not enabled on this installation. We will not
      manufacture an approved plan or submit a video job.
    </p>}
    {REVIEW_ENABLED && !shopId && <p role="status">
      Select a verified business to review its creative plans.
    </p>}
    {REVIEW_ENABLED && ISSUE_ENABLED && shopId && canReview && <div
      className="rg-f4-source-issue" aria-label="Saved campaign to Creative Director">
      <h3>Prepare review from a saved campaign</h3>
      {sources.isError && <p role="alert">Saved campaign days are unavailable.
        <Button variant="outline" onClick={() => sources.refetch()}>Retry read</Button>
      </p>}
      {sources.isSuccess && !days.length && <p role="status">
        No current 30-second draft Reel day is available for this shop.
      </p>}
      {chosen && <>
        <label>Saved campaign day
          <select value={chosen.id} aria-label="Creative source day"
            onChange={event => setSourceId(event.target.value)}>
            {days.map(day => <option key={day.id} value={day.id}>
              {day.campaign_id.slice(0, 8)} · Day {day.day_index}
            </option>)}
          </select>
        </label>
        <Button type="button" disabled={working} onClick={issueSource}>
          Prepare exact saved storyboard for review
        </Button>
      </>}
    </div>}
    {reviews.isPending && reviews.isFetching && <p role="status">
      Reading private creative proposals…
    </p>}
    {reviews.isError && <p role="alert">
      Private creative history could not be verified. Rendering stays disabled.
      <Button variant="outline" size="sm" onClick={() => reviews.refetch()}>
        Retry read
      </Button>
    </p>}
    {reviews.isSuccess && plans.length === 0 && <p role="status">
      No service-issued Creative Director plan exists for this business.
      Create your campaign first; no media or claims are assumed.
    </p>}
    {plan && <>
      <label>Review saved plan
        <select aria-label="Saved creative plan" value={plan.id}
          onChange={event => { setSelectedId(event.target.value); setError(''); setNotice(''); setCpuJob(null); setCpuPreview(null); setCpuError('') }}>
          {plans.map(item => <option key={item.id} value={item.id}>
            {item.campaign_id.slice(0, 8)} · {item.state}
          </option>)}
        </select>
      </label>
      <p><strong>Review state:</strong> {plan.state}</p>
      <p><strong>Source fingerprint:</strong> <code>{plan.proposal_sha256}</code></p>
      <p><strong>Call to action:</strong> {String(source?.cta || '')}</p>
      <ol aria-label="Original reviewed director scenes">
        {scenes.map((scene, index) => <li key={index}>
          <strong>Scene {index + 1}</strong> · {scene.duration} seconds · {scene.headline}
        </li>)}
      </ol>
      <p>Review real product claims and media rights before approval. Speech
        scripts are text only until separately recorded and licensed.</p>
      {canReview && plan.state === 'DRAFT' && <Button type="button"
        disabled={working} onClick={() => write('review')}>
        Approve this exact creative revision
      </Button>}
      {CPU_RENDER_ENABLED && canReview && plan.state === 'APPROVED' && <>
        <h3>Private CPU video render</h3>
        {!cpuApi && <p role="status">
          The verified CPU renderer is not configured; no job or credits were used.
        </p>}
        {cpuApi && <Button type="button" disabled={working} onClick={submitCpuRender}>
          Render approved Reel using owned media
        </Button>}
        {cpuApi && <Button type="button" variant="outline" disabled={working}
          onClick={recoverCpuRender}>Check existing render (read only)</Button>}
        {cpuJob && cpuJob.planId === plan.id && <p role="status">
          Render {cpuJob.status.toLowerCase()} · {cpuJob.job_id}
        </p>}
        {cpuJob && cpuJob.planId === plan.id &&
          cpuJob.status === 'SUCCEEDED' && cpuApi && <Button type="button"
            variant="outline" onClick={downloadCpu}>Download private MP4</Button>}
        {cpuJob && cpuJob.planId === plan.id &&
          cpuJob.status === 'SUCCEEDED' && cpuPreview &&
          <video aria-label="Private CPU render preview" controls playsInline
            preload="metadata" src={cpuPreview} />}
        {cpuError && <p role="alert">{cpuError}</p>}
      </>}
      {role === 'OWNER' && plan.state === 'APPROVED' && <Button
        type="button" variant="outline" disabled={working}
        onClick={() => write('revoke')}>Revoke this version</Button>}
      {!canReview && <p role="status">Read-only business access cannot approve or revoke.</p>}
    </>}
    {notice && <p role="status">{notice}</p>}
    {error && <p role="alert">{error}</p>}
  </Card>
}
