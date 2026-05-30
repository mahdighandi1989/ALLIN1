import React from 'react'

type Variant = 'default' | 'destructive'

function cx(...classes: Array<string | undefined>): string {
  return classes.filter(Boolean).join(' ')
}

const VARIANTS: Record<Variant, string> = {
  default: 'bg-white text-gray-900 border-gray-200',
  destructive: 'border-red-300 bg-red-50 text-red-800',
}

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: Variant
}

export function Alert({ className, variant = 'default', ...props }: AlertProps) {
  return (
    <div
      role="alert"
      className={cx(
        'relative w-full rounded-lg border p-4 flex items-start gap-3',
        VARIANTS[variant],
        className
      )}
      {...props}
    />
  )
}

export function AlertTitle({
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h5 className={cx('mb-1 font-medium leading-none tracking-tight', className)} {...props} />
  )
}

export function AlertDescription({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cx('text-sm', className)} {...props} />
}
