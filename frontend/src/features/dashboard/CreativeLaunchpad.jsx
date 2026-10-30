import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import { useAuthorizedShops } from './useAuthorizedShops.js'
import { useSelectedShop } from './useSelectedShop.js'
import { creativeReadiness, validatedCreativeProfile } from './creative-readiness-model.mjs'
import { Badge } from '../../components/ui/badge.jsx'
import { Button } from '../../components/ui/button.jsx'
import { Card } from '../../components/ui/card.jsx'
import { Skeleton } from '../../components/ui/skeleton.jsx'

const STAGES = [
  { step: '01', title: 'Discover a trend', description: 'Review trend evidence and save a content idea for your business.',
    to: '/trends', action: 'Open Trend Intelligence' },
  { step: '02', title: 'Prepare approved media', description: 'Review licensed images registered to your own business.',
    to: '/media-library', action: 'View Media Library' },
  { step: '03', title: 'Design your campaign', description: 'Edit posters and Reel storyboards in the existing Campaign Studio.',
    to: '/campaigns', action: 'Open Campaign Studio' },
  { step: '04', title: 'Review draft dates', description: 'Inspect the latest verified campaign schedule. Draft is not published.',
    to: '/calendar', action: 'Open Draft Calendar' },
]

export default function CreativeLaunchpad() {
  const { client, user, configured } = useRetailAuth()
  const shopsQuery = useAuthorizedShops({ client, user, configured })
  const shops = shopsQuery.data || []
  // Never use an unchecked URL value or user-entered business ID.
  const { shopId, selectShop } = useSelectedShop({ user, shops })
  const profileQuery = useQuery({
    queryKey: ['creative-launchpad', 'profile', user?.id, shopId],
    queryFn: async () => {
      const record = await client.getBusinessProfile(shopId)
      if (!record) return null
      if (!validatedCreativeProfile(record, shopId)) throw new Error('Unverified business profile scope')
      return record
    },
    enabled: Boolean(configured && user && shopId),
    retry: false,
    staleTime: 20_000,
    gcTime: 0,
  })
  const readiness = creativeReadiness(profileQuery.data, shopId)
  const error = shopsQuery.isError || profileQuery.isError
  const loading = shopsQuery.isPending && shopsQuery.isFetching || profileQuery.isPending && profileQuery.isFetching
  return <div className="rg-workspace-page rg-creative-launchpad">
    <div className="page-heading">
      <div><div className="eyebrow">CREATE &amp; MANAGE</div><h1>Creative Studio</h1>
        <p className="lead">One workflow for retailer trend research, licensed images, campaign designs and draft review. Each tool remains under its existing authorization rules.</p>
      </div><Button asChild><Link to="/campaigns">Start designing</Link></Button>
    </div>
    <div className="rg-creative-tools">
      <Badge className="rg-state-label">No fabricated live data</Badge>
      <span>Content readiness is guidance from your business profile—not AI generation, publishing or approval status.</span>
    </div>
    <div className="rg-creative-layout">
      <Card className="panel rg-creative-readiness" aria-label="Business profile readiness">
        <div className="rg-settings-top"><div><div className="eyebrow">RETAILER CONTEXT</div><h2>Make content feel like your shop</h2></div>
          <Button asChild variant="outline" size="sm"><Link to="/settings">Edit profile</Link></Button>
        </div>
        {!configured && <p role="status">Connect your dedicated RetailGrowthAI account to review actual business details.</p>}
        {configured && user && <>
          <label className="rg-creative-shop">Business
            <select aria-label="Creative Studio business" value={shopId}
              onChange={event => selectShop(event.target.value)}>
              {!shopId && <option value="">No accessible business</option>}
              {shops.map(shop => <option key={shop.id} value={shop.id}>{shop.name}</option>)}
            </select>
          </label>
          {loading && <div role="status"><Skeleton className="rg-skeleton" />Loading your verified business profile…</div>}
          {error && <p role="alert">Business profile could not be verified. No readiness details are assumed.
            <Button variant="outline" size="sm" onClick={() => shopsQuery.isError ? shopsQuery.refetch() : profileQuery.refetch()}>Retry</Button>
          </p>}
          {!loading && !error && shopsQuery.isSuccess && !shops.length &&
            <p role="status">No accessible business yet. <Link to="/account">Create a business first.</Link></p>}
          {!loading && !error && shopId && profileQuery.isSuccess && !profileQuery.data &&
            <p role="status">No verified business profile exists for this shop. Review <Link to="/account">Account</Link>.</p>}
          {!loading && !error && readiness && <>
            <p className="rg-creative-score" role="status"><strong>{readiness.completed} of {readiness.total}</strong> profile details provided</p>
            <progress aria-label="Business content context completeness" value={readiness.completed} max={readiness.total} />
            <ul className="rg-creative-checklist" aria-label="Business content checklist">
              {readiness.checks.map(check => <li key={check.key}>
                <span className={check.satisfied ? 'rg-creative-check done' : 'rg-creative-check'}
                  aria-hidden="true">{check.satisfied ? '✓' : '·'}</span>
                <div><strong>{check.label}</strong>
                  <span>{check.satisfied ? 'Provided' : check.guidance}</span></div>
              </li>)}
            </ul>
          </>}
        </>}
      </Card>
      <Card className="panel rg-creative-flow" aria-label="Creative workflow">
        <div className="eyebrow">YOUR CREATIVE WORKFLOW</div><h2>From idea to a reviewable draft</h2>
        <ol className="rg-creative-stages">
          {STAGES.map(stage => <li key={stage.step}>
            <span className="rg-creative-number" aria-hidden="true">{stage.step}</span>
            <div><h3>{stage.title}</h3><p>{stage.description}</p>
              <Button variant="outline" size="sm" asChild><Link to={stage.to}>{stage.action}</Link></Button>
            </div>
          </li>)}
        </ol>
      </Card>
    </div>
    <Card className="panel rg-creative-notice">
      <strong>Publishing is a separate step.</strong>
      <p>Opening these tools does not schedule or publish anything. Poster/video cloud rendering, AI content generation, social connections and delivery receipts depend on their own validated backend workflows. No credits are spent by this page.</p>
    </Card>
  </div>
}
