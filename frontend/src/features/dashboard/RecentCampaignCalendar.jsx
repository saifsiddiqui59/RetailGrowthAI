import { useEffect, useMemo, useRef, useState } from 'react'
import { useAuthorizedShops } from './useAuthorizedShops.js'
import { Link } from 'react-router-dom'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import { createCampaignApi } from '../campaigns/campaign-api.mjs'
import { Card } from '../../components/ui/card.jsx'
import { Badge } from '../../components/ui/badge.jsx'
import { recentCampaignHint, verifiedCampaignDays } from './recent-calendar-model.mjs'

export default function RecentCampaignCalendar() {
  const { client, configured, user } = useRetailAuth()
  const [requestedShopId, setRequestedShopId] = useState('')
  const [campaign, setCampaign] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const requestEpoch = useRef(0)
  useEffect(() => () => { requestEpoch.current += 1 }, [])
  const shopsQuery = useAuthorizedShops({ client, user, configured })
  const shops = shopsQuery.data || []
  const shopId = shops.some(shop => shop.id === requestedShopId)
    ? requestedShopId : shops[0]?.id || ''
  const api = useMemo(() => createCampaignApi({
    baseUrl: import.meta.env?.VITE_CAMPAIGN_API_BASE_URL || '',
    tokenProvider: () => client.getAccessToken(),
    supabaseOrigin: import.meta.env?.VITE_SUPABASE_URL || '',
    supabasePublishableKey: import.meta.env?.VITE_SUPABASE_PUBLISHABLE_KEY || '',
  }), [client])
  const days = campaign ? verifiedCampaignDays(campaign, shopId) : []
  const eligible = Boolean(user && configured && shopId && api)

  async function fetchRecent() {
    if (!eligible || loading) return
    setError('')
    setCampaign(null)
    const hint = recentCampaignHint(window.sessionStorage, user.id, shopId)
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

  return <div className="rg-workspace-page rg-calendar">
    <div className="page-heading"><div><div className="eyebrow">RECENT CAMPAIGN / DRAFT SCHEDULE</div>
      <h1>Campaign calendar</h1>
      <p className="lead">Review verified dates from your latest campaign in this browser session. Draft dates are not social publishing confirmations.</p>
    </div><Link to="/campaigns" className="primary-action">Open campaign studio</Link></div>
    <Card className="panel">
      {!eligible && <p role="status">Sign in and select a business with the RetailGrowthAI DEV campaign API configured to view authorized campaign dates.</p>}
      {eligible && <>
        <div className="rg-library-tools">
          <label>Business
            <select aria-label="Calendar business" value={shopId}
              onChange={event=>{requestEpoch.current += 1;setLoading(false);setRequestedShopId(event.target.value);setCampaign(null);setError('')}}>
              {shops.map(shop=><option value={shop.id} key={shop.id}>{shop.name}</option>)}
            </select>
          </label>
          <button className="subtle-button" type="button" disabled={loading}
            onClick={fetchRecent}>{loading ? 'Checking…' : 'Load recent campaign'}</button>
        </div>
        {error && <p role="alert">{error}</p>}
        {campaign && <div className="rg-library-summary" role="status">
          <Badge>Verified campaign: {campaign.status}</Badge>
          <span>{days.length} verified draft dates in this campaign</span>
        </div>}
        {!!days.length && <div className="rg-calendar-grid" aria-label="Verified campaign day schedule">
          {days.map(day=><article className="rg-calendar-day" key={day.id}>
            <div className="rg-calendar-date"><strong>{day.scheduled_date}</strong>
              <Badge>{day.review_status}</Badge></div>
            <h2>{day.topic}</h2><span>Day {day.day_index} · Not published</span>
          </article>)}
        </div>}
        {campaign && !days.length && <p role="status">No verified draft schedule is available. Campaign status: {campaign.status}.</p>}
      </>}
      <p className="rg-library-safety">This is the most recent per-user/per-shop campaign hint, not a cross-campaign calendar. No publishing or media job is triggered. Global calendars remain part of Feature #6 integration.</p>
    </Card>
  </div>
}
