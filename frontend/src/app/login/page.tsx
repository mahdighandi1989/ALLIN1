'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import { parseApiError } from '@/lib/api'
import toast from 'react-hot-toast'
import Link from 'next/link'
import { Eye, EyeOff, Lock, User } from 'lucide-react'

// Marketing/utility links surfaced in the login-page nav bar so the sign-in
// screen is no longer a dead-end card — the brand + key destinations stay
// discoverable, matching the header used across the rest of the app.
const NAV_LINKS = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/customers', label: 'Customers' },
  { href: '/facilities', label: 'Facilities' },
]

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [loginAttempts, setLoginAttempts] = useState(0)
  const { login, authDisabled } = useAuth()
  const router = useRouter()

  // Login is currently disabled — there is nothing to sign in to, go to the app.
  useEffect(() => {
    if (authDisabled) router.replace('/dashboard')
  }, [authDisabled, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (loginAttempts >= 5) {
      toast.error('Too many login attempts. Please try again later.')
      return
    }

    if (!username.trim() || !password.trim()) {
      toast.error('Please enter both username and password')
      return
    }

    setLoading(true)
    try {
      await login(username.trim(), password)
      toast.success('Login successful')
      setLoginAttempts(0)
    } catch (error: any) {
      setLoginAttempts(prev => prev + 1)
      
      // Handle both API errors and network errors
      if (error.response?.status === 401) {
        toast.error('Invalid username or password')
      } else if (error.response?.status === 429) {
        toast.error('Too many requests. Please try again later.')
      } else if (error.code === 'ECONNABORTED') {
        toast.error('Request timeout. Please check your connection.')
      } else if (error.message === 'Network Error') {
        toast.error('Unable to connect to server. Please try again.')
      } else {
        toast.error(parseApiError(error))
      }
    } finally {
      setLoading(false)
    }
  }

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword)
  }

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-blue-50 to-indigo-100">
      <header className="bg-white border-b shadow-sm">
        <div className="container mx-auto px-4 flex items-center justify-between h-16">
          <div className="flex items-center gap-8">
            <span className="text-lg font-bold text-blue-600">Banking Ops</span>
            <nav className="hidden sm:flex items-center gap-1">
              {NAV_LINKS.map(({ href, label }) => (
                <Link
                  key={href}
                  href={href}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 transition-colors"
                >
                  {label}
                </Link>
              ))}
            </nav>
          </div>
          <span className="text-sm text-gray-500">Sign in</span>
        </div>
      </header>

      <div className="flex-1 flex items-center justify-center p-4">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md border border-gray-200">
        <div className="text-center mb-8">
          <div className="mx-auto w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mb-4">
            <Lock className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Banking Operations</h1>
          <p className="text-gray-600 text-sm">Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
              Username
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User className="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="username"
                data-testid="username-input"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                placeholder="Enter your username"
                required
                autoComplete="username"
                disabled={loading}
                maxLength={50}
              />
            </div>
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                data-testid="password-input"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-3 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                placeholder="Enter your password"
                required
                autoComplete="current-password"
                disabled={loading}
                maxLength={100}
              />
              <button
                type="button"
                onClick={togglePasswordVisibility}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                disabled={loading}
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5" />
                ) : (
                  <Eye className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>

          {loginAttempts > 0 && (
            <div className="text-sm text-amber-600 bg-amber-50 p-3 rounded-lg border border-amber-200">
              Login attempt {loginAttempts} of 5. {5 - loginAttempts} attempts remaining.
            </div>
          )}

          <button
            type="submit"
            data-testid="login-submit"
            disabled={loading || loginAttempts >= 5}
            className="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Signing in...
              </div>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        {/* Visible divider so the alternate sign-in option is discoverable. */}
        <div className="flex items-center gap-3 my-6">
          <div className="flex-1 h-px bg-gray-200" />
          <span className="text-xs font-medium text-gray-400">OR</span>
          <div className="flex-1 h-px bg-gray-200" />
        </div>

        <a
          href="/api/auth/google/login"
          data-testid="btn-google-login"
          className="w-full flex items-center justify-center gap-3 py-3 px-4 border border-gray-300 rounded-lg bg-white hover:bg-gray-50 transition-colors text-sm font-medium text-gray-700"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24" aria-hidden="true">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.27-4.74 3.27-8.1z" />
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23z" />
            <path fill="#FBBC05" d="M5.84 14.1a6.6 6.6 0 0 1 0-4.2V7.06H2.18a11 11 0 0 0 0 9.88l3.66-2.84z" />
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84C6.71 7.31 9.14 5.38 12 5.38z" />
          </svg>
          Sign in with Google
        </a>

        <div className="mt-6 text-center">
          <p className="text-xs text-gray-500">
            Secure banking operations system
          </p>
        </div>
      </div>
      </div>
    </div>
  )
}