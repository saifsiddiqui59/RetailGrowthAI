import { useMemo, useState } from 'react'
import { useAuthorizedShops } from './useAuthorizedShops.js'
import { useSelectedShop } from './useSelectedShop.js'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import { Card } from '../../components/ui/card.jsx'
import { Button } from '../../components/ui/button.jsx'
import { Badge } from '../../components/ui/badge.jsx'
import { Skeleton } from '../../components/ui/skeleton.jsx'
import { filterAssets, mediaLabel, paginateVerifiedAssets } from './media-library-model.mjs'

export default function MediaLibrary() {
  const { client, configured, user } = useRetailAuth()
  const [filter, setFilter] = useState('')
  const [type, setType] = useState('all')
  const [paging, setPaging] = useState({scope:'',page:1})
  const shopsQuery = useAuthorizedShops({ client, user, configured })
  const shops = shopsQuery.data || []
  // Never fetch from an arbitrary user-supplied shop ID: resolve from RLS-backed memberships.
  const { shopId, selectShop } = useSelectedShop({ user, shops })
  const assetsQuery = useQuery({
    queryKey: ['media-library', 'assets', user?.id, shopId],
    queryFn: () => client.listMediaAssets(shopId),
    enabled: Boolean(configured && user && shopId),
    staleTime: 30000,
    retry: false,
  })
  const assets = useMemo(() => filterAssets(assetsQuery.data || [], shopId, filter, type),
    [assetsQuery.data, shopId, filter, type])
  const scope = user?.id + ':' + shopId + ':' + filter + ':' + type
  const view = paginateVerifiedAssets(assets, paging.scope === scope ? paging.page : 1)
  const movePage = next => setPaging({scope,page:next})
  const hasError = shopsQuery.isError || assetsQuery.isError
  const fetching = shopsQuery.isFetching || assetsQuery.isFetching
  const hasShops = !shopsQuery.isPending && shops.length > 0

  return <div className="rg-workspace-page rg-library">
    <div className="page-heading">
      <div><div className="eyebrow">AUTHORIZED BUSINESS ASSETS</div><h1>Media library</h1>
        <p className="lead">Browse the latest registered images for one business. All results are returned through your Supabase session and tenant RLS.</p></div>
      <Button asChild className="primary-action rg-workspace-cta"><Link to="/campaigns">Upload an image</Link></Button>
    </div>
    <Card className="panel">
      {!configured && <p role="status">Connect RetailGrowthAI DEV Supabase to browse your private image records. No demo images are presented as uploads.</p>}
      {configured && user && <div className="rg-library-tools">
        <label>Business
          <select aria-label="Media library business" value={shopId} onChange={event => {setPaging({scope:'',page:1});selectShop(event.target.value)}}>
            {!shops.length && <option value="">No accessible business</option>}
            {shops.map(shop => <option key={shop.id} value={shop.id}>{shop.name}</option>)}
          </select>
        </label>
        <label>Search asset ID or licence
          <input aria-label="Search media" type="search" maxLength={80} value={filter}
            onChange={event => {setPaging({scope:'',page:1});setFilter(event.target.value)}} placeholder="Filter current business" />
        </label>
        <label>Type
          <select aria-label="Media file type" value={type} onChange={event => {setPaging({scope:'',page:1});setType(event.target.value)}}>
            <option value="all">All images</option><option value="image/png">PNG</option>
            <option value="image/jpeg">JPEG</option><option value="image/webp">WebP</option>
          </select>
        </label>
        <Button type="button" variant="outline" className="subtle-button" disabled={!shopId || fetching}
          onClick={() => assetsQuery.refetch()}>Refresh assets</Button>
      </div>}
      {fetching && <div role="status" aria-label="Loading media"><Skeleton className="rg-skeleton" />Loading registered images…</div>}
      {hasError && <p role="alert">Private media metadata could not be verified. No files or totals are estimated.
        <Button variant="outline" size="sm" onClick={() => shopsQuery.isError ? shopsQuery.refetch() : assetsQuery.refetch()}>Retry</Button>
      </p>}
      {configured && !fetching && !hasError && !hasShops && <p role="status">No accessible businesses. <Link to="/account">Create or join a business in Account.</Link></p>}
      {configured && hasShops && !fetching && !hasError && <>
        <div className="rg-library-summary"><strong>{assets.length} matching registered images</strong>
          <Badge>Searching only the 100 newest records; older images may not appear</Badge></div>
        {assets.length === 0
          ? <p role="status">No matching registered images in this business. Upload licensed images through Campaign Studio.</p>
          : <div className="rg-library-grid" role="region" aria-label="Authorized media records">
              {view.items.map(asset => <Card className="rg-library-record" key={asset.id}>
                <div className="rg-library-icon" aria-hidden="true">▧</div>
                <div><strong>{mediaLabel(asset.id)}</strong>
                  <p>{asset.mime_type || 'Image type unavailable'}</p>
                  <span>Licence: {asset.license_name}</span>
                </div>
              </Card>)}
            </div>}
        {assets.length > 12 && <nav className="rg-library-pager" aria-label="Media library pages">
          <Button variant="outline" size="sm" disabled={view.page === 1}
            onClick={()=>movePage(view.page-1)}>Previous images</Button>
          <span role="status" aria-live="polite">Page {view.page} of {view.pages} · Showing {view.first}–{view.last} of {view.total} matching images</span>
          <Button variant="outline" size="sm" disabled={view.page === view.pages}
            onClick={()=>movePage(view.page+1)}>Next images</Button>
        </nav>}
      </>}
      <p className="rg-library-safety">Files remain private. Metadata is not a signed image URL; no direct blob links, public sharing, delete operations or unverified rights are offered here.</p>
    </Card>
  </div>
}
