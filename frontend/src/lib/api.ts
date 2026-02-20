typescript
import { api } from './axios'
import { AUTH_DISABLED } from '../config'
import { Customer, CustomerList, Facility, FacilityList, User } from '@/types'

// Parse API error into user-friendly message
export function parseApiError(error: any): string {
  if (error.response?.status === 422 && Array.isArray(error.response?.data?.detail)) {
    const details = error.response.data.detail
    if (details.length > 0) {
      const firstError = details[0]
      const field = firstError.loc?.filter((l: any) => l !== 'body').join('.')
      return field ? `${field}: ${firstError.msg}` : firstError.msg
    }
  }
  if (typeof error.response?.data?.detail === 'string') {
    return error.response.data.detail
  }
  return error.message || 'An error occurred'
}

// Auth API
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

// Stats API
export const statsApi = {
  dashboard: async () => {
    try {
      const res = await api.get('/api/stats/dashboard')
      return res.data
    } catch (error) {
      // فقط در حالت توسعه خطا را لاگ می‌کنیم
      if (process.env.NODE_ENV === 'development') {
        if (error instanceof Error) {
          console.error('Dashboard stats error:', error.message)
        } else {
          console.error('Dashboard stats error:', error)
        }
      }
      return {
        total_customers: 0,
        active_customers: 0,
        total_facilities: 0,
        expiring_soon_facilities: 0,
        total_exposure: { amount: 0, currency: 'AED' },
        recent_customers: [],
      }
    }
  },
}

// Customers API
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

// Facilities API
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

export default api