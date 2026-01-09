/**
 * Authentication Hook
 * هوک احراز هویت
 */
import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useRouter } from 'next/router'
import api from '@/services/api'

interface User {
  id: string
  username: string
  email: string
  first_name?: string
  last_name?: string
  role: string
  is_active: boolean
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setIsLoading(false)
      return
    }

    try {
      const response = await api.get('/auth/me')
      setUser(response.data)
    } catch (error) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (username: string, password: string) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    localStorage.setItem('access_token', response.data.access_token)
    localStorage.setItem('refresh_token', response.data.refresh_token)

    // Get user info
    const userResponse = await api.get('/auth/me')
    setUser(userResponse.data)

    router.push('/')
  }

  const logout = async () => {
    try {
      await api.post('/auth/logout')
    } catch (error) {
      // Ignore error
    }

    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
    router.push('/login')
  }

  const refreshToken = async () => {
    const refresh = localStorage.getItem('refresh_token')
    if (!refresh) {
      throw new Error('No refresh token')
    }

    const response = await api.post('/auth/refresh', {
      refresh_token: refresh
    })

    localStorage.setItem('access_token', response.data.access_token)
    localStorage.setItem('refresh_token', response.data.refresh_token)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        refreshToken
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
