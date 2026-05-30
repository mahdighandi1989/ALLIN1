'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { authApi } from './api'
import { setAuthDisabled } from './axios'
import { User } from '@/types'

interface AuthContextType {
  user: User | null
  loading: boolean
  authDisabled: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Shape of the local demo user used while login is disabled.
const DEMO_USER: User = {
  id: 'demo',
  username: 'demo',
  email: 'demo@example.com',
  full_name: 'Demo User',
  is_active: true,
  is_admin: true,
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [authDisabled, setDisabled] = useState(false)
  const router = useRouter()

  useEffect(() => {
    checkAuth()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const checkAuth = async () => {
    try {
      // Ask the backend whether login is currently required.
      const cfg = await authApi.config().catch(() => ({ auth_disabled: false }))
      setDisabled(cfg.auth_disabled)
      setAuthDisabled(cfg.auth_disabled)

      if (cfg.auth_disabled) {
        // Login removed for now — run as the demo user, no token needed.
        try {
          setUser(await authApi.me())
        } catch {
          setUser(DEMO_USER)
        }
        return
      }

      const token = localStorage.getItem('token')
      if (!token) {
        setUser(null)
        return
      }
      setUser(await authApi.me())
    } catch (error) {
      console.error('Authentication check failed:', error)
      localStorage.removeItem('token')
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (username: string, password: string) => {
    if (authDisabled) {
      // No login required — go straight in.
      setUser((u) => u ?? DEMO_USER)
      router.push('/dashboard')
      return
    }
    try {
      const data = await authApi.login(username, password)
      localStorage.setItem('token', data.access_token)
      const userData = await authApi.me()
      setUser(userData)
      router.push('/dashboard')
    } catch (error) {
      console.error('Login failed:', error || 'Unknown error')
      throw error
    }
  }

  const logout = async () => {
    if (authDisabled) {
      // Nothing to revoke when auth is bypassed.
      router.push('/dashboard')
      return
    }
    try {
      await authApi.logout()
    } catch (error) {
      console.error('Server logout failed (clearing local session anyway):', error)
    } finally {
      localStorage.removeItem('token')
      setUser(null)
      router.push('/login')
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, authDisabled, login, logout }}>
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
