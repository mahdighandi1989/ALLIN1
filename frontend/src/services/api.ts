/**
 * API Service v2.0
 * سرویس ارتباط با Backend - نسخه جدید
 */
import axios, { AxiosInstance } from 'axios'

const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_URL = baseUrl.endsWith('/api/v1') ? baseUrl : `${baseUrl}/api/v1`

const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle errors and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // If 401 and not already retried, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })

          localStorage.setItem('access_token', response.data.access_token)
          localStorage.setItem('refresh_token', response.data.refresh_token)

          originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`
          return api(originalRequest)
        } catch {
          // Refresh failed, redirect to login
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
        }
      } else {
        // No refresh token, redirect to login
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
    }

    return Promise.reject(error)
  }
)

export default api

// ========================================
// Auth API
// ========================================
export const authApi = {
  login: (username: string, password: string) => {
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)
    return api.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
  },
  register: (data: { username: string; email: string; password: string; first_name?: string; last_name?: string }) =>
    api.post('/auth/register', data),
  refresh: (refresh_token: string) => api.post('/auth/refresh', { refresh_token }),
  me: () => api.get('/auth/me'),
  logout: () => api.post('/auth/logout'),
}

// ========================================
// Customers API
// ========================================
export const customersApi = {
  list: (params?: { skip?: number; limit?: number; search?: string; status?: string }) =>
    api.get('/customers', { params }),
  get: (id: string) => api.get(`/customers/${id}`),
  create: (data: any) => api.post('/customers', data),
  update: (id: string, data: any) => api.put(`/customers/${id}`, data),
  delete: (id: string) => api.delete(`/customers/${id}`),
  stats: () => api.get('/customers/stats'),
}

// ========================================
// Facilities API
// ========================================
export const facilitiesApi = {
  list: (params?: { skip?: number; limit?: number; customer_id?: string; facility_type?: string; status?: string }) =>
    api.get('/facilities', { params }),
  get: (id: string) => api.get(`/facilities/${id}`),
  create: (data: any) => api.post('/facilities', data),
  update: (id: string, data: any) => api.put(`/facilities/${id}`, data),
  delete: (id: string) => api.delete(`/facilities/${id}`),
  stats: () => api.get('/facilities/stats'),
  expiring: (days?: number) => api.get('/facilities/expiring', { params: { days } }),
}

// ========================================
// AI API
// ========================================
export const aiApi = {
  status: () => api.get('/ai/status'),
  providers: () => api.get('/ai/providers'),
  generate: (data: { prompt: string; provider?: string; system_prompt?: string; max_tokens?: number; temperature?: number }) =>
    api.post('/ai/generate', data),
  analyze: (data: { content: string; analysis_type?: string; provider?: string }) =>
    api.post('/ai/analyze', data),
  extractDocument: (file: File, provider?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    if (provider) {
      formData.append('provider', provider)
    }
    return api.post('/ai/extract-document', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  addProvider: (providerId: string, apiKey: string, model?: string) =>
    api.post(`/ai/providers/${providerId}`, null, { params: { api_key: apiKey, model } }),
}

// ========================================
// Settings API
// ========================================
export const settingsApi = {
  getSystem: (category?: string) => api.get('/settings/system', { params: { category } }),
  updateSystem: (key: string, value: string) => api.put(`/settings/system/${key}`, { value }),
  getUser: () => api.get('/settings/user'),
  updateUser: (settings: any) => api.put('/settings/user', settings),
}

// ========================================
// Reports API
// ========================================
export const reportsApi = {
  dashboard: () => api.get('/reports/dashboard'),
  customers: (params?: { format?: string; status?: string }) =>
    api.get('/reports/customers', { params }),
  facilities: (params?: { format?: string; facility_type?: string }) =>
    api.get('/reports/facilities', { params }),
  expiring: (days?: number) => api.get('/reports/expiring', { params: { days } }),
  backup: () => api.post('/reports/backup'),
  backupStatus: () => api.get('/reports/backup/status'),
}
