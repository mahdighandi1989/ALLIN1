'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { authApi } from './api'
import { User } from '@/types'

// AUTH DISABLED - Using fake user for development
const AUTH_DISABLED = true

const FAKE_USER: User = {
  id: 'dev-user',
  username: 'developer',
  email: 'dev@example.com',
  full_name: 'Developer Mode',
  is_active: true,
  is_admin: true,
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(AUTH_DISABLED ? FAKE_USER : null)
  const [loading, setLoading] = useState(!AUTH_DISABLED)
  const router = useRouter()

  useEffect(() => {
    if (!AUTH_DISABLED) {
      checkAuth()
    }
  }, [])

  const checkAuth = async () => {
    if (AUTH_DISABLED) {
      setUser(FAKE_USER)
      setLoading(false)
      return
    }

    const token = localStorage.getItem('token')
    if (!token) {
      setLoading(false)
      return
    }

    try {
      const userData = await authApi.me()
      setUser(userData)
    } catch (error: any) {
      // Token is invalid or expired - clean up
      console.warn('Authentication check failed:', error.response?.data?.detail || error.message)
      localStorage.removeItem('token')
      setUser(null)

      // Only redirect to login if we're on a protected route
      if (typeof window !== 'undefined') {
        const currentPath = window.location.pathname
        const publicPaths = ['/login', '/']
        if (!publicPaths.includes(currentPath)) {
          router.push('/login')
        }
      }
    } finally {
      setLoading(false)
    }
  }

  const login = async (username: string, password: string) => {
    if (AUTH_DISABLED) {
      setUser(FAKE_USER)
      router.push('/dashboard')
      return
    }

    try {
      const data = await authApi.login(username, password)
      localStorage.setItem('token', data.access_token)
      const userData = await authApi.me()
      setUser(userData)
      router.push('/dashboard')
    } catch (error: any) {
      // Ensure any invalid tokens are cleaned up on login failure
      localStorage.removeItem('token')
      setUser(null)
      throw error
    }
  }

  const logout = () => {
    if (AUTH_DISABLED) {
      router.push('/dashboard')
      return
    }
    localStorage.removeItem('token')
    setUser(null)
    router.push('/login')
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}