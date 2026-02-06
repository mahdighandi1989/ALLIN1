import axios from 'axios'
import { Customer, CustomerList, Facility, FacilityList, DashboardStats, User } from '@/types'

// Use empty string (same origin) when deployed together, or localhost for local dev
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? ''

// Validation error structure from FastAPI/Pydantic
interface ValidationError {
  type: string
  loc: (string | number)[]
  msg: string
  input?: unknown
  url?: string
}

// Parse FastAPI validation error response into a user-friendly message
export function parseApiError(error: any): string {
  // Check if this is a 422 validation error with detail array
  if (error.response?.status === 422 && Array.isArray(error.response?.data?.detail)) {
    const details = error.response.data.detail as ValidationError[]
    if (details.length > 0) {
      // Extract field name and message from first error
      const firstError = details[0]
      const field = firstError.loc.filter(l => l !== 'body').join('.')
      const message = firstError.msg
      return field ? `${field}: ${message}` : message
    }
  }

  // Check if detail is a string (other API errors)
  if (typeof error.response?.data?.detail === 'string') {
    return error.response.data.detail
  }

  // Fall back to error message or generic error
  return error.message || 'An error occurred'
}

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000, // 30 second timeout to prevent indefinite hanging
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

// Handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle network errors and timeouts
    if (!error.response) {
      if (error.code === 'ECONNABORTED') {
        error.message = 'Request timed out. Please check your connection and try again.'
      } else if (error.message === 'Network Error') {
        error.message = 'Unable to connect to server. Please check your connection.'
      }
    }
    // Handle 401 unauthorized
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth
export const authApi = {
  login: async (username: string, password: string) => {
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)
    const res = await api.post('/api/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return res.data
  },
  me: async (): Promise<User> => {
    const res = await api.get('/api/auth/me')
    return res.data
  },
}

// Customers
export const customersApi = {
  list: async (params?: { page?: number; page_size?: number; search?: string }): Promise<CustomerList> => {
    const res = await api.get('/api/customers', { params })
    return res.data
  },
  get: async (id: string): Promise<Customer> => {
    const res = await api.get(`/api/customers/${id}`)
    return res.data
  },
  create: async (data: Partial<Customer>): Promise<Customer> => {
    const res = await api.post('/api/customers', data)
    return res.data
  },
  update: async (id: string, data: Partial<Customer>): Promise<Customer> => {
    const res = await api.put(`/api/customers/${id}`, data)
    return res.data
  },
  delete: async (id: string): Promise<void> => {
    await api.delete(`/api/customers/${id}`)
  },
}

// Facilities
export const facilitiesApi = {
  list: async (params?: { page?: number; page_size?: number; customer_id?: string }): Promise<FacilityList> => {
    const res = await api.get('/api/facilities', { params })
    return res.data
  },
  get: async (id: string): Promise<Facility> => {
    const res = await api.get(`/api/facilities/${id}`)
    return res.data
  },
  create: async (data: Partial<Facility>): Promise<Facility> => {
    const res = await api.post('/api/facilities', data)
    return res.data
  },
  update: async (id: string, data: Partial<Facility>): Promise<Facility> => {
    const res = await api.put(`/api/facilities/${id}`, data)
    return res.data
  },
  delete: async (id: string): Promise<void> => {
    await api.delete(`/api/facilities/${id}`)
  },
}

// Stats
export const statsApi = {
  dashboard: async (): Promise<DashboardStats> => {
    const res = await api.get('/api/stats/dashboard')
    return res.data
  },
  expiring: async (days?: number) => {
    const res = await api.get('/api/stats/expiring', { params: { days } })
    return res.data
  },
}

export default api