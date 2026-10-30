import { useEffect, useMemo, useRef, useState } from 'react'
import { useAuthorizedShops } from './useAuthorizedShops.js'
import { useSelectedShop } from './useSelectedShop.js'
import { Link } from 'react-router-dom'
import { useInfiniteQuery } from '@tanstack/react-query'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import { Card } from '../../components/ui/card.jsx'
import { Button } from '../../components/ui/button.jsx'
import { Badge } from '../../components/ui/badge.jsx'
import { Skeleton } from '../../components/ui/skeleton.jsx'
import { filterAssets, mediaLabel, mediaPreviewAccess, mediaPreviewRevision, currentMediaPreview, paginateVerifiedAssets } from './media-library-model.mjs'

export default function MediaLibrary() {
  const { client, configured, user } = useRetailAuth()
  const [filter, setFilter] = useState('')
  const [type, setType] = useState('all')
  const [paging, setPaging] = useState({scope:'',page:1})
  const [preview, setPreview] = useState(null)
  const previewUrl = useRef(null)
  const previewScope = useRef('')
  const requestEpoch = useRef(0)
  const shopsQuery = useAuthorizedShops({ client, user, configured })
  const shops = shopsQuery.isError ? [] : (shopsQuery.data || [])
  // Never fetch from an arbitrary user-supplied shop ID: resolve from RLS-backed memberships.
  const { shopId, selectShop } = useSelectedShop({ user, shops })
  const activeScope = (user?.id || '') + ':' + (shopId || '')
  previewScope.current = activeScope
  useEffect(() => {
    requestEpoch.current += 1
    if (previewUrl.current) { URL.revokeObjectURL(previewUrl.current); previewUrl.current = null }
    setPreview(null)
  }, [activeScope])
  useEffect(() => () => {
    requestEpoch.current += 1
    if (previewUrl.current) URL.revokeObjectURL(previewUrl.current)
  }, [])
  function closePrivateImage() {
    // A pending private Storage read must never reopen a dismissed preview.
    requestEpoch.current += 1
    if (previewUrl.current) URL.revokeObjectURL(previewUrl.current)
    previewUrl.current = null
    setPreview(null)
  }
  async function showPrivateImage(asset) {
    const revision = mediaPreviewRevision(asset,shopId)
    if (!user || !revision) return
    const epoch = ++requestEpoch.current
    const scope = activeScope
    // Dispose the previous authorized private URL even if the next read fails.
    if (previewUrl.current) URL.revokeObjectURL(previewUrl.current)
    previewUrl.current = null
    setPreview({scope,id:asset.id,revision,loading:true})
    try {
      const {blob, filename} = await client.downloadPrivateImage(shopId,asset.id)
      if (requestEpoch.current !== epoch || previewScope.current !== scope) return
      const url = URL.createObjectURL(blob)
      if (previewUrl.current) URL.revokeObjectURL(previewUrl.current)
      previewUrl.current = url
      setPreview({scope,id:asset.id,revision,url,filename,loading:false})
    } catch {
      if (requestEpoch.current === epoch && previewScope.current === scope) {
        setPreview({scope,id:asset.id,revision,error:'Private image could not be verified or accessed.',loading:false})
      }
    }
  }
  const assetsQuery = useInfiniteQuery({
    queryKey: ['media-library', 'keyset-v1', user?.id, shopId],
    queryFn: ({pageParam}) => client.listMediaAssetsKeysetPage(shopId, pageParam),
    initialPageParam: null,
    getNextPageParam: last => last.nextCursor ?? undefined,
    enabled: Boolean(configured && user && shopId),
    staleTime: 30000,
    retry: false,
    refetchOnWindowFocus: false,
  })
  // A private blob is only valid while the latest RLS-backed metadata still
  // identifies this same-shop record as an original UPLOAD. A refreshed
  // GENERATED/STOCK/revoked/missing asset must not leave a stale download link.
  const previewAuthorized = useMemo(() => Boolean(
    preview?.scope === activeScope && preview?.id &&
    assetsQuery.isSuccess &&
    currentMediaPreview(preview, assetsQuery.data?.pages, shopId)
  ), [preview, activeScope, assetsQuery.isSuccess, assetsQuery.data, shopId])
  useEffect(() => {
    if (!preview || preview.scope !== activeScope) return
    if (!shopsQuery.isError && !assetsQuery.isError &&
        (!assetsQuery.isSuccess || previewAuthorized)) return
    // Revocation/metadata failure invalidates both the displayed link and a
    // pending private byte read. Never rely on a previously authorized blob.
    requestEpoch.current += 1
    if (previewUrl.current) URL.revokeObjectURL(previewUrl.current)
    previewUrl.current = null
    setPreview(null)
  }, [preview?.id, preview?.scope, previewAuthorized, activeScope,
    shopsQuery.isError, assetsQuery.isError, assetsQuery.isSuccess])
  const assets = useMemo(() => {
    const unique = new Map()
    for (const page of assetsQuery.data?.pages || []) {
      for (const asset of page.items) if (!unique.has(asset.id)) unique.set(asset.id, asset)
    }
    return filterAssets([...unique.values()], shopId, filter, type)
  }, [assetsQuery.data, shopId, filter, type])
  const scope = user?.id + ':' + shopId + ':' + filter + ':' + type
  const view = paginateVerifiedAssets(assets, paging.scope === scope ? paging.page : 1)
  const movePage = next => setPaging({scope,page:next})
  const hasError = shopsQuery.isError || assetsQuery.isError
  const fetching = shopsQuery.isFetching || (assetsQuery.isFetching && !assetsQuery.isFetchingNextPage)
  const hasShops = !shopsQuery.isPending && shops.length > 0

  return <div className="rg-workspace-page rg-library">
    <div className="page-heading">
      <div><div className="eyebrow">AUTHORIZED BUSINESS ASSETS</div><h1>Media library</h1>
        <p className="lead">Browse registered images for one business with stable older-image pages that are not shifted by newer uploads. All results use your Supabase session and tenant RLS.</p></div>
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
          <Badge>{assetsQuery.hasNextPage ? 'Older records available — load more to include them in search' : 'No older records in this history'}</Badge></div>
        {assets.length === 0
          ? <p role="status">No matching registered images in the loaded pages. Upload licensed images or load older records if available.</p>
          : <div className="rg-library-grid" role="region" aria-label="Authorized media records">
              {view.items.map(asset => <Card className="rg-library-record" key={asset.id}>
                <div className="rg-library-icon" aria-hidden="true">▧</div>
                <div><strong>{mediaLabel(asset.id)}</strong>
                  <p>{asset.mime_type || 'Image type unavailable'}</p>
                  <span>Licence: {asset.license_name}</span>
                  {mediaPreviewAccess(asset, shopId).allowed
                    ? <Button variant="outline" size="sm" disabled={preview?.loading}
                        onClick={()=>showPrivateImage(asset)}>Preview {mediaLabel(asset.id)}</Button>
                    : <span>Private preview unavailable until ownership, rights and private access are verified</span>}
                </div>
              </Card>)}
            </div>}
        {previewAuthorized && !shopsQuery.isFetching && !assetsQuery.isFetching && !hasError &&
          <Card className="rg-private-preview" aria-label="Verified private image preview">
          <Button type="button" variant="outline" size="sm" onClick={closePrivateImage}>Close private preview</Button>
          {preview.loading && <p role="status">Reading private image with your current session…</p>}
          {preview.error && <p role="alert">{preview.error}</p>}
          {preview.url && <>
            <img src={preview.url} alt={'Authorized private image ' + mediaLabel(preview.id)}
              referrerPolicy="no-referrer"/>
            <Button asChild variant="outline"><a href={preview.url} download={preview.filename}
              referrerPolicy="no-referrer">Save private image</a></Button>
          </>}
        </Card>}
        {assetsQuery.hasNextPage && <Button type="button" variant="outline"
          disabled={assetsQuery.isFetchingNextPage} onClick={() => assetsQuery.fetchNextPage()}>
          {assetsQuery.isFetchingNextPage ? 'Loading older records…' : 'Load 100 older records'}
        </Button>}
        {assets.length > 12 && <nav className="rg-library-pager" aria-label="Media library pages">
          <Button variant="outline" size="sm" disabled={view.page === 1}
            onClick={()=>movePage(view.page-1)}>Previous images</Button>
          <span role="status" aria-live="polite">Page {view.page} of {view.pages} · Showing {view.first}–{view.last} of {view.total} matching images</span>
          <Button variant="outline" size="sm" disabled={view.page === view.pages}
            onClick={()=>movePage(view.page+1)}>Next images</Button>
        </nav>}
      </>}
      <p className="rg-library-safety">Registered uploads can be previewed on demand through your signed-in JWT and private Storage RLS. Images use temporary in-browser blob URLs, never public links or permanent signed URLs. Other source types require separate rights verification.</p>
    </Card>
  </div>
}
