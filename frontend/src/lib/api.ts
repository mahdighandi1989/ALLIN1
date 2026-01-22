import axios from 'axios'
import { Customer, CustomerList, Facility, FacilityList, DashboardStats, User } from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
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

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
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
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    const res = await api.post('/api/auth/login', formData, {
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
