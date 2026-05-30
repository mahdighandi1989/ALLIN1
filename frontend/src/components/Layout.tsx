'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import { LayoutDashboard, Users, Building, FileText, BarChart3, ShieldCheck, LogOut } from 'lucide-react'

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/customers', label: 'Customers', icon: Users },
  { href: '/facilities', label: 'Facilities', icon: Building },
  { href: '/offer-letters', label: 'Offer Letters', icon: FileText },
  { href: '/reports', label: 'Reports', icon: BarChart3 },
]

// Shown only to admins (or in the no-login demo mode).
const ADMIN_NAV_ITEMS = [
  { href: '/users', label: 'Users', icon: ShieldCheck },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout, authDisabled } = useAuth()
  const pathname = usePathname()
  const showAdmin = authDisabled || !!user?.is_admin
  const navItems = showAdmin ? [...NAV_ITEMS, ...ADMIN_NAV_ITEMS] : NAV_ITEMS

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b shadow-sm">
        <div className="container mx-auto px-4 flex items-center justify-between h-16">
          <div className="flex items-center gap-8">
            <span className="text-lg font-bold text-blue-600">Banking Ops</span>
            <nav className="flex items-center gap-1">
              {navItems.map(({ href, label, icon: Icon }) => {
                const active = pathname?.startsWith(href)
                return (
                  <Link
                    key={href}
                    href={href}
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
            </nav>
          </div>

          <div className="flex items-center gap-4">
            {user && (
              <span className="text-sm text-gray-600">{user.full_name || user.username}</span>
            )}
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
