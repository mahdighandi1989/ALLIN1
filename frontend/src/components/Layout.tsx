/**
 * Main Layout Component
 * کامپوننت چیدمان اصلی
 */
import { ReactNode, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import {
  Home,
  Users,
  FileText,
  CheckSquare,
  Settings,
  LogOut,
  Menu,
  X,
  Bell,
  User,
  Wallet,
  Building,
  Brain,
  StickyNote,
  ChevronDown
} from 'lucide-react'

import { useAuth } from '@/hooks/useAuth'

interface LayoutProps {
  children: ReactNode
}

const menuItems = [
  { href: '/', label: 'Dashboard', icon: Home },
  { href: '/customers', label: 'Customers', icon: Users },
  { href: '/facilities', label: 'Facilities', icon: Wallet },
  { href: '/checklists', label: 'Checklists', icon: CheckSquare },
  { href: '/properties', label: 'Properties', icon: Building },
  { href: '/ai', label: 'AI Tools', icon: Brain },
  { href: '/personal', label: 'My Notes', icon: StickyNote },
  { href: '/settings', label: 'Settings', icon: Settings },
]

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const { user, logout } = useAuth()
  const router = useRouter()

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? 'w-64' : 'w-20'
        } bg-slate-900 text-white min-h-screen transition-all duration-300 flex flex-col`}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800">
          {sidebarOpen && (
            <span className="font-bold text-lg">Banking Ops</span>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-slate-800 rounded-lg"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4">
          {menuItems.map((item) => {
            const Icon = item.icon
            const isActive = router.pathname === item.href

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-3 ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                } transition-colors`}
              >
                <Icon size={20} />
                {sidebarOpen && <span>{item.label}</span>}
              </Link>
            )
          })}
        </nav>

        {/* User section */}
        <div className="border-t border-slate-800 p-4">
          <button
            onClick={logout}
            className="flex items-center gap-3 w-full px-2 py-2 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          >
            <LogOut size={20} />
            {sidebarOpen && <span>Logout</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Header */}
        <header className="h-16 bg-white border-b flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <h2 className="font-semibold text-gray-700">
              {menuItems.find(item => item.href === router.pathname)?.label || 'Dashboard'}
            </h2>
          </div>

          <div className="flex items-center gap-4">
            {/* Notifications */}
            <button className="relative p-2 hover:bg-gray-100 rounded-lg">
              <Bell size={20} className="text-gray-600" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>

            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-2 p-2 hover:bg-gray-100 rounded-lg"
              >
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-semibold">
                  {user?.first_name?.[0] || user?.username?.[0] || 'U'}
                </div>
                {sidebarOpen && (
                  <>
                    <span className="text-sm font-medium text-gray-700">
                      {user?.first_name || user?.username}
                    </span>
                    <ChevronDown size={16} className="text-gray-500" />
                  </>
                )}
              </button>

              {userMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border py-1 z-50">
                  <div className="px-4 py-2 border-b">
                    <p className="font-medium">{user?.first_name} {user?.last_name}</p>
                    <p className="text-sm text-gray-500">{user?.email}</p>
                    <p className="text-xs text-gray-400 mt-1 capitalize">{user?.role}</p>
                  </div>
                  <Link
                    href="/profile"
                    className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-50"
                    onClick={() => setUserMenuOpen(false)}
                  >
                    <User size={16} />
                    Profile
                  </Link>
                  <Link
                    href="/settings"
                    className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-50"
                    onClick={() => setUserMenuOpen(false)}
                  >
                    <Settings size={16} />
                    Settings
                  </Link>
                  <button
                    onClick={logout}
                    className="flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-gray-50 w-full text-left"
                  >
                    <LogOut size={16} />
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
