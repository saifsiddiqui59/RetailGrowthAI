import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '../../components/ui/button.jsx'
import { Card } from '../../components/ui/card.jsx'

const REVIEW_ENABLED = import.meta.env?.VITE_FEATURE4_PLAN_REVIEW_ENABLED === 'true'
const ISSUE_ENABLED = import.meta.env?.VITE_FEATURE4_PLAN_ISSUE_ENABLED === 'true'

// REAL signed source review: no synthetic approval toggles and no generated
// media/sounds/GPU calls. Only an explicit retailer click runs the narrow SQL
// RPC after fetching this business's persisted F2 proposal under RLS.
export default function CreativePlanReview({ client, user, shopId, role }) {
  const [selectedId, setSelectedId] = useState('')
  const [sourceId, setSourceId] = useState('')
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
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
          onChange={event => { setSelectedId(event.target.value); setError(''); setNotice('') }}>
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
      {role === 'OWNER' && plan.state === 'APPROVED' && <Button
        type="button" variant="outline" disabled={working}
        onClick={() => write('revoke')}>Revoke this version</Button>}
      {!canReview && <p role="status">Read-only business access cannot approve or revoke.</p>}
    </>}
    {notice && <p role="status">{notice}</p>}
    {error && <p role="alert">{error}</p>}
  </Card>
}
