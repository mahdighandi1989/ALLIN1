'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import NotificationBell from '@/components/NotificationBell'
import { LayoutDashboard, Users, Building, FileText, BarChart3, ShieldCheck, Trash2, ScrollText, FileSpreadsheet, Settings, LogOut, BookOpen } from 'lucide-react'

// A nav item may list extra path prefixes whose detail pages belong to it, so
// that e.g. /customer-detail/123 keeps the "Customers" item highlighted.
type NavItem = {
  href: string
  label: string
  icon: typeof LayoutDashboard
  match?: string[]
}

// Navigation is organised into labelled groups so related destinations are
// discoverable together instead of one long flat list. ``adminOnly`` groups are
// hidden from non-admins (and shown in the no-login demo mode).
type NavGroup = { title: string; adminOnly?: boolean; items: NavItem[] }

const NAV_GROUPS: NavGroup[] = [
  {
    title: 'Operations',
    items: [
      { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
      { href: '/customers', label: 'Customers', icon: Users, match: ['/customer-detail'] },
      { href: '/facilities', label: 'Facilities', icon: Building, match: ['/facility-detail'] },
      { href: '/offer-letters', label: 'Offer Letters', icon: FileText },
    ],
  },
  {
    title: 'Finance & Reports',
    items: [
      { href: '/reports', label: 'Reports', icon: BarChart3 },
      { href: '/knowledge', label: 'دانش‌نامه', icon: BookOpen },
      { href: '/import', label: 'Import', icon: FileSpreadsheet },
    ],
  },
  {
    title: 'System',
    adminOnly: true,
    items: [
      { href: '/users', label: 'Users', icon: ShieldCheck },
      { href: '/audit', label: 'Audit Log', icon: ScrollText },
      { href: '/settings', label: 'Settings', icon: Settings },
      { href: '/trash', label: 'Recycle Bin', icon: Trash2 },
    ],
  },
]

/** True when ``pathname`` is on ``item``'s route or one of its detail prefixes. */
function isNavActive(item: NavItem, pathname: string | null): boolean {
  if (!pathname) return false
  const prefixes = [item.href, ...(item.match ?? [])]
  return prefixes.some((p) => pathname === p || pathname.startsWith(p + '/') || pathname.startsWith(p))
}

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout, authDisabled } = useAuth()
  const pathname = usePathname()
  const showAdmin = authDisabled || !!user?.is_admin
  const groups = NAV_GROUPS.filter((g) => showAdmin || !g.adminOnly)

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b shadow-sm">
        <div className="container mx-auto px-4 flex items-center justify-between h-16">
          <div className="flex items-center gap-6">
            <span className="text-lg font-bold text-blue-600">Banking Ops</span>
            <nav className="flex items-center gap-4">
              {groups.map((group) => (
                <div key={group.title} className="flex items-center gap-1" aria-label={group.title}>
                  <span className="sr-only">{group.title}</span>
                  {group.items.map(({ href, label, icon: Icon, match }) => {
                    const active = isNavActive({ href, label, icon: Icon, match }, pathname)
                    return (
                      <Link
                        key={href}
                        href={href}
                        title={`${group.title}: ${label}`}
                        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                          active
                            ? 'bg-blue-50 text-blue-700'
                            : 'text-gray-600 hover:bg-gray-100'
                        }`}
                      >
                        <Icon size={18} />
                        {label}
                      </Link>
                    )
                  })}
                </div>
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <NotificationBell />
            <Link
              href="/profile"
              className="text-sm text-gray-600 hover:text-blue-600"
              title="My profile"
            >
              {user?.full_name || user?.username || 'Profile'}
            </Link>
            <button
              onClick={() => logout()}
              className="flex items-center gap-1 text-gray-500 hover:text-gray-700"
              title="Logout"
              type="button"
            >
              <LogOut size={20} />
            </button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">{children}</main>
    </div>
  )
}
