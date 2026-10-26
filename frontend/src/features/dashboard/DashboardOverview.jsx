import { useAuthorizedShops } from './useAuthorizedShops.js'
import { useSelectedShop } from './useSelectedShop.js'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import sampleCampaign from '../campaigns/fixtures/sample-campaign.json'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import VerifiedMetricsChart from './VerifiedMetricsChart.jsx'
import { Skeleton } from '../../components/ui/skeleton.jsx'

const EMPTY = { campaigns: null, drafts: null, reelsReady: null, rendersProcessing: null }

export default function DashboardOverview() {
  const { client, configured, user, loading: authLoading } = useRetailAuth()
  // Keep query keys scoped to an authenticated principal. No stale counts are
  // shared with another user or business; the backend still enforces RLS.
  const shopsQuery = useAuthorizedShops({ client, user, configured })
  const shops = shopsQuery.data || []
  const { shopId, selectShop } = useSelectedShop({ user, shops })
  const live = configured && Boolean(user)
  const metricsQuery = useQuery({
    queryKey: ['dashboard', 'shop-metrics', user?.id, shopId],
    queryFn: () => client.getShopMetrics(shopId),
    enabled: Boolean(live && shopId),
  })
  const stats = metricsQuery.data || EMPTY
  const pending = shopsQuery.isPending && shopsQuery.isFetching || metricsQuery.isFetching
  const error = shopsQuery.isError
    ? 'Unable to load your businesses. Refresh and try again.'
    : metricsQuery.isError ? 'Live dashboard metrics could not be loaded. No totals are estimated.' : ''

  const cards = live ? [
    { title: 'Campaigns created', value: stats.campaigns, hint: 'All recorded statuses' },
    { title: 'Draft campaigns', value: stats.drafts, hint: 'Awaiting review' },
    { title: 'Reels completed', value: stats.reelsReady, hint: 'Render jobs succeeded' },
    { title: 'Renders processing', value: stats.rendersProcessing, hint: 'Queued or running' },
  ] : [
    { title: 'Mock campaign days', value: sampleCampaign.days.length, hint: 'Example data, not your business' },
    { title: 'Sample channels', value: 2, hint: 'LinkedIn & Instagram mock' },
    { title: 'Sample reel target', value: '30s', hint: 'Illustrative storyboard only' },
  ]

  return (
    <div className="overview">
      <div className="page-heading">
        <div><div className="eyebrow">PERFORMANCE OVERVIEW</div><h1>Campaign workspace</h1>
          <p className="lead">{live
            ? 'Your business campaign and render activity, securely counted from your RetailGrowthAI DEV workspace.'
            : 'Create, review and render marketing campaigns. Sign in to see real business metrics.'}</p></div>
        <Link className="primary-action" to="/campaigns">Open campaign studio <span aria-hidden="true">→</span></Link>
      </div>
      <div className="dashboard-filter-row">
        {live && shops.length > 0 && <label>Business
          <select aria-label="Dashboard business" value={shopId} onChange={(event) => selectShop(event.target.value)}>
            {shops.map((shop) => <option key={shop.id} value={shop.id}>{shop.name}</option>)}
          </select></label>}
        <span className={'data-mode ' + (live ? 'is-live' : 'is-demo')}>{live ? 'LIVE · Tenant-secured' : 'DEMO · Sample data'}</span>
      </div>
      {error && <p role="alert" className="notice-error">{error} <button type="button" onClick={() => {
        if (shopsQuery.isError) shopsQuery.refetch()
        else metricsQuery.refetch()
      }}>Retry</button></p>}
      {!authLoading && live && !shopsQuery.isPending && !shops.length && !error && <p role="status">No accessible businesses yet. <Link to="/account">Create a business in Account.</Link></p>}
      {pending && <p role="status">Loading verified business metrics…</p>}
      <section className="metrics" aria-label={live ? 'Live business metrics' : 'Illustrative metrics'}>
        {cards.map((item) => <section className="metric" key={item.title}>
          <span>{item.title}</span>
          {pending && live ? <Skeleton className="rg-skeleton" aria-hidden="true" /> : <strong>{item.value ?? '—'}</strong>}
          <small>{item.hint}</small>
        </section>)}
      </section>
      {live && !error && !pending && <section className="panel rg-chart-panel" aria-label="Verified business analytics">
        <div className="eyebrow">VERIFIED ACTIVITY</div><h2>Campaign and render records</h2>
        <VerifiedMetricsChart title="Your business records" labels={['Campaigns', 'Drafts', 'Completed Reels', 'Processing']}
          values={[stats.campaigns, stats.drafts, stats.reelsReady, stats.rendersProcessing]} />
      </section>}
      <div className="dashboard-section-grid">
        <section className="panel">
          <div className="eyebrow">YOUR WORKFLOW</div><h2>From idea to campaign</h2>
          <p>1. Add your business and approved images. 2. Generate and edit your campaign. 3. Render a private vertical video and download it.</p>
          <Link className="text-link" to="/campaigns">Create or review campaigns →</Link>
          <p><Link className="text-link" to="/creative-studio">Explore Creative Studio →</Link></p>
        </section>
        <section className="panel">
          <div className="eyebrow">SUBSCRIPTION</div><h2>Track your usage</h2>
          <p>Review your server-managed trial, reserved campaign and render allowances, and expiry dates. Paid checkout is not available yet.</p>
          <Link className="text-link" to="/subscription">View plan &amp; usage →</Link>
          <p><Link className="text-link" to="/calendar">Campaign calendar →</Link></p>
        </section>
      </div>
      <section className="panel dashboard-analytics-note">
        <div className="eyebrow">ANALYTICS SCOPE</div><h2>What the metrics show</h2>
        <p>{live
          ? 'Counts come from your own shop-scoped, RLS-protected campaigns and render jobs. No estimated impressions, follower growth, published posts or revenue are shown.'
          : 'The sample figures above are only local fixture data. They are not usage, spend, published post counts, follower counts or customer engagement.'} Social reach and engagement metrics require approved platform connections in Part 2.</p>
      </section>
    </div>
  )
}
