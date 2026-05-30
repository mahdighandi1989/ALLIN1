'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Bell, CheckCheck } from 'lucide-react'
import { notificationsApi, parseApiError } from '@/lib/api'
import { AppNotification } from '@/types'
import toast from 'react-hot-toast'

const LEVEL_DOT: Record<string, string> = {
  info: 'bg-blue-500',
  success: 'bg-green-500',
  warning: 'bg-yellow-500',
  error: 'bg-red-500',
}

export default function NotificationBell() {
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [items, setItems] = useState<AppNotification[]>([])
  const [unread, setUnread] = useState(0)
  const ref = useRef<HTMLDivElement>(null)

  const refreshCount = async () => {
    try {
      setUnread(await notificationsApi.unreadCount())
    } catch {
      /* silent — the bell must never disrupt the app */
    }
  }

  const loadList = async () => {
    try {
      const data = await notificationsApi.list()
      setItems(data.items)
      setUnread(data.unread)
    } catch (e) {
      toast.error(parseApiError(e))
    }
  }

  useEffect(() => {
    refreshCount()
    const t = setInterval(refreshCount, 60000) // poll every minute
    return () => clearInterval(t)
  }, [])

  // Close on outside click.
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  const toggle = () => {
    const next = !open
    setOpen(next)
    if (next) loadList()
  }

  const onItemClick = async (n: AppNotification) => {
    try {
      if (!n.is_read) {
        await notificationsApi.markRead(n.id)
        setUnread((u) => Math.max(0, u - 1))
        setItems((arr) => arr.map((x) => (x.id === n.id ? { ...x, is_read: true } : x)))
      }
    } catch {
      /* ignore */
    }
    if (n.link) {
      setOpen(false)
      router.push(n.link)
    }
  }

  const markAll = async () => {
    try {
      await notificationsApi.markAllRead()
      setUnread(0)
      setItems((arr) => arr.map((x) => ({ ...x, is_read: true })))
      toast.success('All marked as read')
    } catch (e) {
      toast.error(parseApiError(e))
    }
  }

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={toggle}
        data-testid="notification-bell"
        className="relative text-gray-500 hover:text-gray-700"
        title="Notifications"
      >
        <Bell size={20} />
        {unread > 0 && (
          <span className="absolute -top-1.5 -right-1.5 min-w-[16px] h-4 px-1 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center">
            {unread > 99 ? '99+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-xl border z-50 max-h-96 overflow-hidden flex flex-col">
          <div className="flex items-center justify-between px-4 py-2 border-b">
            <span className="font-medium text-sm">Notifications</span>
            <button onClick={markAll} className="flex items-center gap-1 text-xs text-blue-600 hover:underline">
              <CheckCheck size={14} /> Mark all read
            </button>
          </div>
          <div className="overflow-y-auto">
            {items.length === 0 ? (
              <p className="px-4 py-8 text-center text-sm text-gray-400">No notifications</p>
            ) : (
              items.map((n) => (
                <button
                  key={n.id}
                  onClick={() => onItemClick(n)}
                  className={`w-full text-left px-4 py-3 border-b hover:bg-gray-50 flex gap-3 ${
                    n.is_read ? 'opacity-60' : ''
                  }`}
                >
                  <span className={`mt-1.5 w-2 h-2 rounded-full shrink-0 ${LEVEL_DOT[n.level] || 'bg-gray-400'}`} />
                  <span className="flex-1 min-w-0">
                    <span className="block text-sm font-medium truncate">{n.title}</span>
                    {n.message && <span className="block text-xs text-gray-500 truncate">{n.message}</span>}
                    <span className="block text-[11px] text-gray-400">
                      {n.created_at ? new Date(n.created_at).toLocaleString() : ''}
                    </span>
                  </span>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
