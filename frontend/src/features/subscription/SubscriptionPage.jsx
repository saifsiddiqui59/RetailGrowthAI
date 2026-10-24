import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import { PLAN_LIMITS, presentSubscription, subscriptionNotice } from './plan-display.mjs'

const INITIAL_USAGE = { campaign: null, render: null }
const CANDIDATES = ['STARTER', 'GROWTH', 'BUSINESS']
function formatDate(iso) {
  const date = new Date(iso)
  return Number.isFinite(date.getTime())
    ? date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
    : 'Unavailable'
}

function Meter({ label, meter }) {
  return <div className="quota-meter">
    <div className="quota-meter-head">
      <strong>{label}</strong><span>{meter.used} of {meter.limit} used · {meter.remaining} remaining</span>
    </div>
    <div className="quota-track" role="progressbar" aria-label={label + ' used'}
      aria-valuemin={0} aria-valuemax={meter.limit} aria-valuenow={Math.min(meter.used, meter.limit)}>
      <div style={{ width: meter.percent + '%' }} />
    </div>
  </div>
}

export default function SubscriptionPage() {
  const { client, configured, user, loading: sessionLoading } = useRetailAuth()
  const [shops, setShops] = useState([])
  const [shopId, setShopId] = useState('')
  const [subscription, setSubscription] = useState(null)
  const [usage, setUsage] = useState(INITIAL_USAGE)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')
  const [reload, setReload] = useState(0)

  useEffect(() => {
    let current = true
    setShops([])
    setShopId('')
    setError('')
    if (user && configured) client.listShops().then((rows) => {
      if (current) {
        setShops(rows)
        setShopId(rows.find((shop) => shop.membership?.role === 'OWNER')?.id || rows[0]?.id || '')
      }
    }).catch(() => {
      if (current) setError('Unable to load your businesses. Try again from Account.')
    })
    return () => { current = false }
  }, [client, configured, user])

  const selected = shops.find((shop) => shop.id === shopId)
  const isOwner = selected?.membership?.role === 'OWNER'
  useEffect(() => {
    let current = true
    setSubscription(null)
    setUsage(INITIAL_USAGE)
    if (!user || !isOwner || !shopId) {
      setPending(false)
      return () => { current = false }
    }
    setPending(true)
    setError('')
    client.getShopSubscription(shopId).then(async (result) => {
      if (!result) throw new Error('missing subscription')
      const counts = await client.getShopUsage(shopId, result.period_start)
      if (current) {
        setSubscription(result)
        setUsage(counts)
      }
    }).catch(() => {
      if (current) setError('Unable to verify plan or usage. No balances are estimated.')
    }).finally(() => {
      if (current) setPending(false)
    })
    return () => { current = false }
  }, [client, user, shopId, isOwner, reload])

  let summary = null
  try {
    if (subscription && usage.campaign !== null && usage.render !== null) {
      summary = presentSubscription(subscription, usage)
    }
  } catch {
    // Fail closed: do not show an unverified entitlement or balance.
  }

  return (
    <div className="subscription-page">
      <div className="page-heading"><div><div className="eyebrow">BILLING &amp; USAGE</div>
        <h1>Subscription &amp; plans</h1>
        <p className="lead">Monitor your shop's server-controlled plan, trial expiry and campaign/render allowances.</p>
      </div><span className="tag">DEV · No payments enabled</span></div>
      {!configured && <p role="status" className="panel">This demo has no live subscription connection. Sign-in and quota checks require your RetailGrowthAI DEV configuration.</p>}
      {configured && !sessionLoading && !user && <section className="panel">
        <h2>Sign in to view your plan</h2>
        <p>Only authorized shop owners can view subscription details and quota reservations.</p>
        <Link className="primary-action" to="/account">Sign in</Link>
      </section>}
      {configured && user && <section className="panel subscription-current" aria-label="Current subscription">
        <div className="panel-heading"><div><div className="eyebrow">CURRENT SUBSCRIPTION</div><h2>Plan and allowances</h2></div>
          <button className="subtle-button" type="button" onClick={() => setReload((value) => value + 1)}>Refresh</button>
        </div>
        {shops.length > 0 && <label className="subscription-shop-select">Business
          <select value={shopId} onChange={(event) => setShopId(event.target.value)}>
            {shops.map((shop) => <option key={shop.id} value={shop.id}>{shop.name} · {shop.membership.role}</option>)}
          </select></label>}
        {!shops.length && !error && <p role="status">No accessible businesses. <Link to="/account">Create your business.</Link></p>}
        {selected && !isOwner && <p role="status">Only the business OWNER can view plan and usage details. Your {selected.membership.role} access does not include billing.</p>}
        {pending && <p role="status">Verifying live subscription and usage…</p>}
        {error && <p role="alert" className="notice-error">{error}</p>}
        {subscription && !pending && !error && !summary && <p role="alert">Plan data could not be verified. Refresh to try again.</p>}
        {summary && !pending && !error && isOwner && <>
          <div className="subscription-summary">
            <div><span className="plan-name">{summary.plan} plan</span>
              <span className={'plan-status ' + (summary.active ? 'active' : 'inactive')}>
                {summary.active ? summary.status : 'EXPIRED / INACTIVE'}</span>
              <p>{summary.active
                ? summary.remainingDays + ' day(s) of access remaining'
                : 'New AI jobs are blocked until a valid entitlement is assigned by the service.'}</p>
            </div>
            <div className="subscription-dates">
              <div><span>Access until</span><strong>{formatDate(summary.validUntil)}</strong></div>
              <div><span>Usage period ends</span><strong>{formatDate(summary.periodEnd)}</strong></div>
            </div>
          </div>
          {subscriptionNotice(summary) && <p role={subscriptionNotice(summary).level === 'alert' ? 'alert' : 'status'} className="plan-fineprint">{subscriptionNotice(summary).text}</p>}
          <h3>Current usage · this billing period</h3>
          <Meter label="Campaign jobs" meter={summary.meters.campaign} />
          <Meter label="Video render jobs" meter={summary.meters.render} />
          <p className="plan-fineprint">These are atomic job reservations, not post impressions or paid invoices. Once your plan expires or a limit is reached, new campaign/render spending is denied by the backend; existing drafts remain viewable.</p>
        </>}
      </section>}
      <section className="plan-comparison" aria-label="Available plan comparison">
        <div className="eyebrow">PLAN ROADMAP</div><h2>Explore planned tiers</h2>
        <p>Subscription limits shown below are candidates already defined in the backend policy. No paid upgrades, payment checkout, renewals or prices are available in DEV.</p>
        <div className="plan-grid">
          <div className="plan-card">
            <span className="plan-flag">Enabled for new businesses</span><h3>Free trial</h3><strong>7 days</strong>
            <p>Explore campaign generation and private video rendering.</p>
            <ul><li>{PLAN_LIMITS.TRIAL.campaign} campaign jobs</li><li>{PLAN_LIMITS.TRIAL.render} render jobs</li><li>Secure draft editing</li></ul>
            <span className="plan-foot">Automatically created by the service</span>
          </div>
          {CANDIDATES.map((code) => <div className="plan-card" key={code}>
            <span className="plan-flag muted">Coming later</span><h3>{code[0] + code.slice(1).toLowerCase()}</h3>
            <strong>Pricing pending</strong><p>Proposed usage tier. Not available to purchase.</p>
            <ul><li>{PLAN_LIMITS[code].campaign} campaign jobs / period</li><li>{PLAN_LIMITS[code].render} render jobs / period</li><li>Server-controlled access</li></ul>
            <span className="plan-foot">No checkout or self-upgrade</span>
          </div>)}
        </div>
      </section>
    </div>
  )
}
