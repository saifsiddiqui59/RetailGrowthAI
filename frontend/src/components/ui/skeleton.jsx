import { cn } from '../../lib/utils.mjs'
export function Skeleton({ className, ...props }) {
  return <div data-slot="skeleton" aria-hidden="true" className={cn('animate-pulse rounded-lg bg-slate-100', className)} {...props} />
}
