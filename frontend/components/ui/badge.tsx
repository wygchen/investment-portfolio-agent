import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center justify-center border font-medium w-fit whitespace-nowrap shrink-0 [&>svg]:size-3 gap-1 [&>svg]:pointer-events-none focus-visible:outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive transition-[color,box-shadow] overflow-hidden',
  {
    variants: {
      variant: {
        default:
          'border-transparent bg-primary text-primary-foreground [a&]:hover:bg-primary/90 hover:bg-primary/80',
        secondary:
          'border-transparent bg-secondary text-secondary-foreground [a&]:hover:bg-secondary/90 hover:bg-secondary/80',
        destructive:
          'border-transparent bg-destructive text-white [a&]:hover:bg-destructive/90 hover:bg-destructive/80 focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/40 dark:bg-destructive/60',
        outline:
          'text-foreground [a&]:hover:bg-accent [a&]:hover:text-accent-foreground',
      },
      shape: {
        default: 'rounded-md',
        pill: 'rounded-full',
      },
      size: {
        default: 'text-xs px-2 py-0.5',
        sm: 'text-[10px] px-1.5 py-0.5',
        lg: 'text-sm px-3 py-1',
      },
    },
    compoundVariants: [
      {
        shape: 'pill',
        size: 'default',
        class: 'px-2.5',
      },
      {
        shape: 'pill',
        size: 'sm',
        class: 'px-2',
      },
      {
        shape: 'pill',
        size: 'lg',
        class: 'px-4',
      },
    ],
    defaultVariants: {
      variant: 'default',
      shape: 'default',
      size: 'default',
    },
  },
)

export interface BadgeProps 
  extends Omit<React.ComponentProps<'span'>, 'ref'>,
    VariantProps<typeof badgeVariants> {
  asChild?: boolean
}

function Badge({ className, variant, shape, size, asChild = false, ...props }: BadgeProps) {
  const Comp = asChild ? Slot : 'span'

  return (
    <Comp
      data-slot="badge"
      className={cn(badgeVariants({ variant, shape, size }), className)}
      {...props}
    />
  )
}

export { Badge, badgeVariants }
