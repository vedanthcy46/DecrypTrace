import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-[#3B82F6] text-white',
        success: 'border-transparent bg-[#10B981] text-white',
        warning: 'border-transparent bg-[#F59E0B] text-white',
        danger: 'border-transparent bg-[#EF4444] text-white',
        info: 'border-transparent bg-[#3B82F6]/20 text-[#3B82F6]',
        sender: 'border-transparent bg-[#8B5CF6]/20 text-[#8B5CF6]',
        recipient: 'border-transparent bg-[#10B981]/20 text-[#10B981]',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}
