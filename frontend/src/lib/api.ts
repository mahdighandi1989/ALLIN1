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
  FacilityDetail,
  DashboardStats,
  OfferLetter,
  OfferLetterDetail,
  OfferLetterList,
  OfferLetterForm,
  CustomerDetail,
  PortfolioReport,
  TopExposures,
  AdminUser,
  AdminUserList,
  AdminUserForm,
  TrashList,
  AuditList,
  NotificationList,
  ImportResult,
  SettingsResponse,
  EditableSetting,
  FxRates,
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
  /** Public: whether the backend currently has login/auth disabled. */
  async config(): Promise<{ auth_disabled: boolean }> {
    const { data } = await api.get<{ auth_disabled: boolean }>('/api/auth/config')
    return data
  },

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

  async updateProfile(payload: { full_name?: string; email?: string }): Promise<User> {
    const { data } = await api.put<User>('/api/auth/me', payload)
    return data
  },

  async changePassword(current_password: string, new_password: string): Promise<void> {
    await api.post('/api/auth/change-password', { current_password, new_password })
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
    // The backend list endpoint paginates by page/page_size (not skip/limit).
    const params: Record<string, any> = { page, page_size: pageSize }
    if (filters.search) params.search = filters.search
    if (filters.account_type) params.account_type = filters.account_type
    if (filters.status) params.status = filters.status
    if (filters.branch) params.branch = filters.branch
    if (filters.sort_by) params.sort_by = filters.sort_by
    if (filters.sort_order) params.sort_order = filters.sort_order

    const { data } = await api.get('/api/customers/', { params })
    return toPaginated<Customer>(data, page, pageSize)
  },

  async detail(id: string | number): Promise<CustomerDetail> {
    const { data } = await api.get<CustomerDetail>(`/api/customers/${id}/detail`)
    return data
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

  async bulkDelete(ids: string[]): Promise<{ deleted: number }> {
    const { data } = await api.post<{ deleted: number }>('/api/customers/bulk/delete', { ids })
    return data
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
    if (filters.amount_min != null) params.amount_min = filters.amount_min
    if (filters.amount_max != null) params.amount_max = filters.amount_max
    if (filters.sort_by) params.sort_by = filters.sort_by
    if (filters.sort_order) params.sort_order = filters.sort_order

    const { data } = await api.get('/api/facilities/', { params })
    return toPaginated<Facility>(data, page, pageSize)
  },

  async get(id: string | number): Promise<Facility> {
    const { data } = await api.get<Facility>(`/api/facilities/${id}`)
    return data
  },

  async detail(id: string | number): Promise<FacilityDetail> {
    const { data } = await api.get<FacilityDetail>(`/api/facilities/${id}/detail`)
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

  async bulkDelete(ids: string[]): Promise<{ deleted: number }> {
    const { data } = await api.post<{ deleted: number }>('/api/facilities/bulk/delete', { ids })
    return data
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
  async captureSnapshot(): Promise<void> {
    await api.post('/api/stats/snapshot')
  },
  async expiringDocuments(days = 90): Promise<any> {
    const { data } = await api.get(`/api/stats/expiring-documents?days=${days}`)
    return data
  },
}

// ---------------------------------------------------------------------------
// CRM interactive actions (credit-file workflow)
// ---------------------------------------------------------------------------
export const crmApi = {
  async toggleChecklistStep(accountNo: string, step: number, done: boolean): Promise<any> {
    const { data } = await api.patch(`/api/crm/checklist/${encodeURIComponent(accountNo)}`, { step, done })
    return data
  },
  async createTask(accountNo: string, body: { task_name: string; followup_date?: string; priority?: string; notes?: string }): Promise<any> {
    const { data } = await api.post(`/api/crm/tasks/${encodeURIComponent(accountNo)}`, body)
    return data
  },
  async updateTask(taskId: string, body: { status?: string; is_active?: string }): Promise<any> {
    const { data } = await api.patch(`/api/crm/tasks/${encodeURIComponent(taskId)}`, body)
    return data
  },
  async addGuarantor(accountNo: string, body: { guarantor_name: string; guarantor_account?: string; cheque_no?: string; cheque_amount?: number; issuing_bank?: string; pim_ref?: string }): Promise<any> {
    const { data } = await api.post(`/api/crm/guarantors/${encodeURIComponent(accountNo)}`, body)
    return data
  },
  async addFacility(accountNo: string, body: { facility_type: string; amount: number; currency?: string; name?: string }): Promise<any> {
    const { data } = await api.post(`/api/crm/facilities/${encodeURIComponent(accountNo)}`, body)
    return data
  },
  async updateProfile(accountNo: string, body: Record<string, string>): Promise<any> {
    const { data } = await api.patch(`/api/crm/profile/${encodeURIComponent(accountNo)}`, body)
    return data
  },
  async runMerge(): Promise<any> {
    const { data } = await api.post('/api/crm/run-merge')
    return data
  },
  async mergeStatus(): Promise<any> {
    const { data } = await api.get('/api/crm/merge-status')
    return data
  },
  async addNote(accountNo: string, body: { title?: string; content: string; category?: string; reminder_date?: string }): Promise<any> {
    const { data } = await api.post(`/api/crm/notes/${encodeURIComponent(accountNo)}`, body)
    return data
  },
}

// ---------------------------------------------------------------------------
// Offer letters
// ---------------------------------------------------------------------------
export const offerLettersApi = {
  async list(
    filters: { page?: number; page_size?: number; customer_id?: string; status?: string } = {}
  ): Promise<OfferLetterList> {
    const page = filters.page ?? 1
    const pageSize = filters.page_size ?? 20
    const params: Record<string, any> = { page, page_size: pageSize }
    if (filters.customer_id) params.customer_id = filters.customer_id
    if (filters.status) params.status = filters.status
    const { data } = await api.get('/api/offer-letters/', { params })
    if (Array.isArray(data)) {
      return { items: data, total: data.length, page, page_size: pageSize }
    }
    return data
  },

  async get(id: string): Promise<OfferLetterDetail> {
    const { data } = await api.get<OfferLetterDetail>(`/api/offer-letters/${id}`)
    return data
  },

  async create(payload: OfferLetterForm): Promise<OfferLetter> {
    const { data } = await api.post<OfferLetter>('/api/offer-letters/', payload)
    return data
  },

  async update(id: string, payload: Partial<OfferLetterForm>): Promise<OfferLetter> {
    const { data } = await api.put<OfferLetter>(`/api/offer-letters/${id}`, payload)
    return data
  },

  async generateSchedule(id: string): Promise<OfferLetterDetail> {
    const { data } = await api.post<OfferLetterDetail>(
      `/api/offer-letters/${id}/generate-schedule`
    )
    return data
  },

  async setStatus(id: string, status: string): Promise<OfferLetter> {
    const { data } = await api.post<OfferLetter>(
      `/api/offer-letters/${id}/status`,
      null,
      { params: { new_status: status } }
    )
    return data
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/api/offer-letters/${id}`)
  },
}

// ---------------------------------------------------------------------------
// Admin user management
// ---------------------------------------------------------------------------
export const usersApi = {
  async list(filters: { page?: number; page_size?: number; search?: string } = {}): Promise<AdminUserList> {
    const page = filters.page ?? 1
    const pageSize = filters.page_size ?? 20
    const params: Record<string, any> = { page, page_size: pageSize }
    if (filters.search) params.search = filters.search
    const { data } = await api.get('/api/users/', { params })
    if (Array.isArray(data)) return { items: data, total: data.length, page, page_size: pageSize }
    return data
  },
  async create(payload: AdminUserForm): Promise<AdminUser> {
    const { data } = await api.post<AdminUser>('/api/users/', payload)
    return data
  },
  async update(id: string, payload: Partial<AdminUserForm>): Promise<AdminUser> {
    const { data } = await api.put<AdminUser>(`/api/users/${id}`, payload)
    return data
  },
  async deactivate(id: string): Promise<void> {
    await api.delete(`/api/users/${id}`)
  },
}

// ---------------------------------------------------------------------------
// System settings
// ---------------------------------------------------------------------------
export const fxApi = {
  async list(): Promise<FxRates> {
    const { data } = await api.get<FxRates>('/api/fx/')
    return data
  },
  async update(rates: Record<string, number>): Promise<FxRates> {
    const { data } = await api.put<FxRates>('/api/fx/', { rates })
    return data
  },
}

export const settingsApi = {
  async get(): Promise<SettingsResponse> {
    const { data } = await api.get<SettingsResponse>('/api/settings/')
    return data
  },
  async update(values: Record<string, string>): Promise<{ editable: EditableSetting[] }> {
    const { data } = await api.put<{ editable: EditableSetting[] }>('/api/settings/', { values })
    return data
  },
}

// ---------------------------------------------------------------------------
// Excel import
// ---------------------------------------------------------------------------
export const importsApi = {
  async customers(file: File, dryRun = false): Promise<ImportResult> {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post<ImportResult>('/api/imports/customers', form, {
      params: { dry_run: dryRun },
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },
  async facilities(file: File, dryRun = false): Promise<ImportResult> {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post<ImportResult>('/api/imports/facilities', form, {
      params: { dry_run: dryRun },
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },
}

// ---------------------------------------------------------------------------
// In-app notifications
// ---------------------------------------------------------------------------
export const notificationsApi = {
  async list(unreadOnly = false): Promise<NotificationList> {
    const { data } = await api.get<NotificationList>('/api/notifications/', {
      params: { unread_only: unreadOnly, limit: 50 },
    })
    return data
  },
  async unreadCount(): Promise<number> {
    const { data } = await api.get<{ unread: number }>('/api/notifications/unread-count')
    return data.unread
  },
  async markRead(id: string): Promise<void> {
    await api.post(`/api/notifications/${id}/read`)
  },
  async markAllRead(): Promise<void> {
    await api.post('/api/notifications/read-all')
  },
}

// ---------------------------------------------------------------------------
// Audit log (admin)
// ---------------------------------------------------------------------------
export const auditApi = {
  async list(filters: { page?: number; page_size?: number; action?: string; entity_type?: string; search?: string } = {}): Promise<AuditList> {
    const page = filters.page ?? 1
    const pageSize = filters.page_size ?? 50
    const params: Record<string, any> = { page, page_size: pageSize }
    if (filters.action) params.action = filters.action
    if (filters.entity_type) params.entity_type = filters.entity_type
    if (filters.search) params.search = filters.search
    const { data } = await api.get('/api/audit/', { params })
    return data
  },
}

// ---------------------------------------------------------------------------
// Recycle bin
// ---------------------------------------------------------------------------
export const trashApi = {
  async list(): Promise<TrashList> {
    const { data } = await api.get<TrashList>('/api/trash/')
    return data
  },
  async restore(entity: string, id: string): Promise<void> {
    await api.post(`/api/trash/${entity}/${id}/restore`)
  },
}

// ---------------------------------------------------------------------------
// File download helper (authenticated): fetches a binary endpoint as a blob and
// triggers a browser download with the server-provided filename.
// ---------------------------------------------------------------------------
export async function downloadFile(url: string, fallbackName: string): Promise<void> {
  const resp = await api.get(url, { responseType: 'blob' })
  const disposition: string = resp.headers['content-disposition'] || ''
  const match = disposition.match(/filename="?([^"]+)"?/)
  const filename = match ? match[1] : fallbackName

  const blobUrl = window.URL.createObjectURL(resp.data as Blob)
  const a = document.createElement('a')
  a.href = blobUrl
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(blobUrl)
}

// ---------------------------------------------------------------------------
// Reports
// ---------------------------------------------------------------------------
export const reportsApi = {
  async portfolio(): Promise<PortfolioReport> {
    const { data } = await api.get<PortfolioReport>('/api/reports/portfolio')
    return data
  },
  async topExposures(limit = 10): Promise<TopExposures> {
    const { data } = await api.get<TopExposures>('/api/reports/top-exposures', {
      params: { limit },
    })
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
