import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-[#3B82F6] text-white hover:bg-[#3B82F6]/90',
        outline: 'border border-[#1E293B] bg-transparent hover:bg-[#1E293B] text-white',
        ghost: 'hover:bg-[#1E293B] text-[#E2E8F0]',
        sender: 'bg-[#8B5CF6] text-white hover:bg-[#8B5CF6]/90',
        recipient: 'bg-[#10B981] text-white hover:bg-[#10B981]/90',
        investigator: 'bg-[#F59E0B] text-white hover:bg-[#F59E0B]/90',
        danger: 'bg-[#EF4444] text-white hover:bg-[#EF4444]/90',
      },
      size: {
        sm: 'h-9 px-3',
        md: 'h-10 px-4 py-2',
        lg: 'h-11 px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
);

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(({ className, variant, size, ...props }, ref) => {
  return (
    <button className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
  );
});
Button.displayName = 'Button';
