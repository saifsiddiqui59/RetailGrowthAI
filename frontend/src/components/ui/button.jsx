import { Slot } from '@radix-ui/react-slot'
import { cva } from 'class-variance-authority'
import { cn } from '../../lib/utils.mjs'

export const buttonVariants = cva(
  'inline-flex shrink-0 items-center justify-center gap-2 rounded-lg text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  { variants: {
    variant: {
      default: 'bg-emerald-700 text-white hover:bg-emerald-800',
      outline: 'border border-slate-200 bg-white text-emerald-800 hover:bg-emerald-50',
      ghost: 'text-slate-700 hover:bg-slate-100',
    },
    size: { default: 'h-10 px-4 py-2', sm: 'h-8 px-3', icon: 'h-9 w-9' },
  }, defaultVariants: { variant: 'default', size: 'default' } },
)

export function Button({ asChild = false, variant = 'default', size = 'default', className, ...props }) {
  const Component = asChild ? Slot : 'button'
  return <Component data-slot="button" className={cn(buttonVariants({ variant, size }), className)}
    {...(!asChild ? { type: props.type || 'button' } : {})} {...props} />
}
