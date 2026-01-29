'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'

export default function HomePage() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [redirected, setRedirected] = useState(false)

  useEffect(() => {
    if (loading || redirected) return

    const performRedirect = () => {
      setRedirected(true)
      if (user) {
        router.push('/dashboard')
      } else {
        router.push('/login')
      }
    }

    // Use setTimeout to ensure state is stable
    const timeoutId = setTimeout(performRedirect, 0)
    
    return () => clearTimeout(timeoutId)
  }, [user, loading, router, redirected])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
  )
}