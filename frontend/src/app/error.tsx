'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  const router = useRouter()

  useEffect(() => {
    if (error?.message) {
      console.error('Application error:', error.message)
    }
  }, [error])

  const handleReset = () => {
    if (typeof reset === 'function') {
      reset()
    }
  }

  const handleGoHome = () => {
    router.push('/')
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
      <div className="bg-white rounded-lg shadow-lg p-6 max-w-lg w-full">
        <h2 className="text-xl font-bold text-red-600 mb-4">Something went wrong!</h2>
        <div className="bg-red-50 border border-red-200 rounded p-4 mb-4">
          <p className="text-sm text-red-800 font-mono break-all">
            {error?.message || 'Unknown error occurred'}
          </p>
          {error?.digest && (
            <p className="text-xs text-red-600 mt-2">Error ID: {error.digest}</p>
          )}
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleReset}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Try again
          </button>
          <button
            onClick={handleGoHome}
            className="flex-1 px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
          >
            Go home
          </button>
        </div>
      </div>
    </div>
  )
}