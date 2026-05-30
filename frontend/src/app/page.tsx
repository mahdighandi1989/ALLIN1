'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'

export default function HomePage() {
  const router = useRouter()
  const { loading, user, authDisabled } = useAuth()

  useEffect(() => {
    if (loading) return
    // When login is disabled, or the user is already authenticated, go to the
    // dashboard; otherwise show the login screen.
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
