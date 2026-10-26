import { cn } from '../../lib/utils.mjs'

export function Card({ className, ...props }) {
  return <section data-slot="card" className={cn('rounded-xl border border-slate-200 bg-white shadow-sm', className)} {...props} />
}
export function CardHeader({ className, ...props }) {
  return <div data-slot="card-header" className={cn('flex flex-col gap-1 p-6', className)} {...props} />
}
export function CardTitle({ className, ...props }) {
  return <h2 data-slot="card-title" className={cn('text-xl font-semibold', className)} {...props} />
}
export function CardContent({ className, ...props }) {
  return <div data-slot="card-content" className={cn('p-6 pt-0', className)} {...props} />
}
