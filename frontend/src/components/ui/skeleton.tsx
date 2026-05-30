import React from 'react'

function cx(...classes: Array<string | undefined>): string {
  return classes.filter(Boolean).join(' ')
}

export function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cx('animate-pulse rounded-md bg-gray-200', className)}
      {...props}
    />
  )
}
