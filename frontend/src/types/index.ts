// User types
export interface User {
  id: string
  username: string
  email: string
  full_name: string | null
  is_active: boolean
  is_admin: boolean
}

// Customer types
export interface Customer {
  id: string
  account_no: string
  name: string
  name_ar: string | null
  account_type: string
  status: string
  email: string | null
  phone: string | null
  mobile: string | null
  address: string | null
  branch: string | null
  relationship_manager: string | null
  notes: string | null
  created_at: string
  updated_at: string | null
}

export interface CustomerList {
  items: Customer[]
  total: number
  page: number
  page_size: number
}

// Facility types
export interface Facility {
  id: string
  customer_id: string
  customer_name: string | null
  facility_type: string
  name: string | null
  status: string
  amount: number
  outstanding: number
  currency: string
  start_date: string | null
  expiry_date: string | null
  interest_rate: number | null
  tenor_months: string | null
  notes: string | null
  created_at: string
  updated_at: string | null
}

export interface FacilityList {
  items: Facility[]
  total: number
  page: number
  page_size: number
}

// Dashboard types — flat contract matching backend DashboardStatsResponse.
export interface RecentActivity {
  id: number
  action: string
  timestamp: string | null
  user: string
}

export interface RecentCustomerStat {
  id: string
  account_no: string | null
  name: string
  status: string | null
  created_at: string | null
}

export interface TotalExposure {
  amount: number
  currency: string
}

export interface BreakdownItem {
  label: string
  count: number
  amount: number
}

export interface MonthlyTrendItem {
  month: string
  exposure: number
  facilities: number
}

export interface ExpiringFacility {
  id: string
  name: string | null
  customer_id: string | null
  customer_name: string | null
  facility_type: string | null
  amount: number
  currency: string
  expiry_date: string | null
  days_to_expiry: number | null
  status: string | null
}

// Audit log
export interface AuditEntry {
  id: string
  user_id: string | null
  username: string | null
  action: string
  entity_type: string | null
  entity_id: string | null
  detail: string | null
  ip_address: string | null
  created_at: string | null
}

export interface AuditList {
  items: AuditEntry[]
  total: number
  page: number
  page_size: number
}

// Recycle bin
export interface TrashItem {
  id: string
  label: string
  sublabel: string | null
  type: 'customer' | 'facility' | 'offer_letter'
}

export interface TrashList {
  items: TrashItem[]
  total: number
  counts: { customers: number; facilities: number; offer_letters: number }
}

// Admin user management
export interface AdminUser {
  id: string
  username: string
  email: string
  full_name: string | null
  is_active: boolean
  is_admin: boolean
  created_at: string | null
  last_login: string | null
}

export interface AdminUserList {
  items: AdminUser[]
  total: number
  page: number
  page_size: number
}

export interface AdminUserForm {
  username: string
  email: string
  password: string
  full_name: string
  is_admin: boolean
  is_active: boolean
}

export interface FacilityDetail {
  facility: Facility
  customer_name: string | null
  customer_account_no: string | null
}

// Customer detail + reporting types
export interface CustomerDetailSummary {
  total_facilities: number
  active_facilities: number
  total_offers: number
  total_exposure: number
  total_outstanding: number
  currency: string
}

export interface CustomerDetail {
  customer: Customer
  facilities: Facility[]
  offer_letters: OfferLetter[]
  summary: CustomerDetailSummary
}

export interface PortfolioReport {
  summary: {
    total_customers: number
    total_facilities: number
    total_exposure: number
    total_outstanding: number
    available_headroom: number
    utilisation_pct: number
    currency: string
  }
  facilities_by_type: BreakdownItem[]
  facilities_by_status: BreakdownItem[]
  facilities_by_risk: BreakdownItem[]
  customers_by_branch: BreakdownItem[]
  customers_by_type: BreakdownItem[]
}

export interface TopExposureItem {
  customer_id: string
  name: string
  account_no: string | null
  exposure: number
  facilities: number
}

export interface TopExposures {
  items: TopExposureItem[]
}

// Offer-letter types
export interface OfferLetter {
  id: string
  customer_id: string
  facility_id: string | null
  offer_date: string | null
  expiry_date: string | null
  status: string | null
  principal_amount: number
  currency: string
  interest_rate: number
  tenor_months: number
  grace_period_months: number | null
  repayment_type: string | null
  monthly_installment: number | null
  total_repayment_amount: number | null
  purpose_of_facility: string | null
  created_at: string | null
}

export interface OfferInstallment {
  installment_number: number
  payment_date: string | null
  opening_balance: number
  principal_payment: number
  interest_payment: number
  total_payment: number
  closing_balance: number
}

export interface OfferLetterDetail extends OfferLetter {
  customer_name: string | null
  schedule: OfferInstallment[]
}

export interface OfferLetterList {
  items: OfferLetter[]
  total: number
  page: number
  page_size: number
}

export interface OfferLetterForm {
  customer_id: string
  expiry_date: string
  principal_amount: number
  interest_rate: number
  tenor_months: number
  currency: string
  repayment_type: 'monthly' | 'quarterly' | 'semi_annual' | 'annual' | 'bullet'
  grace_period_months?: number
  purpose_of_facility?: string
}

export interface DashboardStats {
  total_customers: number
  active_customers: number
  total_facilities: number
  active_facilities: number
  expiring_soon: number
  expiring_facilities: number
  expiring_soon_facilities: number
  monthly_revenue: number
  total_outstanding: number
  total_exposure: TotalExposure
  recent_customers: RecentCustomerStat[]
  recent_activities: RecentActivity[]
  // Richer analytics (optional so older API responses still type-check).
  facility_type_breakdown?: BreakdownItem[]
  facility_status_breakdown?: BreakdownItem[]
  risk_rating_breakdown?: BreakdownItem[]
  customer_type_breakdown?: BreakdownItem[]
  monthly_trend?: MonthlyTrendItem[]
  expiring_facilities_list?: ExpiringFacility[]
}

// API Response types
export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

// Form types
export interface LoginForm {
  username: string
  password: string
}

export interface CustomerForm {
  account_no: string
  name: string
  name_ar?: string
  account_type: 'retail' | 'corporate' | 'sme'
  status?: 'active' | 'inactive' | 'suspended'
  email?: string
  phone?: string
  mobile?: string
  address?: string
  branch?: string
  relationship_manager?: string
  notes?: string
}

export interface FacilityForm {
  customer_id: string
  facility_type: 'loan' | 'overdraft' | 'lc' | 'lg' | 'other'
  name?: string
  amount: number
  currency: string
  start_date?: string
  expiry_date?: string
  interest_rate?: number
  tenor_months?: string
  notes?: string
}

// Error types
export interface ApiError {
  detail: string
  status_code: number
  type?: string
}

// Filter types
export interface CustomerFilters {
  search?: string
  account_type?: string
  status?: string
  branch?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface FacilityFilters {
  customer_id?: string
  facility_type?: string
  status?: string
  search?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}