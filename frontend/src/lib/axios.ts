typescript
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? ''

export const api = axios.create({
  baseURL: API_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
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
  async (error) => {
    const originalConfig = error.config
    
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('token')
      window.location.href = '/login'
      return Promise.reject(error)
    }
    
    if (originalConfig && originalConfig.method?.toLowerCase() === 'get') {
      const maxRetries = 3
      const retryStatuses = [429, 500, 502, 503, 504]
      const isNetworkError = !error.response
      const isRetryableStatus = error.response && retryStatuses.includes(error.response.status)
      
      if ((isNetworkError || isRetryableStatus) && originalConfig._retryCount < maxRetries) {
        originalConfig._retryCount += 1
        
        const delay = Math.pow(2, originalConfig._retryCount) * 1000
        await new Promise(resolve => setTimeout(resolve, delay))
        
        return api(originalConfig)
      }
    }
    
    if (error.response?.status === 404) {
      console.error('Resource not found:', originalConfig._originalUrl || originalConfig.url)
    }
    
    return Promise.reject(error)
  }
)

export default api