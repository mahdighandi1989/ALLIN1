/**
 * Dashboard Page v2.0
 * صفحه اصلی داشبورد
 */
import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import Link from 'next/link'
import {
  Users,
  AlertTriangle,
  CheckCircle,
  Wallet,
  ArrowRight,
  TrendingUp,
  Calendar
} from 'lucide-react'

import { useAuth } from '@/hooks/useAuth'
import Layout from '@/components/Layout'
import { reportsApi } from '@/services/api'

interface DashboardData {
  customers: {
    total: number
    active: number
  }
  facilities: {
    total: number
    total_exposure: number
    expiring_soon: number
  }
  recent_customers: Array<{
    id: string
    name: string
    account_no: string
  }>
}

interface ExpiringFacility {
  id: string
  customer_id: string
  customer_name: string
  facility_type: string
  amount: number
  expiry_date: string
  days_until_expiry: number
}

export default function Dashboard() {
  const { user, isLoading, isAuthenticated } = useAuth()
  const router = useRouter()
  const [data, setData] = useState<DashboardData | null>(null)
  const [expiring, setExpiring] = useState<ExpiringFacility[]>([])
  const [loadingData, setLoadingData] = useState(true)

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isLoading, isAuthenticated, router])

  useEffect(() => {
    if (isAuthenticated) {
      fetchDashboardData()
    }
  }, [isAuthenticated])

  const fetchDashboardData = async () => {
    setLoadingData(true)
    try {
      const [dashboardRes, expiringRes] = await Promise.all([
        reportsApi.dashboard().catch(() => ({ data: null })),
        reportsApi.expiring(30).catch(() => ({ data: { items: [] } }))
      ])

      if (dashboardRes.data) {
        setData(dashboardRes.data)
      }
      if (expiringRes.data?.items) {
        setExpiring(expiringRes.data.items.slice(0, 5))
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    } finally {
      setLoadingData(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  const formatCurrency = (amount: number) => {
    if (amount >= 1000000) {
      return `${(amount / 1000000).toFixed(1)}M`
    }
    if (amount >= 1000) {
      return `${(amount / 1000).toFixed(0)}K`
    }
    return amount.toLocaleString()
  }

  return (
    <Layout>
      <Head>
        <title>Dashboard | Banking Operations System</title>
      </Head>

      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-500">Welcome back, {user?.first_name || user?.username || 'User'}</p>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-500 bg-white px-4 py-2 rounded-lg shadow-sm">
            <Calendar size={16} />
            {new Date().toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link href="/customers" className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-all border border-gray-100 group">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Total Customers</p>
                <p className="text-3xl font-bold mt-2 text-gray-900">
                  {loadingData ? '...' : data?.customers?.total?.toLocaleString() || 0}
                </p>
                <p className="text-sm text-green-600 mt-1 flex items-center gap-1">
                  <span className="font-medium">{data?.customers?.active || 0}</span> active
                </p>
              </div>
              <div className="p-4 bg-blue-50 rounded-xl group-hover:bg-blue-100 transition-colors">
                <Users className="w-7 h-7 text-blue-600" />
              </div>
            </div>
          </Link>

          <Link href="/facilities" className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-all border border-gray-100 group">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Total Facilities</p>
                <p className="text-3xl font-bold mt-2 text-gray-900">
                  {loadingData ? '...' : data?.facilities?.total?.toLocaleString() || 0}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  Active facilities
                </p>
              </div>
              <div className="p-4 bg-green-50 rounded-xl group-hover:bg-green-100 transition-colors">
                <Wallet className="w-7 h-7 text-green-600" />
              </div>
            </div>
          </Link>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Total Exposure</p>
                <p className="text-3xl font-bold mt-2 text-gray-900">
                  {loadingData ? '...' : formatCurrency(data?.facilities?.total_exposure || 0)}
                </p>
                <p className="text-sm text-gray-500 mt-1">AED</p>
              </div>
              <div className="p-4 bg-purple-50 rounded-xl">
                <TrendingUp className="w-7 h-7 text-purple-600" />
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Expiring (30d)</p>
                <p className="text-3xl font-bold mt-2 text-gray-900">
                  {loadingData ? '...' : data?.facilities?.expiring_soon?.toLocaleString() || 0}
                </p>
                <p className="text-sm text-orange-600 mt-1">Requires attention</p>
              </div>
              <div className="p-4 bg-orange-50 rounded-xl">
                <AlertTriangle className="w-7 h-7 text-orange-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Customers */}
          <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100">
            <div className="p-5 border-b flex justify-between items-center">
              <h3 className="font-semibold text-gray-900">Recent Customers</h3>
              <Link href="/customers" className="text-blue-600 text-sm hover:text-blue-700 flex items-center gap-1 font-medium">
                View All <ArrowRight size={14} />
              </Link>
            </div>
            <div className="p-5">
              {loadingData ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                </div>
              ) : !data?.recent_customers?.length ? (
                <div className="text-center py-8 text-gray-500">
                  <Users className="mx-auto mb-2 text-gray-300" size={40} />
                  <p>No customers yet</p>
                  <Link href="/customers" className="text-blue-600 text-sm mt-2 inline-block hover:underline">
                    Add your first customer
                  </Link>
                </div>
              ) : (
                <div className="space-y-3">
                  {data.recent_customers.map((customer) => (
                    <Link
                      key={customer.id}
                      href={`/customers/${customer.id}`}
                      className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 font-semibold">
                          {customer.name?.[0] || 'C'}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{customer.name}</p>
                          <p className="text-sm text-gray-500">{customer.account_no}</p>
                        </div>
                      </div>
                      <ArrowRight size={16} className="text-gray-400" />
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Expiring Facilities */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100">
            <div className="p-5 border-b flex items-center gap-2">
              <AlertTriangle className="text-orange-500" size={20} />
              <h3 className="font-semibold text-gray-900">Expiring Soon</h3>
            </div>
            <div className="p-5">
              {loadingData ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                </div>
              ) : expiring.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <CheckCircle className="mx-auto mb-2 text-green-400" size={40} />
                  <p className="font-medium text-gray-700">All clear!</p>
                  <p className="text-sm">No expiring facilities</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {expiring.map((facility) => (
                    <Link
                      key={facility.id}
                      href={`/facilities/${facility.id}`}
                      className="block p-4 border-l-4 border-orange-400 bg-orange-50 rounded-r-lg hover:bg-orange-100 transition-colors"
                    >
                      <p className="font-medium text-orange-900">{facility.facility_type}</p>
                      <p className="text-sm text-orange-700">{facility.customer_name}</p>
                      <div className="flex justify-between items-center mt-2">
                        <p className="text-xs text-orange-600">
                          {facility.days_until_expiry} days left
                        </p>
                        <p className="text-xs font-medium text-orange-800">
                          {formatCurrency(facility.amount)} AED
                        </p>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
