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

// Dashboard types
export interface DashboardStats {
  customers: {
    total: number
    active: number
  }
  facilities: {
    total: number
    total_amount: number
    outstanding: number
    expiring_soon: number
  }
  recent_customers: {
    id: string
    name: string
    account_no: string
  }[]
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