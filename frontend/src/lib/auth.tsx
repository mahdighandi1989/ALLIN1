'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { authApi } from './api'
import { User } from '@/types'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  // Authentication is always enforced — there is no demo/fake-user bypass.
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      setLoading(false)
      return
    }
    try {
      const userData = await authApi.me()
      setUser(userData)
    } catch (error) {
      console.error('Authentication check failed:', error)
      localStorage.removeItem('token')
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (username: string, password: string) => {
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
    // Revoke the token server-side (blacklist) so the session is invalidated on
    // the backend too, keeping frontend and backend session state in sync. This
    // is best-effort: even if the request fails we still clear local state.
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
