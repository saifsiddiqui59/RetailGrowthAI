import { useEffect, useRef, useState } from 'react'

/**
 * Retailer-side review controls. All writes require a verified backend user JWT,
 * an active OWNER/EDITOR role and server-side snapshot/quota transaction.
 * No browser field can confer approval, publish directly or allocate quota.
 */
export function SocialAuthoringPanel({ api, shopId, zone, days, accounts, jobs,
                                       canWrite, onUpdated }) {
  const [dayId, setDayId] = useState('')
  const [accountId, setAccountId] = useState('')
  const [caption, setCaption] = useState('')
  const [date, setDate] = useState('')
  const [clock, setClock] = useState('10:00')
  const [actionBusy, setActionBusy] = useState(false)
  const [reviewId, setReviewId] = useState('')
  const [editing, setEditing] = useState(null)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const idempotency = useRef(null)

  useEffect(() => {
    setDayId('')
    setAccountId('')
    setCaption('')
    setReviewId('')
    setEditing(null)
    setNotice('')
    setError('')
    idempotency.current = null
  }, [shopId])

  const approvedDays = days.filter(row => row.review_status === 'APPROVED')
  const textAccounts = accounts.filter(row =>
    row.connection_status === 'CONNECTED' &&
    (row.provider === 'facebook' || row.provider === 'linkedin'))
  const account = textAccounts.find(row => row.id === accountId)
  const editableJobs = jobs.filter(row =>
    ['DRAFT','APPROVED','QUEUED','RETRYABLE'].includes(row.status))

  function revise(setter, value) {
    idempotency.current = null
    setError('')
    setter(value)
  }
  function chooseDay(nextId) {
    const selected = approvedDays.find(row => row.id === nextId)
    revise(setDayId, nextId)
    setCaption(typeof selected?.linkedin?.post_text === 'string'
      ? selected.linkedin.post_text.slice(0, 5000) : '')
  }

  async function create(event) {
    event.preventDefault()
    if (!api || !shopId || !canWrite || !account || !approvedDays.some(d => d.id === dayId))
      return
    setActionBusy(true)
    setError('')
    setNotice('')
    try {
      // One idempotency key for this exact unsent form across network retries.
      if (!idempotency.current) idempotency.current = crypto.randomUUID()
      await api.createDraft({
        shopId, dayId, accountId, provider: account.provider,
        caption, day: date, clock, timezone: zone, idempotencyKey: idempotency.current,
        mediaAssetId: null,
      })
      idempotency.current = null
      setNotice('Draft saved. Review its exact text before approving a publish quota reservation.')
      await onUpdated()
    } catch (failure) {
      setError(failure.message)
    } finally {
      setActionBusy(false)
    }
  }

  function beginEdit(job) {
    if (!canWrite || job.status !== 'DRAFT') return
    setReviewId('')
    setNotice('')
    setError('')
    setEditing({id: job.id, revision: job.revision,
      caption: job.caption, day: '', clock: '10:00'})
  }

  async function saveEdit(event) {
    event.preventDefault()
    if (!editing || !canWrite || !api || !shopId) return
    setActionBusy(true)
    setError('')
    setNotice('')
    try {
      await api.reviseDraft({shopId, jobId: editing.id,
        expectedRevision: editing.revision, caption: editing.caption,
        day: editing.day, clock: editing.clock, timezone: zone})
      setEditing(null)
      setReviewId('')
      setNotice('Draft revised. Review the updated text and time again before approval.')
      await onUpdated()
    } catch (failure) {
      setError(failure.message)
    } finally {
      setActionBusy(false)
    }
  }

  async function changeJob(action, job) {
    if (!api || !canWrite || !shopId || action === 'approve' && reviewId !== job.id)
      return
    setActionBusy(true)
    setError('')
    setNotice('')
    try {
      if (action === 'approve') {
        await api.approveDraft(shopId, job.id, job.revision)
        setNotice('Review approval saved and publishing quota reserved. This does not immediately publish.')
      } else {
        await api.cancelDraft(shopId, job.id, job.revision)
        setNotice('Unsent publishing job cancelled.')
      }
      setReviewId('')
      await onUpdated()
    } catch (failure) {
      setError(failure.message)
    } finally {
      setActionBusy(false)
    }
  }

  return <section className="panel" aria-labelledby="social-review-heading" style={{marginTop:16}}>
    <h2 id="social-review-heading">Review and schedule posts</h2>
    <p>Only real, reviewed campaign days and connected business accounts can create a draft.
      These controls never directly publish or upload to any platform.</p>
    {!canWrite && <p role="status">A business OWNER or EDITOR is required to create or approve posts.</p>}
    {error && <p role="alert">{error}</p>}
    {notice && <p role="status">{notice}</p>}
    <form onSubmit={create} style={{display:'grid',gap:12,maxWidth:650}}>
      <label htmlFor="social-authoring-day">Approved campaign day</label>
      <select id="social-authoring-day" value={dayId}
        onChange={event=>chooseDay(event.target.value)}
        required disabled={!canWrite || actionBusy}>
        <option value="">Select a reviewed campaign day</option>
        {approvedDays.map(item=><option key={item.id} value={item.id}>
          {item.scheduled_date} · {item.topic}</option>)}
      </select>
      <label htmlFor="social-authoring-account">Connected publishing account</label>
      <select id="social-authoring-account" value={accountId}
        onChange={event=>revise(setAccountId,event.target.value)}
        required disabled={!canWrite || actionBusy}>
        <option value="">Select a connected LinkedIn or Facebook Page</option>
        {textAccounts.map(item=><option key={item.id} value={item.id}>
          {item.provider} · {item.display_name}</option>)}
      </select>
      <label htmlFor="social-authoring-caption">Exact text to review</label>
      <textarea id="social-authoring-caption" value={caption}
        onChange={event=>revise(setCaption,event.target.value)}
        maxLength={5000} rows={5} required disabled={!canWrite || actionBusy}/>
      <div style={{display:'flex',flexWrap:'wrap',gap:12}}>
        <label htmlFor="social-authoring-date">Local date
          <input id="social-authoring-date" type="date" value={date}
            onChange={event=>revise(setDate,event.target.value)}
            required disabled={!canWrite || actionBusy}/>
        </label>
        <label htmlFor="social-authoring-clock">Local time
          <input id="social-authoring-clock" type="time" value={clock}
            onChange={event=>revise(setClock,event.target.value)}
            required disabled={!canWrite || actionBusy}/>
        </label>
      </div>
      <p>Timezone: <strong>{zone}</strong>. The server rejects expired, DST-gap and ambiguous times.</p>
      <button type="submit" disabled={!canWrite || !api || actionBusy ||
        !dayId || !accountId || !caption.trim() || !date}>
        {actionBusy ? 'Processing…' : 'Save publishing draft'}
      </button>
    </form>

    <h3 style={{marginTop:24}}>Review pending posts</h3>
    {!editableJobs.length && <p>No pending publishing drafts for this business.</p>}
    {editableJobs.map(job=><article className="day-card" key={job.id}
      style={{padding:16,marginTop:12}}>
      <strong>{job.provider} · {job.status}</strong>
      <p style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{job.caption}</p>
      <p>Scheduled: {job.scheduled_at} ({job.timezone}) · Revision {job.revision}</p>
      {job.status === 'DRAFT' && <label style={{display:'block',marginBottom:10}}>
        <input type="checkbox" checked={reviewId === job.id}
          onChange={event=>setReviewId(event.target.checked ? job.id : '')}
          disabled={!canWrite || actionBusy}/>
        {' '}I have reviewed this exact text, account and scheduled time.
      </label>}
      {job.status === 'DRAFT' && <button type="button"
        onClick={()=>changeJob('approve',job)}
        disabled={!canWrite || actionBusy || reviewId !== job.id}>
        Approve and reserve publishing quota
      </button>}
      {job.status === 'DRAFT' && <button type="button"
        onClick={()=>editing?.id === job.id ? setEditing(null) : beginEdit(job)}
        disabled={!canWrite || actionBusy}>
        {editing?.id === job.id ? 'Close editor' : 'Edit draft / reschedule'}
      </button>}
      {job.status === 'DRAFT' && editing?.id === job.id &&
        <form onSubmit={saveEdit} style={{display:'grid',gap:8,marginTop:12,maxWidth:650}}>
          <label htmlFor={'social-revise-caption-' + job.id}>Revised caption</label>
          <textarea id={'social-revise-caption-' + job.id} required rows={4}
            maxLength={5000} value={editing.caption} disabled={actionBusy}
            onChange={event=>setEditing(old=>({...old,caption:event.target.value}))}/>
          <label htmlFor={'social-revise-date-' + job.id}>New local publish date</label>
          <input id={'social-revise-date-' + job.id} type="date" required
            value={editing.day} disabled={actionBusy}
            onChange={event=>setEditing(old=>({...old,day:event.target.value}))}/>
          <label htmlFor={'social-revise-time-' + job.id}>New local publish time ({zone})</label>
          <input id={'social-revise-time-' + job.id} type="time" required
            value={editing.clock} disabled={actionBusy}
            onChange={event=>setEditing(old=>({...old,clock:event.target.value}))}/>
          <p>Saving increases the draft revision and invalidates prior review intent.
            Approved or possibly sent posts cannot be edited here.</p>
          <button type="submit" disabled={actionBusy || !editing.day ||
            !editing.caption.trim()}>Save revised draft</button>
        </form>}
      {' '}
      <button type="button" onClick={()=>changeJob('cancel',job)}
        disabled={!canWrite || actionBusy}>Cancel unsent job</button>
    </article>)}
    <p>Instagram Reels and YouTube videos remain unavailable for approval until
      server-verified media licenses and codec checks are complete.</p>
  </section>
}

export default SocialAuthoringPanel
