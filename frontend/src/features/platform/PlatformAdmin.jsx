import { useCallback, useEffect, useState } from 'react'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'

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

export default function PlatformAdmin() {
  const { client } = useRetailAuth()
  const [summary, setSummary] = useState(EMPTY)
  const [shops, setShops] = useState([])
  const [total, setTotal] = useState(null)
  const [offset, setOffset] = useState(0)
  const [reload, setReload] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [editing, setEditing] = useState(null)
  const [plan, setPlan] = useState('STARTER')
  const [status, setStatus] = useState('ACTIVE')
  const [validUntil, setValidUntil] = useState('')
  const [reason, setReason] = useState('')
  const [confirmed, setConfirmed] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    setShops([])
    setTotal(null)
    setSummary(EMPTY)
    Promise.all([client.getPlatformSummary(), client.listPlatformShops(25, offset)]).then(
      ([metrics, listing]) => {
        if (!active) return
        if (!metrics || !listing || !Array.isArray(listing.shops) ||
            !Number.isSafeInteger(listing.total) || listing.total < 0) {
          throw new Error('Invalid platform reporting data')
        }
        setSummary(metrics)
        setShops(listing.shops)
        setTotal(listing.total)
      }
    ).catch(() => {
      if (active) setError('Unable to verify platform access or load retailer data. No figures are estimated.')
    }).finally(() => {
      if (active) setLoading(false)
    })
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

  return <div className="platform-page" aria-label="Platform Control dashboard">
    <div className="page-heading">
      <div><div className="eyebrow">RETAILGROWTHAI · PROVIDER OPERATIONS</div>
        <h1>Platform Control</h1>
        <p className="lead">Retailer operations and manual subscription administration. Accessible only with a database-verified Platform Super Admin grant.</p>
      </div>
      <span className="tag">DEV · No payment gateway</span>
    </div>
    <div className="panel platform-security-note">
      <strong>Privileged access, same login.</strong>
      <p>Shop OWNER rights remain restricted to that shop. This platform console uses separately verified service-side RPCs with audited changes; it does not expose service-role credentials or bypass campaign authorization.</p>
    </div>
    {loading && <p role="status">Verifying platform reports…</p>}
    {error && <p role="alert" className="notice-error">{error}</p>}
    {message && <p role="status">{message}</p>}
    <section className="metrics platform-metrics" aria-label="Platform overview metrics">
      {CARDS.map(([key, label]) => <div className="metric" key={key}>
        <span>{label}</span><strong>{summary[key] ?? '—'}</strong>
        <small>Verified server count</small>
      </div>)}
    </section>
    <section className="panel">
      <div className="panel-heading">
        <div><div className="eyebrow">TENANT DIRECTORY</div><h2>Retailer accounts</h2></div>
        <button type="button" className="subtle-button" onClick={() => setReload((v) => v + 1)}>Refresh</button>
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
    </section>
    {editing && <section className="panel platform-edit" aria-label="Admin subscription editor">
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
    </section>}
  </div>
}
