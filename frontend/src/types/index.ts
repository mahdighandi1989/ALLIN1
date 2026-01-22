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
