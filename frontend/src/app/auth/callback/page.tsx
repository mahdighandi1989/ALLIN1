'use client'

import { useEffect, useState } from 'react'

// Google Sign-In lands here. The backend callback
// (GET /api/auth/google/callback) exchanges the OAuth code, creates/updates the
// local user, mints our app JWT, then redirects the browser to
//   /auth/callback?token=<jwt>&role=<role>
// This page captures the token, stores it for the axios client, and hands off to
// the app with a full-page navigation (not the SPA router) so the AuthProvider
// re-runs its session check against the freshly stored token. The Layout gate
// then routes a still-'pending' user to the awaiting-approval screen.
export default function AuthCallbackPage() {
  const [message, setMessage] = useState('Signing you in…')

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)

    const error = params.get('error')
    if (error) {
      setMessage('Sign-in failed. Redirecting…')
      window.location.replace(`/login?error=${encodeURIComponent(error)}`)
      return
    }

    const token = params.get('token')
    if (!token) {
      window.location.replace('/login?error=missing_token')
      return
    }

    try {
      localStorage.setItem('token', token)
    } catch {
      // Storage unavailable (e.g. private mode) — fall back to the login screen.
      window.location.replace('/login?error=storage_unavailable')
      return
    }

    // Hand off to the app; AuthProvider re-checks the session on load.
    window.location.replace('/dashboard')
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="flex flex-col items-center gap-4">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
        <p className="text-gray-600 text-sm">{message}</p>
      </div>
    </div>
  )
}
