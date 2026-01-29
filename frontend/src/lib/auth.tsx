'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { authApi } from './api'
import { User } from '@/types'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const token = localStorage.getItem('token')
    if (token) {
      try {
        const userData = await authApi.me()
        setUser(userData)
      } catch (error) {
        // Clear invalid token and user data
        localStorage.removeItem('token')
        setUser(null)
        console.warn('Invalid token detected, clearing authentication state')
      }
    }
    setLoading(false)
  }

  const login = async (username: string, password: string) => {
    try {
      const data = await authApi.login(username, password)
      localStorage.setItem('token', data.access_token)
      const userData = await authApi.me()
      setUser(userData)
      router.push('/dashboard')
    } catch (error) {
      // Ensure no partial state on login failure
      localStorage.removeItem('token')
      setUser(null)
      throw error
    }
  }

  const logout = () => {
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