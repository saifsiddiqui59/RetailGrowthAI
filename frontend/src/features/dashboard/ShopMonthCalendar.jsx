import {useRef, useState} from 'react'
import {Card} from '../../components/ui/card.jsx'
import {Button} from '../../components/ui/button.jsx'
import {Badge} from '../../components/ui/badge.jsx'
import {draftMonthCells} from './recent-calendar-model.mjs'
import {checkedMonth, verifiedShopMonthRows} from './shop-month-model.mjs'

/** Explicit on-demand, JWT/RLS-protected read of existing campaign_days.
 * Never infer publication or widen access from a remembered shop_id. */
export default function ShopMonthCalendar({client,user,configured,shopId}) {
  const [month,setMonth]=useState(()=>new Date().toISOString().slice(0,7))
  const [status,setStatus]=useState({scope:'',month:'',rows:[],error:'',loading:false})
  const requestRef=useRef(0)
  const scope=(user?.id || '')+':'+(shopId || '')
  const scopeRef=useRef(scope)
  const monthRef=useRef(month)
  scopeRef.current=scope
  monthRef.current=month
  const visible=status.scope===scope && status.month===month ? status : null
  const rows=visible?.rows || []
  const grid=draftMonthCells(rows,month)

  async function loadMonth() {
    // An older shop/month request must not block a new authorized scope.
    if (!configured || !user?.id || !shopId || visible?.loading) return
    const request=++requestRef.current
    const requestedScope=scope
    const requestedMonth=month
    setStatus({scope,month,rows:[],error:'',loading:true})
    try {
      checkedMonth(month)
      const value=await client.listShopCalendarMonth(shopId,month)
      const verified=verifiedShopMonthRows(value,shopId,month)
      if (request===requestRef.current && scopeRef.current===requestedScope &&
          monthRef.current===requestedMonth) {
        setStatus({scope,month,rows:verified,error:'',loading:false})
      }
    } catch {
      if (request===requestRef.current && scopeRef.current===requestedScope &&
          monthRef.current===requestedMonth) {
        setStatus({scope,month,rows:[],error:'Unable to verify this business month. No draft or published dates are assumed.',loading:false})
      }
    }
  }

  return <Card className="panel rg-shop-month" aria-label="All campaigns planning calendar">
    <div className="rg-shop-month-heading">
      <div><div className="eyebrow">ALL CAMPAIGNS / PLANNING</div>
        <h2>Business month overview</h2>
        <p>View draft and reviewed days across your business campaigns. These are <strong>not published social posts</strong>.</p>
      </div>
      <Badge>JWT + tenant RLS</Badge>
    </div>
    <div className="rg-shop-month-controls">
      <label>Month
        <input aria-label="Business calendar month" type="month" min="2000-01" max="2099-12"
          value={month} onChange={e=>{requestRef.current++;setMonth(e.target.value)}}/>
      </label>
      <Button variant="outline" disabled={!configured || !user?.id || !shopId || visible?.loading}
        onClick={loadMonth}>{visible?.loading?'Checking…':'Load business month'}</Button>
    </div>
    {!shopId && <p role="status">Select an authorized business to view its month.</p>}
    {visible?.error && <p role="alert">{visible.error}</p>}
    {visible && !visible.loading && !visible.error && <div role="status" className="rg-library-summary">
      {rows.length} verified planned day{rows.length===1?'':'s'} in {month}. No delivery confirmation.
    </div>}
    {!visible && <p role="status">Choose a month and select Load business month. Nothing is fetched automatically.</p>}
    {visible && !visible.loading && !visible.error && rows.length>0 && <>
      <table className="rg-calendar-month-table" aria-label="All campaigns month grid">
        <thead><tr>{['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map(day=><th scope="col" key={day}>{day}</th>)}</tr></thead>
        <tbody>{Array.from({length:grid.length/7},(_,week)=><tr key={week}>
          {grid.slice(week*7,(week+1)*7).map(day=><td key={day.date} className={day.inMonth?'':'is-outside'}
            aria-label={day.date+': '+day.drafts+' planned days'}>
            <span className="rg-month-date">{day.day}</span>
            {day.drafts>0 && <span className="rg-month-count">{day.drafts} planned</span>}
          </td>)}
        </tr>)}</tbody>
      </table>
      <ol className="rg-shop-month-list" aria-label="Authorized campaign draft days">
        {rows.map(day=><li key={day.id}>
          <div><strong>{day.scheduled_date}</strong><span>{day.topic}</span></div>
          <Badge>{day.review_status} · not published</Badge>
        </li>)}
      </ol>
    </>}
    <p className="rg-library-safety">Reads only this shop's existing RLS-protected campaign-days table on demand (up to 200 rows for one month). A larger month fails closed. Publishing history belongs to Part 2.</p>
  </Card>
}
