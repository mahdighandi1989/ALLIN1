import React from 'react'

type DivProps = React.HTMLAttributes<HTMLDivElement>

function cx(...classes: Array<string | undefined>): string {
  return classes.filter(Boolean).join(' ')
}

export function Card({ className, ...props }: DivProps) {
  return (
    <div
      className={cx('rounded-lg border bg-white text-gray-900 shadow-sm', className)}
      {...props}
    />
  )
}

export function CardHeader({ className, ...props }: DivProps) {
  return <div className={cx('flex flex-col space-y-1.5 p-6', className)} {...props} />
}

export function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cx('text-lg font-semibold leading-none tracking-tight', className)}
      {...props}
    />
  )
}

export function CardContent({ className, ...props }: DivProps) {
  return <div className={cx('p-6 pt-0', className)} {...props} />
}

export function CardFooter({ className, ...props }: DivProps) {
  return <div className={cx('flex items-center p-6 pt-0', className)} {...props} />
}
