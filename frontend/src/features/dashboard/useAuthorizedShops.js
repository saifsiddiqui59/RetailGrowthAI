import { useQuery } from '@tanstack/react-query'

// One short-lived, principal-scoped cache for shared sidebar/workspace business
// options. Each authorized operation still enforces PostgreSQL tenant RLS.
// The 8-second freshness window reduces redundant GETs during rapid navigation;
// 20-second garbage collection releases metadata once no page observes it.
export function useAuthorizedShops({ client, user, configured }) {
  return useQuery({
    queryKey: ['retailer-shops', user?.id || null],
    queryFn: () => client.listShops(),
    enabled: Boolean(configured && user?.id),
    retry: false,
    staleTime: 8_000,
    gcTime: 20_000,
  })
}
