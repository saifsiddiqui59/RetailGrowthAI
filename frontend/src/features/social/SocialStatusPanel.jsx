import { socialStatusForShop } from './social-status.mjs'

export function SocialStatusPanel({ shopId, jobs, loading = false }) {
  const { counts, total, attention } = socialStatusForShop(jobs, shopId)
  return <section className="panel" style={{marginTop:16}}
      aria-labelledby="social-delivery-heading">
    <h2 id="social-delivery-heading">Publishing status and warnings</h2>
    <p>These counts come from this business's RLS-authorized records only.
      Published means a stored provider receipt, not verified reach or engagement.</p>
    {loading && <p role="status">Refreshing publishing statuses…</p>}
    <div className="day-grid">
      <div className="day-card"><strong>{counts.DRAFT}</strong><p>Drafts for review</p></div>
      <div className="day-card"><strong>{counts.APPROVED + counts.QUEUED}</strong><p>Approved or queued</p></div>
      <div className="day-card"><strong>{counts.SENDING + counts.PROCESSING}</strong><p>Sending or processing</p></div>
      <div className="day-card"><strong>{counts.PUBLISHED}</strong><p>Provider receipts stored</p></div>
      <div className="day-card"><strong>{counts.RECONCILE + counts.FAILED}</strong><p>Needs attention</p></div>
    </div>
    {total === 0 && !loading && <p>No publishing jobs recorded for this business.</p>}
    {counts.RECONCILE > 0 && <p role="alert">A provider send may already have succeeded.
      These jobs require manual reconciliation and must never be blindly retried.</p>}
    {counts.FAILED > 0 && <p role="status">Some jobs failed.
      Check account permissions, reviewed media and subscription quota before creating a new draft.</p>}
    {attention.length > 0 && <ul aria-label="Jobs requiring attention">
      {attention.map(item=><li key={item.id}>
        <strong>{item.provider} · {item.status}</strong>
        {' '}Job {item.id}{item.code ? ' · '+item.code : ''}
      </li>)}
    </ul>}
  </section>
}

export default SocialStatusPanel
