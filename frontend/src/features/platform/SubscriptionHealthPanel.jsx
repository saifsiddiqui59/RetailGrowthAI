import { useMemo, useState } from 'react'
import { buildSubscriptionHealth, filterSubscriptionHealth } from './subscription-health.mjs'
import './subscription-health.css'

// Explicitly limited to the currently loaded 25-row page; platform totals are distinct.
export default function SubscriptionHealthPanel({shops, total, offset, loading, error, onManage}) {
  const [status, setStatus] = useState('all')
  const [search, setSearch] = useState('')
  const state = useMemo(() => buildSubscriptionHealth(shops), [shops])
  const rows = useMemo(() => filterSubscriptionHealth(state.rows,status,search), [state.rows,status,search])
  return <section className="panel subscription-health" aria-label="Subscription health on this page">
    <div className="panel-heading">
      <div><div className="eyebrow">SAAS OWNER / ENTITLEMENTS</div>
        <h2>Subscription watch</h2>
      </div>
      <span className="tag">Loaded page only</span>
    </div>
    <p>Monitor upcoming expiry and suspended accounts for the current retailer directory page.
      No payment processing, auto-renewal or billing email is implied.</p>
    <div className="subscription-health-counts" aria-label="Current page subscription health">
      <div><strong>{state.expiring}</strong><span>Due within 7 days</span></div>
      <div><strong>{state.expired}</strong><span>Expired</span></div>
      <div><strong>{state.suspended}</strong><span>Suspended</span></div>
      <div><strong>{state.unknown}</strong><span>Needs verification</span></div>
    </div>
    {loading && <p role="status">Loading subscription signals…</p>}
    {error && <p role="alert">Subscription list not verified. Counts above are not platform totals.</p>}
    {!loading && !error && <>
      <p className="subscription-health-coverage">Showing data for {shops.length} of {total ?? 'unknown'} retailers,
        starting at row {offset+1}. Filters do not search outside this page.</p>
      <div className="subscription-health-controls">
        <label>Filter status <select value={status} onChange={event=>setStatus(event.target.value)}>
          <option value="all">All</option><option value="expiring">Expiring in 7 days</option>
          <option value="expired">Expired</option><option value="suspended">Suspended</option>
          <option value="unknown">Unknown</option><option value="healthy">Other active</option>
        </select></label>
        <label>Search this page <input type="search" value={search} onChange={event=>setSearch(event.target.value)}
          placeholder="Retailer or plan" /></label>
      </div>
      {!rows.length && <p role="status">No retailers match these filters on this page.</p>}
      <div className="subscription-health-rows">
        {rows.map(row => <div key={row.id} className="subscription-health-row">
          <div><strong>{row.name}</strong><small>{row.plan} · {row.status}</small></div>
          <span>{row.validUntil ? 'Ends ' + new Date(row.validUntil).toLocaleDateString('en-IN') : 'Expiry unverified'}</span>
          <button type="button" className="subtle-button" onClick={()=>onManage(row.original)}>Manage plan</button>
        </div>)}
      </div>
    </>}
  </section>
}
