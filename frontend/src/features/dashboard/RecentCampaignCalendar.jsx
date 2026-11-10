import { useEffect, useMemo, useRef, useState } from 'react'
import { useAuthorizedShops } from './useAuthorizedShops.js'
import { useSelectedShop } from './useSelectedShop.js'
import { Link } from 'react-router-dom'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import { createCampaignApi } from '../campaigns/campaign-api.mjs'
import { Card } from '../../components/ui/card.jsx'
import ShopMonthCalendar from './ShopMonthCalendar.jsx'
import { Button } from '../../components/ui/button.jsx'
import { Badge } from '../../components/ui/badge.jsx'
import { recentCampaignHint, verifiedCampaignDays, verifiedDraftMonths, draftMonthCells } from './recent-calendar-model.mjs'

export default function RecentCampaignCalendar() {
  const { client, configured, user } = useRetailAuth()
  const [campaign, setCampaign] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [requestedMonth, setRequestedMonth] = useState('')
  const requestEpoch = useRef(0)
  useEffect(() => () => { requestEpoch.current += 1 }, [])
  const shopsQuery = useAuthorizedShops({ client, user, configured })
  const shops = shopsQuery.data || []
  const { shopId, selectShop } = useSelectedShop({ user, shops })
  const api = useMemo(() => createCampaignApi({
    baseUrl: import.meta.env?.VITE_CAMPAIGN_API_BASE_URL || '',
    tokenProvider: () => client.getAccessToken(),
    supabaseOrigin: import.meta.env?.VITE_SUPABASE_URL || '',
    supabasePublishableKey: import.meta.env?.VITE_SUPABASE_PUBLISHABLE_KEY || '',
  }), [client])
  // A membership refresh can switch the authorized shop while the page stays
  // mounted. Never render status or draft dates from the previous business.
  const verifiedCampaign = campaign?.shop_id === shopId ? campaign : null
  const days = verifiedCampaign ? verifiedCampaignDays(verifiedCampaign, shopId) : []
  const months = verifiedDraftMonths(days)
  const month = months.includes(requestedMonth) ? requestedMonth : months[0] || ''
  const monthCells = draftMonthCells(days, month)
  const currentMonthDays = days.filter(day => day.scheduled_date.startsWith(month))
  const eligible = Boolean(user && configured && shopId && api)

  async function fetchRecent() {
    if (!eligible || loading) return
    setError('')
    setCampaign(null)
    setRequestedMonth('')
    let hint
    try { hint = recentCampaignHint(window.sessionStorage, user.id, shopId) }
    catch {
      setError('Recent campaign preference could not be accessed in this browser. Open Campaign Studio to review an authorized draft.')
      return
    }
    if (!hint) {
      setError('No recent campaign is saved in this browser session for this business. Open Campaign Studio to create or review one.')
      return
    }
    setLoading(true)
    const epoch = ++requestEpoch.current
    try {
      const result = await api.getCampaign(hint)
      if (!result || result.shop_id !== shopId || result.id !== hint ||
          !['DRAFT', 'PLANNING', 'FAILED'].includes(result.status)) {
        throw new Error('Campaign access or status could not be verified.')
      }
      if (requestEpoch.current === epoch) setCampaign(result)
    } catch {
      if (requestEpoch.current === epoch) setError('Recent campaign could not be verified through the authenticated API. No dates or posts are assumed. Azure DEV API may be unavailable.')
    } finally {
      if (requestEpoch.current === epoch) setLoading(false)
    }
  }

  return <div className="rg-workspace-page rg-campaign-calendar-page">
    <div className="page-heading"><div><div className="eyebrow">RECENT CAMPAIGN / DRAFT SCHEDULE</div>
      <h1>Campaign calendar</h1>
      <p className="lead">Review verified dates from your latest campaign in this browser session. Draft dates are not social publishing confirmations.</p>
    </div><Button asChild className="primary-action rg-workspace-cta"><Link to="/campaigns">Open campaign studio</Link></Button></div>
    <Card className="panel">
      {!eligible && <p role="status">Sign in and select a business with the RetailGrowthAI DEV campaign API configured to view authorized campaign dates.</p>}
      {eligible && <>
        <div className="rg-library-tools">
          <label>Business
            <select aria-label="Calendar business" value={shopId}
              onChange={event=>{requestEpoch.current += 1;setLoading(false);selectShop(event.target.value);setCampaign(null);setRequestedMonth('');setError('')}}>
              {shops.map(shop=><option value={shop.id} key={shop.id}>{shop.name}</option>)}
            </select>
          </label>
          <Button variant="outline" className="subtle-button" disabled={loading}
            onClick={fetchRecent}>{loading ? 'Checking…' : 'Load recent campaign'}</Button>
        </div>
        {error && <p role="alert">{error}</p>}
        {verifiedCampaign && <div className="rg-library-summary" role="status">
          <Badge>Verified campaign: {verifiedCampaign.status}</Badge>
          <span>{days.length} verified draft dates in this campaign</span>
        </div>}
        {!!days.length && <section className="rg-calendar-month" aria-label="Recent verified draft month">
          <div className="rg-calendar-month-toolbar">
            <div><h2>Draft month view</h2><p>Only dates verified for this one campaign are marked; none are published.</p></div>
            <label>View month
              <select aria-label="Draft month" value={month} onChange={event=>setRequestedMonth(event.target.value)}>
                {months.map(key=><option key={key} value={key}>{new Intl.DateTimeFormat('en-IN',{month:'long',year:'numeric',timeZone:'UTC'}).format(new Date(key+'-01T12:00:00Z'))}</option>)}
              </select>
            </label>
          </div>
          <table className="rg-calendar-month-table" aria-label="Verified draft month grid">
            <thead><tr>{['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map(weekday=><th scope="col" key={weekday}>{weekday}</th>)}</tr></thead>
            <tbody>{Array.from({length:monthCells.length/7},(_,week)=><tr key={week}>
              {monthCells.slice(week*7,(week+1)*7).map(cell=><td key={cell.date} className={cell.inMonth?'':'is-outside'}
                aria-label={cell.date + (cell.drafts ? ': '+cell.drafts+' unpublished drafts' : ': no verified draft')}>
                <span className="rg-month-date">{cell.day}</span>
                {cell.drafts > 0 && <span className="rg-month-count">{cell.drafts} draft{cell.drafts === 1 ? '' : 's'}</span>}
              </td>)}
            </tr>)}</tbody>
          </table>
        </section>}
        {!!currentMonthDays.length && <div className="rg-calendar-grid" aria-label="Verified campaign day schedule">
          {currentMonthDays.map(day=><Card className="rg-verified-calendar-day" key={day.id}>
            <div className="rg-calendar-date"><strong>{day.scheduled_date}</strong>
              <Badge>{day.review_status}</Badge></div>
            <h2>{day.topic}</h2><span>Day {day.day_index} · Not published</span>
          </Card>)}
        </div>}
        {verifiedCampaign && !days.length && <p role="status">No verified draft schedule is available. Campaign status: {verifiedCampaign.status}.</p>}
      </>}
      <p className="rg-library-safety">This is the most recent per-user/per-shop campaign hint, not a cross-campaign calendar. No publishing or media job is triggered. Global calendars remain part of Feature #6 integration.</p>
    </Card>
    <ShopMonthCalendar client={client} configured={configured} user={user} shopId={shopId}/>
  </div>
}
