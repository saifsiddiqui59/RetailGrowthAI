import { useCallback, useEffect, useState } from 'react'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import SubscriptionHealthPanel from './SubscriptionHealthPanel.jsx'
import VerifiedMetricsChart from '../dashboard/VerifiedMetricsChart.jsx'
import { Card } from '../../components/ui/card.jsx'
import { Button } from '../../components/ui/button.jsx'
import { Badge } from '../../components/ui/badge.jsx'
import './platform-operations.css'

const EMPTY = { retailers: null, trial_shops: null, active_paid_shops: null,
  expired_or_suspended: null, campaigns: null, reels_completed: null }
const CARDS = [
  ['retailers', 'Total retailers'],
  ['trial_shops', 'Active trials'],
  ['active_paid_shops', 'Active paid entitlements'],
  ['expired_or_suspended', 'Expired / suspended'],
  ['campaigns', 'Campaigns generated'],
  ['reels_completed', 'Completed video renders'],
]
const VALID_PLANS = ['STARTER', 'GROWTH', 'BUSINESS']

function deriveWarnings(summary, failed) {
  if (failed) return [{
    level: 'critical', title: 'Platform monitoring is unavailable',
    detail: 'The server did not return verified metrics. Inspect admin authorization and DEV service health; values are not estimated.',
  }]
  if (!Number.isInteger(summary.retailers) || !Number.isInteger(summary.expired_or_suspended) ||
      !Number.isInteger(summary.trial_shops) || !Number.isInteger(summary.active_paid_shops) ||
      !Number.isInteger(summary.campaigns) || !Number.isInteger(summary.reels_completed)) return []
  const items = []
  if (summary.retailers === 0) items.push({
    level: 'attention', title: 'No retailer businesses onboarded',
    detail: 'Create a retailer through normal signup and shop onboarding before evaluating growth metrics.',
  })
  if (summary.expired_or_suspended > 0) items.push({
    level: 'critical', title: summary.expired_or_suspended + ' expired or suspended subscriptions',
    detail: 'Review affected retailers and confirm intended entitlement status before making an audited change.',
  })
  if (summary.retailers > 0 && summary.active_paid_shops === 0 &&
      summary.trial_shops === 0) items.push({
    level: 'attention', title: 'No active trial or paid entitlement',
    detail: 'Retailers may be unable to start new generation and render jobs. Review their subscription state.',
  })
  if (summary.campaigns > 0 && summary.reels_completed === 0) items.push({
    level: 'info', title: 'No completed video renders recorded',
    detail: 'Campaigns exist, but no completed reels are counted. This is not evidence that rendering has failed.',
  })
  items.push({
    level: 'info', title: 'Payments and external platform metrics are not active',
    detail: 'Revenue, publication delivery, reach, Azure spend and error-rate alarms are not verified by this dashboard. Do not treat them as zero.',
  })
  return items
}


export default function PlatformAdmin() {
  const { client } = useRetailAuth()
  const [summary, setSummary] = useState(EMPTY)
  const [shops, setShops] = useState([])
  const [total, setTotal] = useState(null)
  const [offset, setOffset] = useState(0)
  const [reload, setReload] = useState(0)
  const [loading, setLoading] = useState(true)
  const [summaryLoading, setSummaryLoading] = useState(true)
  const [summaryError, setSummaryError] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [editing, setEditing] = useState(null)
  const [plan, setPlan] = useState('STARTER')
  const [status, setStatus] = useState('ACTIVE')
  const [validUntil, setValidUntil] = useState('')
  const [reason, setReason] = useState('')
  const [confirmed, setConfirmed] = useState(false)
  const [saving, setSaving] = useState(false)
  const [reviewOpen, setReviewOpen] = useState(false)
  const [reviewRows, setReviewRows] = useState([])
  const [reviewPending, setReviewPending] = useState(false)
  const [reviewError, setReviewError] = useState('')
  const [reviewReason, setReviewReason] = useState('')
  const [reviewUser, setReviewUser] = useState('')
  const [reviewConfirm, setReviewConfirm] = useState(false)
  const [reviewSaving, setReviewSaving] = useState(false)
  const [reviewVersion, setReviewVersion] = useState(0)

  useEffect(() => {
    let current = true
    if (!reviewOpen) return () => { current = false }
    setReviewPending(true)
    setReviewError('')
    client.listPlatformOnboardingRequests('PENDING')
      .then(rows => { if (current) setReviewRows(rows) })
      .catch(() => { if (current) setReviewError('Approval requests could not be loaded. Do not assume the queue is empty.') })
      .finally(() => { if (current) setReviewPending(false) })
    return () => { current = false }
  }, [client, reviewOpen, reviewVersion])

  async function reviewRequest(accountId, approve) {
    if (!reviewConfirm || reviewSaving || reviewUser !== accountId) return
    setReviewSaving(true)
    setReviewError('')
    try {
      await client.reviewPlatformOnboarding(accountId, approve, reviewReason)
      setReviewUser('')
      setReviewConfirm(false)
      setReviewReason('')
      setMessage(approve ? 'Retailer onboarding approved.' : 'Retailer onboarding rejected.')
      setReviewVersion(value => value + 1)
    } catch {
      setReviewError('Approval decision was not accepted. Refresh before trying again.')
    } finally {
      setReviewSaving(false)
    }
  }


  // The platform-wide summary is independent of the tenant directory page.
  // Fetch it on first render, an explicit Refresh, or after an audited plan
  // change only. Changing pages must not call the cross-tenant summary RPC.
  useEffect(() => {
    let active = true
    setSummaryLoading(true)
    setSummaryError('')
    setSummary(EMPTY)
    client.getPlatformSummary().then(metrics => {
      if (!metrics || !CARDS.every(([key]) =>
          Number.isSafeInteger(metrics[key]) && metrics[key] >= 0)) {
        throw new Error('Invalid platform summary')
      }
      if (active) setSummary(metrics)
    }).catch(() => {
      if (active) {
        setSummary(EMPTY)
        setSummaryError('Platform metrics could not be verified. No totals are estimated.')
      }
    }).finally(() => { if (active) setSummaryLoading(false) })
    return () => { active = false }
  }, [client, reload])

  // Directory pagination uses one bounded per-page RPC. Failure here must
  // not blank separately verified platform-wide metrics or warnings.
  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    setShops([])
    setTotal(null)
    client.listPlatformShops(25, offset).then(listing => {
      if (!listing || !Array.isArray(listing.shops) ||
          !Number.isSafeInteger(listing.total) || listing.total < 0) {
        throw new Error('Invalid retailer directory')
      }
      if (active) {
        setShops(listing.shops)
        setTotal(listing.total)
      }
    }).catch(() => {
      if (active) setError('Retailer directory could not be verified. No directory rows are assumed.')
    }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [client, offset, reload])

  function beginEdit(shop) {
    setEditing(shop)
    setPlan(VALID_PLANS.includes(shop.plan_code) ? shop.plan_code : 'STARTER')
    setStatus('ACTIVE')
    setValidUntil('')
    setReason('')
    setConfirmed(false)
    setError('')
    setMessage('')
  }

  async function save(event) {
    event.preventDefault()
    if (!editing || !confirmed || saving) return
    setSaving(true)
    setError('')
    setMessage('')
    try {
      await client.setPlatformSubscription({
        shopId: editing.shop_id,
        planCode: plan,
        status,
        validUntil,
        reason,
      })
      setEditing(null)
      setMessage('Audited subscription change saved. Usage period refreshed; no payment was charged.')
      setReload((value) => value + 1)
    } catch {
      setError('Subscription change was rejected by server authorization or validation. No change is assumed.')
    } finally {
      setSaving(false)
    }
  }

  const warnings = deriveWarnings(summary, Boolean(summaryError))
  return <div className="platform-page" aria-label="Platform Control dashboard">
    <div className="page-heading">
      <div><div className="eyebrow">RETAILGROWTHAI · PROVIDER OPERATIONS</div>
        <h1>Platform Control</h1>
        <p className="lead">Retailer operations and manual subscription administration. Accessible only with a database-verified Platform Super Admin grant.</p>
      </div>
      <Badge className="tag">DEV · No payment gateway</Badge>
    </div>
    <Card className="panel platform-security-note">
      <strong>Privileged access, same login.</strong>
      <p>Shop OWNER rights remain restricted to that shop. This platform console uses separately verified service-side RPCs with audited changes; it does not expose service-role credentials or bypass campaign authorization.</p>
    </Card>
    {summaryLoading && <p role="status">Verifying platform summary…</p>}
    {loading && <p role="status">Loading retailer directory page…</p>}
    {summaryError && <p role="alert" className="notice-error">{summaryError}</p>}
    {error && <p role="alert" className="notice-error">{error}</p>}
    {message && <p role="status">{message}</p>}
    <section className="metrics platform-metrics" aria-label="Platform overview metrics">
      {CARDS.map(([key, label]) => <Card className="metric rg-platform-metric" key={key}>
        <span>{label}</span><strong>{summary[key] ?? '—'}</strong>
        <small>Verified server count</small>
      </Card>)}
    </section>
    <Card className="panel rg-chart-panel" aria-label="Verified platform analytics">
      <div className="eyebrow">SERVER-VERIFIED OVERVIEW</div><h2>Platform activity</h2>
      <VerifiedMetricsChart title="Verified platform activity"
        labels={['Retailers', 'Trials', 'Paid', 'Expired', 'Campaigns', 'Reels']}
        values={[summary.retailers, summary.trial_shops, summary.active_paid_shops,
          summary.expired_or_suspended, summary.campaigns, summary.reels_completed]} />
    </Card>
    <Card className="panel platform-warning-center" aria-label="Platform monitoring warnings">
      <div className="panel-heading"><div><div className="eyebrow">PLATFORM MONITORING</div>
        <h2>Warnings &amp; attention needed</h2></div>
        <span className="tag">{summaryLoading ? 'Updating' : warnings.length + ' notices'}</span>
      </div>
      <p>Warnings are derived from verified Supabase counts and known DEV feature limitations. They are not automated Azure or social-platform alerts. Summary refreshes only on opening, manual Refresh or an audited plan change; retailer paging does not refresh it.</p>
      {!summaryLoading && !warnings.length && !summaryError && <p role="status">No count-based issues detected. Provider health monitoring is not yet connected.</p>}
      {!summaryLoading && warnings.length > 0 && <div className="platform-warning-list">
        {warnings.map((warning) => <div className={'platform-warning '+warning.level} key={warning.title}>
          <span className="platform-warning-icon" aria-hidden="true">{warning.level === 'critical' ? '!' : warning.level === 'attention' ? '!' : 'i'}</span>
          <div><strong>{warning.title}</strong><p>{warning.detail}</p></div>
        </div>)}
      </div>}
    </Card>
    <Card className="panel platform-approvals" aria-label="Retailer approval center">
      <div className="panel-heading"><div><div className="eyebrow">SAAS OWNER ACTIONS</div>
        <h2>Retailer signup approvals</h2></div>
        <Button variant="outline" size="sm" className="subtle-button"
          onClick={() => setReviewOpen(open => !open)} aria-expanded={reviewOpen}>
          {reviewOpen ? 'Hide requests' : 'Review requests'}
        </Button>
      </div>
      <p>New RetailGrowthAI Auth registrations are queued separately from email verification.
        Decisions are restricted to Platform Super Admin and stored with an audit reason.
        Approval does not charge a customer or send an email.</p>
      {reviewOpen && <>
        <button className="subtle-button" type="button"
          onClick={() => setReviewVersion(v => v+1)}>Refresh queue</button>
        {reviewPending && <p role="status">Loading pending retailer requests…</p>}
        {reviewError && <p role="alert" className="notice-error">{reviewError}</p>}
        {!reviewPending && !reviewError && reviewRows.length === 0 &&
          <p role="status">No pending retailer approval requests.</p>}
        {!reviewPending && reviewRows.map(entry => <div className="platform-review-item" key={entry.user_id}>
          <div><strong>{entry.email}</strong><small>Requested {new Date(entry.requested_at).toLocaleString('en-IN')}</small></div>
          {reviewUser !== entry.user_id
            ? <button className="subtle-button" onClick={() => {
              setReviewUser(entry.user_id)
              setReviewReason('')
              setReviewConfirm(false)
            }}>Review account</button>
            : <div className="platform-review-action">
              <label>Reason for decision (10–300 characters)
                <textarea aria-label="Decision reason" maxLength={300} minLength={10}
                  value={reviewReason} onChange={e => setReviewReason(e.target.value)} />
              </label>
              <label className="platform-review-confirm">
                <input type="checkbox" checked={reviewConfirm}
                  onChange={e => setReviewConfirm(e.target.checked)}/>
                I verified this account request and authorize the decision.
              </label>
              <div className="platform-review-buttons">
                <button type="button" disabled={reviewSaving || !reviewConfirm || reviewReason.trim().length < 10}
                  onClick={() => reviewRequest(entry.user_id,true)}>Approve</button>
                <button type="button" disabled={reviewSaving || !reviewConfirm || reviewReason.trim().length < 10}
                  onClick={() => reviewRequest(entry.user_id,false)}>Reject</button>
                <button type="button" disabled={reviewSaving} onClick={() => setReviewUser('')}>Cancel</button>
              </div>
            </div>}
        </div>)}
      </>}
    </Card>
    <SubscriptionHealthPanel onManage={beginEdit} refreshKey={reload} />
    <Card className="panel rg-platform-directory">
      <div className="panel-heading">
        <div><div className="eyebrow">TENANT DIRECTORY</div><h2>Retailer accounts</h2></div>
        <Button variant="outline" size="sm" className="subtle-button" onClick={() => setReload((v) => v + 1)}>Refresh</Button>
      </div>
      {total !== null && <p role="status">{total} retailers · showing {shops.length} on this page</p>}
      {!loading && !error && !shops.length && <p>No retailers are registered.</p>}
      {!!shops.length && <div className="platform-table-wrap">
        <table className="platform-table">
          <thead><tr><th>Retailer</th><th>Plan</th><th>Status</th><th>Campaigns</th><th>Renders</th><th>Expires</th><th>Action</th></tr></thead>
          <tbody>
            {shops.map((shop) => <tr key={shop.shop_id}>
              <td><strong>{shop.name}</strong><small>{shop.slug}</small></td>
              <td>{shop.plan_code || 'Unavailable'}</td>
              <td>{shop.subscription_status || 'Unknown'}</td>
              <td>{shop.campaigns}</td><td>{shop.renders}</td>
              <td>{shop.valid_until ? new Date(shop.valid_until).toLocaleDateString('en-IN') : 'Unavailable'}</td>
              <td><button type="button" className="subtle-button" onClick={() => beginEdit(shop)}>Manage plan</button></td>
            </tr>)}
          </tbody>
        </table>
      </div>}
      <div className="platform-pager">
        <button type="button" className="subtle-button" disabled={offset === 0 || loading} onClick={() => setOffset(Math.max(0, offset - 25))}>Previous</button>
        <span>Page {Math.floor(offset / 25) + 1}</span>
        <button type="button" className="subtle-button" disabled={loading || total === null || offset + 25 >= total || offset + 25 > 5000}
          onClick={() => setOffset(offset + 25)}>Next</button>
      </div>
    </Card>
    {editing && <Card className="panel platform-edit" aria-label="Admin subscription editor">
      <h2>Manage {editing.name}</h2>
      <p>Changes are applied only after explicit confirmation and are logged with the acting user and reason. Changing a plan starts a new usage period; historic usage is preserved.</p>
      <form onSubmit={save}>
        <label>Subscription tier
          <select aria-label="Subscription tier" value={plan} onChange={(e) => setPlan(e.target.value)}>
            {VALID_PLANS.map((code) => <option key={code} value={code}>{code}</option>)}
          </select>
        </label>
        <label>Access status
          <select aria-label="Access status" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="ACTIVE">ACTIVE</option><option value="SUSPENDED">SUSPENDED</option>
          </select>
        </label>
        <label>Access end date (UTC)
          <input type="date" aria-label="Access end date" required value={validUntil} onChange={(e) => setValidUntil(e.target.value)} />
        </label>
        <label>Audit reason (10–300 characters)
          <textarea aria-label="Audit reason" minLength="10" maxLength="300" required value={reason} onChange={(e) => setReason(e.target.value)} />
        </label>
        <label className="platform-confirm">
          <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />
          I approve this manual entitlement change and its quota period reset.
        </label>
        <div className="platform-form-actions">
          <button type="submit" className="primary-action" disabled={!confirmed || saving || reason.trim().length < 10 || !validUntil}>
            {saving ? 'Applying audited change…' : 'Apply privileged change'}
          </button>
          <button type="button" className="subtle-button" disabled={saving} onClick={() => setEditing(null)}>Cancel</button>
        </div>
      </form>
    </Card>}
  </div>
}
