/**
 * API Service
 * سرویس ارتباط با Backend
 */
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'

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
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle errors
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
        } catch (refreshError) {
          // Refresh failed, redirect to login
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }

    return Promise.reject(error)
  }
)

export default api

// API functions
export const customersApi = {
  list: (params?: any) => api.get('/customers', { params }),
  get: (id: string) => api.get(`/customers/${id}`),
  create: (data: any) => api.post('/customers', data),
  update: (id: string, data: any) => api.put(`/customers/${id}`, data),
  delete: (id: string) => api.delete(`/customers/${id}`),
  getProfile: (id: string) => api.get(`/customers/${id}/profile`),
  getSummary: (id: string) => api.get(`/customers/${id}/summary`),
}

export const facilitiesApi = {
  list: (params?: any) => api.get('/facilities', { params }),
  get: (id: string) => api.get(`/facilities/${id}`),
  create: (data: any) => api.post('/facilities', data),
  update: (id: string, data: any) => api.put(`/facilities/${id}`, data),
  delete: (id: string) => api.delete(`/facilities/${id}`),
  getGuarantors: (id: string) => api.get(`/facilities/${id}/guarantors`),
}

export const checklistsApi = {
  list: (params?: any) => api.get('/checklists', { params }),
  get: (id: string) => api.get(`/checklists/${id}`),
  create: (data: any) => api.post('/checklists', data),
  updateItem: (checklistId: string, itemId: string, data: any) =>
    api.put(`/checklists/${checklistId}/items/${itemId}`, data),
  getPendingTasks: (params?: any) => api.get('/checklists/tasks/pending', { params }),
}

export const aiApi = {
  status: () => api.get('/ai/status'),
  generate: (data: any) => api.post('/ai/generate', data),
  analyze: (data: any) => api.post('/ai/analyze', data),
  riskAssessment: (data: any) => api.post('/ai/risk-assessment', data),
  generateSummary: (data: any) => api.post('/ai/generate-summary', data),
}

export const personalApi = {
  getNotes: (params?: any) => api.get('/personal/notes', { params }),
  createNote: (data: any) => api.post('/personal/notes', data),
  updateNote: (id: string, data: any) => api.put(`/personal/notes/${id}`, data),
  deleteNote: (id: string) => api.delete(`/personal/notes/${id}`),
  toggleNoteDone: (id: string) => api.post(`/personal/notes/${id}/toggle-done`),
  getReminders: () => api.get('/personal/reminders'),
  getDashboard: () => api.get('/personal/dashboard'),
  quickNote: (content: string) => api.post('/personal/quick-note', null, { params: { content } }),
}

export const settingsApi = {
  getSystem: (category?: string) => api.get('/settings/system', { params: { category } }),
  updateSystem: (key: string, value: string) => api.put(`/settings/system/${key}`, { value }),
  getUser: () => api.get('/settings/user'),
  updateUser: (settings: any) => api.put('/settings/user', settings),
  getAIProviders: () => api.get('/settings/ai/providers'),
}

// AI Providers Management API
export const aiProvidersApi = {
  // Get all configured providers
  list: () => api.get('/ai-providers/providers'),

  // Get known/preset providers
  getKnown: () => api.get('/ai-providers/providers/known'),

  // Get single provider details
  get: (providerId: string) => api.get(`/ai-providers/providers/${providerId}`),

  // Create custom provider
  create: (data: {
    provider_id: string
    name: string
    api_key?: string
    base_url?: string
    default_model?: string
    enabled?: boolean
    provider_type?: string
  }) => api.post('/ai-providers/providers', data),

  // Update provider config
  update: (providerId: string, data: {
    name?: string
    api_key?: string
    base_url?: string
    default_model?: string
    enabled?: boolean
  }) => api.put(`/ai-providers/providers/${providerId}`, data),

  // Delete provider
  delete: (providerId: string) => api.delete(`/ai-providers/providers/${providerId}`),

  // Test provider connection
  test: (providerId: string, apiKey?: string) =>
    api.post(`/ai-providers/providers/${providerId}/test`, null, {
      params: apiKey ? { api_key: apiKey } : undefined
    }),

  // Get available models for provider
  getModels: (providerId: string, refresh?: boolean) =>
    api.get(`/ai-providers/providers/${providerId}/models`, {
      params: { refresh }
    }),

  // Fetch models from provider API
  fetchModels: (providerId: string, apiKey?: string) =>
    api.post(`/ai-providers/providers/${providerId}/fetch-models`, null, {
      params: apiKey ? { api_key: apiKey } : undefined
    }),

  // Get default provider
  getDefault: () => api.get('/ai-providers/default-provider'),

  // Set default provider
  setDefault: (providerId: string) => api.put(`/ai-providers/default-provider/${providerId}`),
}
