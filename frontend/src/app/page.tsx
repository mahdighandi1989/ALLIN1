'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'

export default function HomePage() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [hasRedirected, setHasRedirected] = useState(false)

  useEffect(() => {
    // Prevent multiple redirects and race conditions
    if (loading || hasRedirected) return

    const handleRedirect = async () => {
      try {
        if (user) {
          setHasRedirected(true)
          await router.push('/dashboard')
        } else {
          setHasRedirected(true)
          await router.push('/login')
        }
      } catch (error) {
        // Reset redirect flag if navigation fails
        setHasRedirected(false)
      }
    }

    handleRedirect()
  }, [user, loading, router, hasRedirected])

  // Reset redirect flag when auth state changes
  useEffect(() => {
    if (loading) {
      setHasRedirected(false)
    }
  }, [loading])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">
          {loading ? 'Loading...' : hasRedirected ? 'Redirecting...' : 'Initializing...'}
        </p>
      </div>
    </div>
  )
}