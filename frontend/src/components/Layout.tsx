'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import NotificationBell from '@/components/NotificationBell'
import {
  LayoutDashboard, Users, Building, FileText, BarChart3, ShieldCheck, Trash2,
  ScrollText, FileSpreadsheet, Settings, LogOut, BookOpen, Building2, Landmark,
  LayoutGrid,
} from 'lucide-react'

// A nav item may list extra path prefixes whose detail pages belong to it, so
// that e.g. /customer-detail/123 keeps the "Customers" item highlighted.
type NavItem = { href: string; label: string; icon: typeof LayoutDashboard; match?: string[] }
type NavGroup = { title: string; adminOnly?: boolean; items: NavItem[] }

// Grouped sidebar navigation. New forms do NOT get their own top-level tab —
// they live inside the Forms hub (/forms); new data sections slot into the right
// group here. This keeps the chrome clean and scalable as the system grows.
const NAV_GROUPS: NavGroup[] = [
  {
    title: 'Overview',
    items: [{ href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard }],
  },
  {
    title: 'Banking',
    items: [
      { href: '/customers', label: 'Customers', icon: Users, match: ['/customer-detail'] },
      { href: '/facilities', label: 'Facilities', icon: Building, match: ['/facility-detail'] },
      { href: '/offer-letters', label: 'Offer Letters', icon: FileText },
      { href: '/properties', label: 'Mortgaged Properties', icon: Building2 },
    ],
  },
  {
    title: 'Tools',
    items: [
      { href: '/forms', label: 'Forms', icon: LayoutGrid, match: ['/voucher'] },
      { href: '/knowledge', label: 'Knowledge Base', icon: BookOpen },
      { href: '/reports', label: 'Reports', icon: BarChart3 },
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

function isNavActive(item: NavItem, pathname: string | null): boolean {
  if (!pathname) return false
  const prefixes = [item.href, ...(item.match ?? [])]
  return prefixes.some((p) => pathname === p || pathname.startsWith(p + '/'))
}

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout, authDisabled } = useAuth()
  const pathname = usePathname()
  const showAdmin = authDisabled || !!user?.is_admin
  const groups = NAV_GROUPS.filter((g) => showAdmin || !g.adminOnly)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 w-60 bg-white border-r border-gray-200 flex flex-col z-20">
        <div className="h-16 flex items-center gap-2.5 px-5 border-b border-gray-100">
          <div className="bg-blue-600 text-white rounded-lg p-1.5"><Landmark size={18} /></div>
          <div className="leading-tight">
            <div className="font-bold text-blue-700 text-[15px]">Banking Ops</div>
            <div className="text-[10px] text-gray-400">Bank Saderat — UAE</div>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-5">
          {groups.map((group) => (
            <div key={group.title}>
              <div className="px-3 mb-1.5 text-[10.5px] font-semibold uppercase tracking-wider text-gray-400">
                {group.title}
              </div>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const active = isNavActive(item, pathname)
                  const Icon = item.icon
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                        active ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <Icon size={18} className={active ? 'text-blue-600' : 'text-gray-400'} />
                      {item.label}
                    </Link>
                  )
                })}
              </div>
            </div>
          ))}
        </nav>
      </aside>

      {/* Main column */}
      <div className="pl-60">
        <header className="h-16 bg-white border-b border-gray-200 sticky top-0 z-10 flex items-center justify-end gap-4 px-6">
          <NotificationBell />
          <Link href="/profile" className="text-sm text-gray-600 hover:text-blue-600" title="My profile">
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
        </header>
        <main className="p-6 max-w-7xl mx-auto">{children}</main>
      </div>
    </div>
  )
}
