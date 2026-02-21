typescript
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? ''

export const api = axios.create({
  baseURL: API_URL,
  timeout: 60000, // افزایش تایم‌اوت از 30000 به 60000 میلی‌ثانیه
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
  // مقداردهی اولیه تعداد تلاش‌ها
  if (!config._retryCount) {
    config._retryCount = 0
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }

    // برای خطاهای 500 و درخواست‌های GET، حداکثر 2 بار تلاش مجدد
    if (error.response?.status === 500 && error.config && error.config.method?.toLowerCase() === 'get') {
      const maxRetries = 2
      if (error.config._retryCount < maxRetries) {
        error.config._retryCount += 1
        // تاخیر نمایی با ضریب 2
        const delay = Math.pow(2, error.config._retryCount) * 1000
        await new Promise(resolve => setTimeout(resolve, delay))
        return api(error.config)
      }
    }

    return Promise.reject(error)
  }
)

export default api