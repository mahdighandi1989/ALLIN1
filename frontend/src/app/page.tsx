'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function HomePage() {
  const router = useRouter()

  useEffect(() => {
    // Authentication is always enforced: send signed-in users to the dashboard
    // and everyone else to the login page. router.push never rejects, so there
    // is no error path to handle here.
    const token =
      typeof window !== 'undefined' ? localStorage.getItem('token') : null
    router.replace(token ? '/dashboard' : '/login')
  }, [router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4" />
        <p className="text-gray-600">Redirecting…</p>
      </div>
    </div>
  )
}
