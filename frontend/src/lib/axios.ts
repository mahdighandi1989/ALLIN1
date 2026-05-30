import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

// Declaration merging so our retry bookkeeping fields are type-safe.
declare module 'axios' {
  export interface InternalAxiosRequestConfig {
    _retryCount?: number
    _originalUrl?: string
  }
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? ''

// When the backend has login disabled (AUTH_DISABLED), the 401 interceptor must
// not bounce the user to the (skipped) login page. AuthProvider sets this once it
// has read GET /api/auth/config, so the flag stays in sync with the backend.
let authDisabled = false
export function setAuthDisabled(value: boolean) {
  authDisabled = value
}

export const api = axios.create({
  baseURL: API_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }

  if (!config._retryCount) {
    config._retryCount = 0
  }

  if (!config._originalUrl) {
    config._originalUrl = config.url
  }

  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalConfig = error.config as InternalAxiosRequestConfig | undefined

    if (error.response?.status === 401 && typeof window !== 'undefined' && !authDisabled) {
      localStorage.removeItem('token')
      // Avoid redirect loops if we are already on the login page.
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }

    if (originalConfig && originalConfig.method?.toLowerCase() === 'get') {
      const maxRetries = 3
      const retryStatuses = [429, 500, 502, 503, 504]
      const isNetworkError = !error.response
      const isRetryableStatus =
        error.response && retryStatuses.includes(error.response.status)

      if (
        (isNetworkError || isRetryableStatus) &&
        (originalConfig._retryCount ?? 0) < maxRetries
      ) {
        originalConfig._retryCount = (originalConfig._retryCount ?? 0) + 1

        const delay = Math.pow(2, originalConfig._retryCount) * 1000
        await new Promise((resolve) => setTimeout(resolve, delay))

        return api(originalConfig)
      }
    }

    if (error.response?.status === 404) {
      console.error(
        'Resource not found:',
        originalConfig?._originalUrl || originalConfig?.url
      )
    }

    return Promise.reject(error)
  }
)

export default api
