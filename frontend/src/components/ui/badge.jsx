import { cn } from '../../lib/utils.mjs'
export function Badge({ className, ...props }) {
  return <span data-slot="badge" className={cn('inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold', className)} {...props} />
}
