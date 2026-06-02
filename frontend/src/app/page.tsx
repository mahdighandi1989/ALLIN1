'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'

export default function HomePage() {
  const router = useRouter()
  const { loading, user, authDisabled } = useAuth()

  // This effect-based redirect is intentionally minimal and is NOT the
  // over-engineered anti-pattern (useState + try/catch + spinner just to route):
  // the auth decision depends on client-only state (the useAuth context and the
  // localStorage token), so it cannot run as a server-side redirect and must
  // wait for `loading` to settle on the client. We use router.replace (not
  // router.push) so the transient landing page leaves no entry in history and
  // the browser back button can't return the user to this redirect shim.
  // Edge cases covered: still-loading auth (no premature redirect), SSR/no-window
  // (token read guarded), and authDisabled/demo mode (treated as authenticated).
  useEffect(() => {
    if (loading) return
    const token =
      typeof window !== 'undefined' ? localStorage.getItem('token') : null
    if (authDisabled || user || token) {
      router.replace('/dashboard')
    } else {
      router.replace('/login')
    }
  }, [loading, user, authDisabled, router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4" />
        <p className="text-gray-600">Redirecting…</p>
      </div>
    </div>
  )
}
