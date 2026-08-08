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
  StaffMember,
  Department,
  LetterSummary,
  LetterFull,
  NotificationList,
  ImportResult,
  SettingsResponse,
  EditableSetting,
  FxRates,
  AIOverview,
  AIProvider,
  AIModel,
  AITaskRoute,
  AIProviderUpdate,
  AIModelCreate,
  AIModelUpdate,
  AITaskRouteUpdate,
  AITestResult,
  AISyncResult,
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
// Mortgaged-properties register (one backend source, linked to customers)
// ---------------------------------------------------------------------------
export interface PropertyRow {
  id: string; ac_no: string; customer: string; customer_id: string | null
  deed_no: string; city: string; zone: string; type: string; age: string
  land_m2: string; infra_m2: string; mortgage_date: string; amount: number | null
  currency: string; valuation_date: string; valuation: number | null
  owner: string; insurance_expiry: string
}
export interface PropertyList {
  items: PropertyRow[]; total: number; page: number; page_size: number
  totals: { aed: number; irr: number; customers: number }
}
export const propertiesApi = {
  async list(params: {
    search?: string; city?: string; type?: string; currency?: string
    sort_by?: string; sort_order?: 'asc' | 'desc'; page?: number; page_size?: number
  } = {}): Promise<PropertyList> {
    const { data } = await api.get<PropertyList>('/api/properties/', { params })
    return data
  },
  async facets(): Promise<{ cities: string[]; types: string[] }> {
    const { data } = await api.get<{ cities: string[]; types: string[] }>('/api/properties/facets')
    return data
  },
  /** Create a property from the register (auto-links/creates its customer). */
  async create(body: Record<string, any>): Promise<any> {
    const { data } = await api.post('/api/properties/', body)
    return data
  },
  async update(id: string, body: Record<string, any>): Promise<any> {
    const { data } = await api.put(`/api/properties/${id}`, body)
    return data
  },
  async remove(id: string): Promise<void> {
    await api.delete(`/api/properties/${id}`)
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
  async toggleFacilityChecklist(facilityId: string, step: number, done: boolean): Promise<any> {
    const { data } = await api.patch(`/api/crm/facility-checklist/${encodeURIComponent(facilityId)}`, { step, done })
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
  async listGuarantors(accountNo: string): Promise<any[]> {
    const { data } = await api.get(`/api/crm/guarantors/${encodeURIComponent(accountNo)}`)
    return data
  },
  async releaseCheque(accountNo: string, body: { cheque_no: string; facility_id?: string; settled_facility?: string; date?: string; note?: string; guarantor_name?: string; cheque_amount?: number; branch?: string }): Promise<any> {
    const { data } = await api.post(`/api/crm/guarantors/${encodeURIComponent(accountNo)}/release`, body)
    return data
  },
  async addGuarantor(accountNo: string, body: { guarantor_name: string; guarantor_account?: string; cheque_no?: string; cheque_amount?: number; issuing_bank?: string; pim_ref?: string; facility_id?: string; branch?: string; id?: string }): Promise<any> {
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
  async completeness(accountNo: string): Promise<{ percent: number; filled: number; total: number; missing: string[] }> {
    const { data } = await api.get(`/api/crm/completeness/${encodeURIComponent(accountNo)}`)
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
  async runExpiryScan(): Promise<{ warning_days: number; facilities: number; documents: number; total: number }> {
    const { data } = await api.post('/api/crm/run-expiry-scan')
    return data
  },
  async driveStatus(): Promise<any> {
    const { data } = await api.get('/api/crm/backup/drive/status')
    return data
  },
  async driveSyncNow(): Promise<any> {
    const { data } = await api.post('/api/crm/backup/drive/sync')
    return data
  },
  async driveDisconnect(): Promise<any> {
    const { data } = await api.post('/api/auth/google/drive/disconnect')
    return data
  },
  async dailyLog(text: string, followup_date = ''): Promise<{ accounts_found: string[]; routed: any[]; unknown_accounts: string[] }> {
    const { data } = await api.post('/api/crm/daily-log', { text, followup_date })
    return data
  },
  async addNote(accountNo: string, body: { title?: string; content: string; category?: string; reminder_date?: string }): Promise<any> {
    const { data } = await api.post(`/api/crm/notes/${encodeURIComponent(accountNo)}`, body)
    return data
  },
  async emailSummary(accountNo: string, to: string): Promise<any> {
    const { data } = await api.post(`/api/crm/email-summary/${encodeURIComponent(accountNo)}`, { to })
    return data
  },
  async offerLetterData(accountNo: string): Promise<any> {
    const { data } = await api.get(`/api/crm/offer-letter-data/${encodeURIComponent(accountNo)}`)
    return data
  },
  // Facility-type catalog for the Offer Letter combobox (built-ins + user-added).
  async facilityTypes(): Promise<{ ok: boolean; types: string[] }> {
    const { data } = await api.get('/api/crm/facility-types')
    return data
  },
  // Adds a NEW type to the catalog; a name-similar existing entry is matched
  // instead of creating a near-duplicate ({added:false, matched}).
  async addFacilityType(name: string): Promise<{ ok: boolean; added: boolean; matched: string; types: string[] }> {
    const { data } = await api.post('/api/crm/facility-types', { name })
    return data
  },
  async saveOfferLetterData(accountNo: string, body: { POBox?: string; CityCountry?: string; Salutation?: string; Branch?: string; snapshot?: Record<string, any>; snapshot_key?: string; fields?: Record<string, any> }): Promise<any> {
    const { data } = await api.post(`/api/crm/offer-letter-data/${encodeURIComponent(accountNo)}`, body)
    return data
  },
  // Credit Approval (مصوبه) form: first-class persistence (credit_reviews + profile cols).
  async saveSanction(accountNo: string, body: { snapshot: Record<string, any>; limits?: any[]; recip?: any[]; fin?: any[]; guars?: any[]; banks?: any[] }): Promise<any> {
    const { data } = await api.post(`/api/crm/sanction/${encodeURIComponent(accountNo)}`, body)
    return data
  },
  async listCreditReviews(accountNo: string): Promise<any[]> {
    const { data } = await api.get(`/api/crm/credit-reviews/${encodeURIComponent(accountNo)}`)
    return data
  },
  // Parse a filled committee-approval draft (.docx) → prefill fields + persist to DB.
  async extractDraft(accountNo: string, file: File): Promise<any> {
    const form = new FormData()
    form.append('file', file)
    if (accountNo) form.append('account_no', accountNo)
    const { data } = await api.post('/api/crm/extract-draft', form, { headers: { 'Content-Type': 'multipart/form-data' } })
    return data
  },

  // ---- Profile child records: mortgaged properties / fixed deposits / partners ----
  async addProperty(accountNo: string, body: Record<string, any>): Promise<any> {
    const { data } = await api.post(`/api/crm/properties/${encodeURIComponent(accountNo)}`, body)
    return data
  },
  async updateProperty(id: string, body: Record<string, any>): Promise<any> {
    const { data } = await api.patch(`/api/crm/properties/${encodeURIComponent(id)}`, body)
    return data
  },
  async deleteProperty(id: string): Promise<void> {
    await api.delete(`/api/crm/properties/${encodeURIComponent(id)}`)
  },
  // property EVENT TIMELINE (several valuations, mortgage/re-mortgage/release/insurance)
  async addPropertyEvent(propertyId: string, body: { event_type: string; event_date?: string; amount?: number; currency?: string; remarks?: string }): Promise<any> {
    const { data } = await api.post(`/api/crm/properties/${encodeURIComponent(propertyId)}/events`, body)
    return data
  },
  async deletePropertyEvent(id: string): Promise<void> {
    await api.delete(`/api/crm/property-events/${encodeURIComponent(id)}`)
  },
  async addFixedDeposit(accountNo: string, body: Record<string, any>): Promise<any> {
    const { data } = await api.post(`/api/crm/fixed-deposits/${encodeURIComponent(accountNo)}`, body)
    return data
  },
  async updateFixedDeposit(id: string, body: Record<string, any>): Promise<any> {
    const { data } = await api.patch(`/api/crm/fixed-deposits/${encodeURIComponent(id)}`, body)
    return data
  },
  async deleteFixedDeposit(id: string): Promise<void> {
    await api.delete(`/api/crm/fixed-deposits/${encodeURIComponent(id)}`)
  },
  async addPartner(accountNo: string, body: Record<string, any>): Promise<any> {
    const { data } = await api.post(`/api/crm/partners/${encodeURIComponent(accountNo)}`, body)
    return data
  },
  async partnerNames(): Promise<string[]> {
    const { data } = await api.get('/api/crm/partner-names')
    return data
  },
  async updatePartner(id: string, body: Record<string, any>): Promise<any> {
    const { data } = await api.patch(`/api/crm/partners/${encodeURIComponent(id)}`, body)
    return data
  },
  async deletePartner(id: string): Promise<void> {
    await api.delete(`/api/crm/partners/${encodeURIComponent(id)}`)
  },

  // ---- Document attachments (real upload / download / delete) ----
  async uploadAttachment(
    accountNo: string,
    file: File,
    opts: { facility_id?: string; row_index?: string; is_shared?: boolean; notes?: string } = {},
  ): Promise<any> {
    const form = new FormData()
    form.append('file', file)
    if (opts.facility_id) form.append('facility_id', opts.facility_id)
    if (opts.row_index) form.append('row_index', opts.row_index)
    form.append('is_shared', opts.is_shared ? 'true' : 'false')
    if (opts.notes) form.append('notes', opts.notes)
    const { data } = await api.post(`/api/crm/attachments/${encodeURIComponent(accountNo)}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },
  async deleteAttachment(id: string): Promise<void> {
    await api.delete(`/api/crm/attachments/${encodeURIComponent(id)}`)
  },
  // Fetch an attachment's bytes (authed) so it can be opened inline in a new tab.
  async attachmentBlob(id: string): Promise<Blob> {
    const { data } = await api.get(`/api/crm/attachments/${encodeURIComponent(id)}/view`, { responseType: 'blob' })
    return data
  },
}

// ---------------------------------------------------------------------------
// Schedule-of-Charges tariff (editable — tariffs change yearly) + the
// offer-letter processing-charge calculator.
// ---------------------------------------------------------------------------
export interface ChargeRule {
  id: string
  segment: 'corporate' | 'individual'
  rule_key: string
  label: string
  method: 'per_mille' | 'percent' | 'flat'
  rate: number
  min_charge: number | null
  max_charge: number | null
  small_threshold: number | null
  small_min_charge: number | null
  notes: string
  version: string
  enabled: boolean
  sort_order: number
}
export interface ChargeComputeItem {
  facility_type: string
  amount: string
  covered_by_fd?: boolean
  staff_facility?: boolean
  temporary?: boolean
}
export const chargeTariffApi = {
  async list(): Promise<{ rules: ChargeRule[]; rule_keys: string[] }> {
    const { data } = await api.get('/api/charge-tariff')
    return data
  },
  async save(rule: Partial<ChargeRule>): Promise<{ ok: boolean; created: boolean; rule: ChargeRule }> {
    const { data } = await api.post('/api/charge-tariff', rule)
    return data
  },
  async remove(id: string): Promise<void> {
    await api.delete(`/api/charge-tariff/${encodeURIComponent(id)}`)
  },
  async compute(segment: 'corporate' | 'individual', items: ChargeComputeItem[]):
    Promise<{ ok: boolean; total: number; lines: { label: string; base: number; charge: number; rule_key: string; note: string }[]; warnings: string[] }> {
    const { data } = await api.post('/api/charge-tariff/compute', { segment, items })
    return data
  },
}

// ---------------------------------------------------------------------------
// General (non-account) profiles + checklists (A7)
// ---------------------------------------------------------------------------
export const generalApi = {
  async listProfiles(): Promise<{ items: any[]; total: number }> {
    const { data } = await api.get('/api/general/profiles')
    return data
  },
  async createProfile(body: { title: string; category?: string }): Promise<any> {
    const { data } = await api.post('/api/general/profiles', body)
    return data
  },
  async deleteProfile(id: string): Promise<void> {
    await api.delete(`/api/general/profiles/${encodeURIComponent(id)}`)
  },
  async listChecklists(profileId: string): Promise<{ profile_id: string; checklists: any[] }> {
    const { data } = await api.get(`/api/general/profiles/${encodeURIComponent(profileId)}/checklists`)
    return data
  },
  async createChecklist(profileId: string, body: { title: string }): Promise<any> {
    const { data } = await api.post(`/api/general/profiles/${encodeURIComponent(profileId)}/checklists`, body)
    return data
  },
  async deleteChecklist(id: string): Promise<void> {
    await api.delete(`/api/general/checklists/${encodeURIComponent(id)}`)
  },
  async addItem(checklistId: string, body: { text: string }): Promise<any> {
    const { data } = await api.post(`/api/general/checklists/${encodeURIComponent(checklistId)}/items`, body)
    return data
  },
  async updateItem(id: string, body: { is_done?: boolean; text?: string }): Promise<any> {
    const { data } = await api.patch(`/api/general/items/${encodeURIComponent(id)}`, body)
    return data
  },
  async deleteItem(id: string): Promise<void> {
    await api.delete(`/api/general/items/${encodeURIComponent(id)}`)
  },
}

// ---------------------------------------------------------------------------
// Personal (private, per-user) notes + email digest (A8/A11/A16)
// ---------------------------------------------------------------------------
export const personalApi = {
  async list(): Promise<{ items: any[]; total: number }> {
    const { data } = await api.get('/api/personal/notes')
    return data
  },
  async add(body: { content: string; category?: string }): Promise<any> {
    const { data } = await api.post('/api/personal/notes', body)
    return data
  },
  async update(id: string, body: { is_done?: boolean; content?: string }): Promise<any> {
    const { data } = await api.patch(`/api/personal/notes/${encodeURIComponent(id)}`, body)
    return data
  },
  async remove(id: string): Promise<void> {
    await api.delete(`/api/personal/notes/${encodeURIComponent(id)}`)
  },
  async sendEmail(): Promise<{ ok: boolean; sent: number; to?: string; message?: string }> {
    const { data } = await api.post('/api/personal/notes/send-email')
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
// Telegram integration (two-way notifications + bot control)
// ---------------------------------------------------------------------------
export interface TelegramPrefs {
  events: Record<string, boolean>
  sound: Record<string, boolean>
  channels: Record<string, { enabled: boolean }>
  min_priority: 'low' | 'medium' | 'high' | 'critical'
  include_buttons: boolean
  app_base_url: string
  allowed_chat_ids: string[]
}

export interface TelegramStatus {
  prefs: TelegramPrefs
  allowed_chat_ids: string[]
  channels: Record<string, { configured_via_env: boolean; enabled_pref: boolean; ready: boolean }>
  events_registry: Record<string, { label: string; help: string; icon: string; group: string }>
  event_groups: Array<{ id: string; title: string; icon: string }>
}

export const telegramApi = {
  async status(): Promise<TelegramStatus> {
    const { data } = await api.get<TelegramStatus>('/api/telegram/status')
    return data
  },
  async updatePrefs(partial: Partial<TelegramPrefs>): Promise<{ ok: boolean; prefs: TelegramPrefs }> {
    const { data } = await api.put('/api/telegram/prefs', partial)
    return data
  },
  async test(): Promise<{ ok: boolean; results: Array<Record<string, unknown>> }> {
    const { data } = await api.post('/api/telegram/test')
    return data
  },
  async webhookInfo(): Promise<Record<string, unknown>> {
    const { data } = await api.get('/api/telegram/webhook-info')
    return data
  },
  async setWebhook(webhook_url: string): Promise<Record<string, unknown>> {
    const { data } = await api.post('/api/telegram/set-webhook', { webhook_url })
    return data
  },
  async deleteWebhook(): Promise<Record<string, unknown>> {
    const { data } = await api.post('/api/telegram/delete-webhook')
    return data
  },
}

// ---------------------------------------------------------------------------
// AI models & providers (the central AI control layer)
// ---------------------------------------------------------------------------
export const aiApi = {
  async overview(): Promise<AIOverview> {
    const { data } = await api.get<AIOverview>('/api/ai/overview')
    return data
  },
  async updateProvider(key: string, payload: AIProviderUpdate): Promise<AIProvider> {
    const { data } = await api.put<AIProvider>(`/api/ai/providers/${key}`, payload)
    return data
  },
  async createModel(payload: AIModelCreate): Promise<AIModel> {
    const { data } = await api.post<AIModel>('/api/ai/models', payload)
    return data
  },
  async updateModel(id: number, payload: AIModelUpdate): Promise<AIModel> {
    const { data } = await api.put<AIModel>(`/api/ai/models/${id}`, payload)
    return data
  },
  async deleteModel(id: number): Promise<{ deleted: string }> {
    const { data } = await api.delete<{ deleted: string }>(`/api/ai/models/${id}`)
    return data
  },
  async testModel(id: number): Promise<AITestResult> {
    const { data } = await api.post<AITestResult>(`/api/ai/models/${id}/test`)
    return data
  },
  async syncModels(key: string): Promise<AISyncResult> {
    const { data } = await api.post<AISyncResult>(`/api/ai/providers/${key}/sync-models`)
    return data
  },
  async updateRoute(task: string, payload: AITaskRouteUpdate): Promise<AITaskRoute> {
    const { data } = await api.put<AITaskRoute>(`/api/ai/routes/${task}`, payload)
    return data
  },
}

// ---------------------------------------------------------------------------
// AI letter-assistant — propose reviewable edits to an official letter. The
// backend returns *proposals only* (validated, never auto-applied); the UI shows
// them with checkboxes and applies only the ticked ones client-side.
// ---------------------------------------------------------------------------
export type LetterAiModel = { id: number; display_name: string; provider_key: string; provider_name: string; capabilities: string[]; priority: number }
export type LetterAiTool = { id: string; label: string }
export type LetterAiChange = {
  id: string; category: string; field: string; op: 'set_field' | 'text_replace' | 'note' | 'db_write' | 'link' | 'table_replace' | 'table_insert' | 'paragraph_merge' | 'kb_write'
  title: string; detail: string; severity: 'low' | 'medium' | 'high'
  find?: string; replace?: string; occurrence?: 'first' | 'all'
  before?: string; after?: string; applicable: boolean
  // table_replace only — 1-based index into the tables[] sent with analyze + the sanitized new HTML
  table_index?: number; html?: string
  // table_insert only — a brand-new sanitized table + where it lands
  placement?: 'body' | 'attachment'; table_title?: string
  // paragraph_merge only — scattered pieces to stitch (part 1 → replace, rest deleted)
  parts?: string[]
  // db_write only — the extracted profile fact + its resolved target customer
  account_no?: string; customer_name?: string; key?: string; value?: string
  action?: 'add' | 'update'; resolution?: string; exists?: boolean
  // link only — profile↔profile relationship proposal (kind + exact reason)
  related_account?: string; related_name?: string; kind?: string; reason?: string
  // kb_write only — general/educational content grouped under a KB topic
  topic?: string; kb_category?: string; content?: string; source_note?: string
  source_file?: string
}
export type KbEntry = { id: string; content: string; source_kind: string; source_ref: string; account_no?: string; created_by?: string; created_at?: string }
export type KbTopic = { id: string; title: string; category: string; entries: KbEntry[] }
export const knowledgeApi = {
  async list(): Promise<{ topics: KbTopic[]; categories: string[]; count: number }> {
    const { data } = await api.get('/api/knowledge/')
    return data
  },
  async addEntry(body: { topic_title: string; content: string; category?: string; source_ref?: string }): Promise<any> {
    const { data } = await api.post('/api/knowledge/entries', body)
    return data
  },
  async deleteEntry(id: string): Promise<any> {
    const { data } = await api.delete(`/api/knowledge/entries/${encodeURIComponent(id)}`)
    return data
  },
}
export type LetterAiDbOutcome = { account_no: string; key: string; outcome: string; profile_created?: boolean; reason?: string }
export const letterAiApi = {
  async models(): Promise<{ ok: boolean; models: LetterAiModel[]; tools: LetterAiTool[]; available: boolean }> {
    const { data } = await api.get('/api/letter-ai/models')
    return data
  },
  async analyze(body: { account_no?: string; fields: Record<string, any>; tools: string[]; instruction?: string; selection?: string; selections?: string[]; tables?: string[]; attachment_tables?: string[]; attachments_text?: { name: string; text: string }[]; model_id?: number | null }): Promise<{ ok: boolean; error?: string; model?: string; changes: LetterAiChange[]; count?: number; facts_used?: boolean; tools?: string[] }> {
    const { data } = await api.post('/api/letter-ai/analyze', body, { timeout: 300000 })
    return data
  },
  // Persist the user-approved extracted facts into the right customer profile(s)
  // + create approved profile↔profile links (kind + exact reason) + approved
  // Knowledge-Base items (grouped under topics with provenance).
  async applyDb(body: { items: { account_no: string; customer_name?: string; key: string; value: string }[]; links?: { account_no: string; related_account: string; kind: string; reason: string }[]; kb_items?: { topic: string; content: string; category?: string; source_note?: string; account_no?: string }[]; source_ref?: string }): Promise<{ ok: boolean; outcomes: LetterAiDbOutcome[]; counts: { added: number; updated: number; skipped: number; profiles_created: number }; links_created?: number; kb_added?: number; kb_skipped?: number }> {
    const { data } = await api.post('/api/letter-ai/apply-db', body)
    return data
  },
  // Readable TEXT of one attachment (full_check pass) — never writes anything.
  async attachmentText(attachmentId: string, body: { model_id?: number | null } = {}): Promise<{ ok: boolean; error?: string; file?: string; text?: string; model?: string }> {
    const { data } = await api.post(`/api/letter-ai/attachment-text/${encodeURIComponent(attachmentId)}`, body, { timeout: 300000 })
    return data
  },
  // Deep extraction from ONE letter attachment (UI runs them sequentially).
  // Long timeout: chunked model calls over a large file can take minutes.
  async extractAttachment(attachmentId: string, body: { account_no?: string; customer_name?: string; subject?: string; body_excerpt?: string; model_id?: number | null; allow_ai_generated?: boolean }): Promise<{ ok: boolean; error?: string; changes: LetterAiChange[]; model?: string; chunk_errors?: string[]; file?: string; suggestions?: any[] }> {
    const { data } = await api.post(`/api/letter-ai/extract-attachment/${encodeURIComponent(attachmentId)}`, body, { timeout: 420000 })
    return data
  },
  // AI builds a REAL file attachment (Excel/Word) from an instruction and/or a
  // TEMPLATE file's text — data only from the DB facts; stored like a manual
  // upload, marked ai_generated.
  async generateAttachment(body: { letter_id: string; account_no?: string; instruction: string; kind?: 'excel' | 'word'; subject?: string; recipient?: string; body_excerpt?: string; model_id?: number | null; template_text?: string; template_name?: string; source_files?: { name: string; text: string }[] }): Promise<{ ok: boolean; error?: string; model?: string; kind?: string; warnings?: string[]; attachment?: LetterAttachment }> {
    const { data } = await api.post('/api/letter-ai/generate-attachment', body, { timeout: 420000 })
    return data
  },
  // Readable TEXT of a local TEMPLATE/SAMPLE file (any format) — nothing stored.
  async templateText(file: File, modelId?: number | null): Promise<{ ok: boolean; error?: string; file?: string; text?: string; model?: string }> {
    const form = new FormData()
    form.append('file', file)
    if (modelId != null) form.append('model_id', String(modelId))
    const { data } = await api.post('/api/letter-ai/template-text', form, {
      headers: { 'Content-Type': 'multipart/form-data' }, timeout: 300000,
    })
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
  // AI document import: list document/vision models (wired from Settings) + analyze a file.
  async aiModels(): Promise<{ models: any[]; drive_enabled: boolean }> {
    const { data } = await api.get('/api/imports/ai-models')
    return data
  },
  async analyzeDocument(file: File, modelId?: number, onTick?: () => void, instructions?: string): Promise<any> {
    // Start a background job (returns immediately), then poll until done — so a
    // long extraction never hits the HTTP gateway timeout.
    const form = new FormData()
    form.append('file', file)
    if (modelId != null) form.append('model_id', String(modelId))
    // v103 — operator's free-text guidance for the extraction model (optional)
    if (instructions && instructions.trim()) form.append('instructions', instructions.trim())
    const { data: start } = await api.post('/api/imports/analyze', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000, // generous: this only covers the file UPLOAD
    })
    const jobId = start.job_id
    if (!jobId) return start
    const deadline = Date.now() + 25 * 60 * 1000 // poll up to 25 min
    while (Date.now() < deadline) {
      await new Promise((r) => setTimeout(r, 3000))
      if (onTick) onTick()
      let j: any
      try {
        j = (await api.get(`/api/imports/jobs/${jobId}`)).data
      } catch (e: any) {
        // A long poll will occasionally hit a network blip or a 5xx gateway
        // hiccup — keep waiting. Only a 4xx (e.g. the job genuinely expired) is
        // terminal.
        if (!e?.response || e.response.status >= 500) continue
        throw e
      }
      if (j.status === 'done') return j.result
      if (j.status === 'error') {
        const err: any = new Error('extraction failed')
        err.response = { data: { detail: j.detail }, status: j.http_status || 500 }
        throw err
      }
    }
    throw new Error('Extraction is taking too long; please try a smaller file.')
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
  async list(filters: { page?: number; page_size?: number; action?: string; entity_type?: string; account_no?: string; search?: string; date_from?: string; date_to?: string } = {}): Promise<AuditList> {
    const page = filters.page ?? 1
    const pageSize = filters.page_size ?? 50
    const params: Record<string, any> = { page, page_size: pageSize }
    if (filters.action) params.action = filters.action
    if (filters.entity_type) params.entity_type = filters.entity_type
    if (filters.account_no) params.account_no = filters.account_no
    if (filters.search) params.search = filters.search
    if (filters.date_from) params.date_from = filters.date_from
    if (filters.date_to) params.date_to = filters.date_to
    const { data } = await api.get('/api/audit/', { params })
    return data
  },
  // One customer's activity log (powers the profile «Logs» tab).
  async listForCustomer(accountNo: string, filters: { page?: number; page_size?: number; action?: string; search?: string; date_from?: string; date_to?: string } = {}): Promise<AuditList> {
    const params: Record<string, any> = { page: filters.page ?? 1, page_size: filters.page_size ?? 25 }
    if (filters.action) params.action = filters.action
    if (filters.search) params.search = filters.search
    if (filters.date_from) params.date_from = filters.date_from
    if (filters.date_to) params.date_to = filters.date_to
    const { data } = await api.get(`/api/audit/customer/${encodeURIComponent(accountNo)}`, { params })
    return data
  },
  // Record an action performed in the SPA (printed voucher / official letter, …).
  // Best-effort: never throws so it can't break the user's print/save flow.
  async logActivity(a: { action: string; entity_type?: string; entity_id?: string; account_no?: string; detail?: string }): Promise<void> {
    try { await api.post('/api/audit/activity', a) } catch { /* logging must not break the action */ }
  },
}

// ---------------------------------------------------------------------------
// Staff directory (bank employees) — editable; names carry a Persian equivalent.
// ---------------------------------------------------------------------------
export const staffApi = {
  async list(params: { q?: string; region?: string; department?: string } = {}): Promise<{ items: StaffMember[]; total: number }> {
    const { data } = await api.get('/api/staff/', { params })
    return data
  },
  async departments(region?: string): Promise<string[]> {
    const { data } = await api.get('/api/staff/departments', { params: region ? { region } : {} })
    return data
  },
  async create(payload: Partial<StaffMember>): Promise<StaffMember> {
    const { data } = await api.post('/api/staff/', payload)
    return data
  },
  async update(id: string, payload: Partial<StaffMember>): Promise<StaffMember> {
    const { data } = await api.patch(`/api/staff/${id}`, payload)
    return data
  },
  async remove(id: string): Promise<void> {
    await api.delete(`/api/staff/${id}`)
  },
}

// ---------------------------------------------------------------------------
// Recipient departments + managers (with manager history) — letter «گیرنده» fields.
// ---------------------------------------------------------------------------
export const departmentsApi = {
  async list(q?: string): Promise<Department[]> {
    const { data } = await api.get('/api/departments/', { params: q ? { q } : {} })
    return data
  },
  async resolve(payload: { name: string; name_fa?: string; manager?: string; manager_fa?: string; manager_title?: string }): Promise<Department> {
    const { data } = await api.post('/api/departments/resolve', payload)
    return data
  },
  async update(id: string, payload: Partial<Department>): Promise<Department> {
    const { data } = await api.patch(`/api/departments/${id}`, payload)
    return data
  },
  async remove(id: string): Promise<void> { await api.delete(`/api/departments/${id}`) },
}

// ---------------------------------------------------------------------------
// Saved letters — under an account (auto-creates the profile) or general.
// ---------------------------------------------------------------------------
export type LetterAttachment = { id: string; account_no?: string; original_name: string; file_size?: string; upload_date?: string; uploaded_by?: string; storage: 'drive' | 'disk'; ai_generated?: boolean }
export const lettersApi = {
  async attachments(letterId: string): Promise<LetterAttachment[]> {
    const { data } = await api.get(`/api/letters/${encodeURIComponent(letterId)}/attachments`)
    return data
  },
  async list(params: { account_no?: string; general?: boolean } = {}): Promise<LetterSummary[]> {
    const { data } = await api.get('/api/letters/', { params })
    return data
  },
  async get(id: string): Promise<LetterFull> {
    const { data } = await api.get(`/api/letters/${id}`)
    return data
  },
  async save(payload: { id?: string; account_no?: string; general?: boolean; title?: string; subject?: string; recipient_dept?: string; recipient_manager?: string; values?: any; layout?: any; labels?: any }): Promise<LetterFull> {
    if (payload.id) { const { data } = await api.patch(`/api/letters/${payload.id}`, payload); return data }
    const { data } = await api.post('/api/letters/', payload)
    return data
  },
  async remove(id: string): Promise<void> { await api.delete(`/api/letters/${id}`) },
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
// Database cleanup / de-duplication (admin) — REVIEW FIRST
// ---------------------------------------------------------------------------
export interface CleanupRef { id: string; summary: string }
export interface CleanupGroup {
  account_no: string
  customer_name: string
  keeper: CleanupRef
  removals: CleanupRef[]
  conflict_fields: string[]
  reason: string
  confidence: 'certain' | 'probable'
}
export interface CleanupFacilityReview {
  account_no: string
  customer_name: string
  rows: CleanupRef[]
}
export interface CleanupReport {
  generated_at: string
  groups: Record<string, CleanupGroup[]>
  review: { facilities: CleanupFacilityReview[] }
  counts: Record<string, number>
}
export interface CleanupApplyResult {
  applied_at: string
  removed: Record<string, number>
}
export interface CleanupRun {
  id: string
  kind: string
  trigger: string
  username: string
  counts: Record<string, number>
  detail: string
  created_at: string | null
}
export interface CleanupModel {
  id: number
  name: string
  provider?: string
  priority?: number
}
export interface CleanupConfig {
  schedule: string
  ai_review: string
  last_run: string
  schedules: string[]
  models: CleanupModel[]
  active_model: string | null
  ai_available: boolean
}
export interface CleanupAIVerdictItem {
  id: string
  same: boolean
  confidence: number
  reason: string
}
export interface CleanupAIGroupVerdict {
  entity: string
  label: string
  account_no: string
  customer_name: string
  keeper: CleanupRef
  verdicts: CleanupAIVerdictItem[]
}
export interface CleanupAIReview {
  available: boolean
  reason?: string
  note?: string
  model?: string
  verdicts?: CleanupAIGroupVerdict[]
  confirmed_ids?: string[]
  calls?: number
}

export const cleanupApi = {
  async scan(): Promise<CleanupReport> {
    const { data } = await api.post<CleanupReport>('/api/cleanup/scan')
    return data
  },
  async apply(only?: string[], confirmIds?: string[]): Promise<CleanupApplyResult> {
    const { data } = await api.post<CleanupApplyResult>('/api/cleanup/apply',
      { only: only ?? null, confirm_ids: confirmIds ?? null })
    return data
  },
  async history(limit = 30): Promise<{ runs: CleanupRun[] }> {
    const { data } = await api.get<{ runs: CleanupRun[] }>('/api/cleanup/history', { params: { limit } })
    return data
  },
  async getConfig(): Promise<CleanupConfig> {
    const { data } = await api.get<CleanupConfig>('/api/cleanup/config')
    return data
  },
  async updateConfig(body: { schedule?: string; ai_review?: string }): Promise<CleanupConfig> {
    const { data } = await api.put<CleanupConfig>('/api/cleanup/config', body)
    return data
  },
  async aiReview(): Promise<CleanupAIReview> {
    const { data } = await api.post<CleanupAIReview>('/api/cleanup/ai-review')
    return data
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
