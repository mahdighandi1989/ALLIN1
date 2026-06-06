import React from 'react'

function cx(...classes: Array<string | undefined>): string {
  return classes.filter(Boolean).join(' ')
}

export interface PageHeaderProps {
  /** Page title, rendered as the primary heading. */
  title: string
  /** Optional supporting line under the title. */
  subtitle?: string
  /** Optional right-aligned actions (buttons, filters, etc.). */
  actions?: React.ReactNode
  className?: string
}

/**
 * Consistent page header (title + optional subtitle + actions) so every page
 * presents its heading and primary actions the same way, instead of each page
 * hand-rolling a slightly different `flex justify-between` block.
 */
export function PageHeader({ title, subtitle, actions, className }: PageHeaderProps) {
  return (
    <div className={cx('flex flex-wrap items-center justify-between gap-3 mb-6', className)}>
      <div>
        <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
        {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  )
}

export default PageHeader
