import api from './axios'
import type {
  User,
  Customer,
  CustomerList,
  CustomerForm,
  CustomerFilters,
  Facility,
  FacilityList,
  FacilityForm,
  FacilityFilters,
  DashboardStats,
} from '@/types'

export { api }

/** Shape returned by POST /api/auth/login and /register. */
export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

/**
 * Normalise any list payload into the paginated envelope the UI expects.
 * The backend list endpoints currently return a bare array; this adapter keeps
 * the frontend working whether the API returns an array or an
 * ``{ items, total, page, page_size }`` envelope.
 */
function toPaginated<T>(
  payload: any,
  page: number,
  pageSize: number
): { items: T[]; total: number; page: number; page_size: number } {
  if (Array.isArray(payload)) {
    return { items: payload, total: payload.length, page, page_size: pageSize }
  }
  const items: T[] = payload?.items ?? []
  return {
    items,
    total: payload?.total ?? items.length,
    page: payload?.page ?? page,
    page_size: payload?.page_size ?? pageSize,
  }
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------
export const authApi = {
  /** OAuth2 password-flow login (form-encoded), returns token + user. */
  async login(username: string, password: string): Promise<LoginResponse> {
    const body = new URLSearchParams()
    body.append('username', username)
    body.append('password', password)
    const { data } = await api.post<LoginResponse>('/api/auth/login', body, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return data
  },

  async me(): Promise<User> {
    const { data } = await api.get<User>('/api/auth/me')
    return data
  },

  /** Revoke the current token server-side (blacklist) and end the session. */
  async logout(): Promise<void> {
    await api.post('/api/auth/logout')
  },

  async refresh(): Promise<LoginResponse> {
    const { data } = await api.post<LoginResponse>('/api/auth/refresh')
    return data
  },
}

// ---------------------------------------------------------------------------
// Customers
// ---------------------------------------------------------------------------
export const customersApi = {
  async list(filters: CustomerFilters = {}): Promise<CustomerList> {
    const page = filters.page ?? 1
    const pageSize = filters.page_size ?? 20
    const params: Record<string, any> = {
      skip: (page - 1) * pageSize,
      limit: pageSize,
    }
    if (filters.search) params.search = filters.search
    if (filters.account_type) params.account_type = filters.account_type
    if (filters.status) params.status = filters.status
    if (filters.branch) params.branch = filters.branch

    const { data } = await api.get('/api/customers/', { params })
    return toPaginated<Customer>(data, page, pageSize)
  },

  async get(id: string | number): Promise<Customer> {
    const { data } = await api.get<Customer>(`/api/customers/${id}`)
    return data
  },

  async create(payload: CustomerForm): Promise<Customer> {
    const { data } = await api.post<Customer>('/api/customers/', payload)
    return data
  },

  async update(id: string | number, payload: Partial<CustomerForm>): Promise<Customer> {
    const { data } = await api.put<Customer>(`/api/customers/${id}`, payload)
    return data
  },

  async delete(id: string | number): Promise<void> {
    await api.delete(`/api/customers/${id}`)
  },
}

// ---------------------------------------------------------------------------
// Facilities
// ---------------------------------------------------------------------------
export const facilitiesApi = {
  async list(filters: FacilityFilters = {}): Promise<FacilityList> {
    const page = filters.page ?? 1
    const pageSize = filters.page_size ?? 20
    const params: Record<string, any> = { page, page_size: pageSize }
    if (filters.customer_id) params.customer_id = filters.customer_id
    if (filters.facility_type) params.facility_type = filters.facility_type
    if (filters.status) params.status = filters.status
    if (filters.search) params.search = filters.search

    const { data } = await api.get('/api/facilities/', { params })
    return toPaginated<Facility>(data, page, pageSize)
  },

  async get(id: string | number): Promise<Facility> {
    const { data } = await api.get<Facility>(`/api/facilities/${id}`)
    return data
  },

  async create(payload: FacilityForm): Promise<Facility> {
    const { data } = await api.post<Facility>('/api/facilities/', payload)
    return data
  },

  async update(id: string | number, payload: Partial<FacilityForm>): Promise<Facility> {
    const { data } = await api.put<Facility>(`/api/facilities/${id}`, payload)
    return data
  },

  async delete(id: string | number): Promise<void> {
    await api.delete(`/api/facilities/${id}`)
  },
}

// ---------------------------------------------------------------------------
// Dashboard stats
// ---------------------------------------------------------------------------
export const statsApi = {
  async dashboard(): Promise<DashboardStats> {
    const { data } = await api.get<DashboardStats>('/api/stats/dashboard')
    return data
  },
}

// ---------------------------------------------------------------------------
// Error helper
// ---------------------------------------------------------------------------
/**
 * Turn any axios/API error into a human-readable message. Handles FastAPI's
 * ``{ detail: string }`` and validation ``{ detail: [{ msg, loc }] }`` shapes
 * without ever surfacing raw internals to the user.
 */
export function parseApiError(error: any): string {
  // Robust 'reason' validation: the old facilities code did
  // `if (reason instanceof Response)` and assumed a Response/`message` shape,
  // which broke for axios errors, plain objects and strings. This helper instead
  // defensively reads the well-known fields and always returns a safe string, so
  // any rejection reason (Response, AxiosError, object, string, undefined) is
  // handled without leaking internals.
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const first = detail[0]
    if (first?.msg) {
      const field = Array.isArray(first.loc) ? first.loc[first.loc.length - 1] : ''
      return field ? `${field}: ${first.msg}` : first.msg
    }
  }
  if (error?.code === 'ECONNABORTED') return 'Request timeout. Please try again.'
  if (error?.message === 'Network Error') return 'Unable to connect to the server.'
  return error?.message || 'An unexpected error occurred.'
}

export default api
