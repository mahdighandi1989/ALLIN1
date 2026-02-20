'use client'

import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { statsApi } from '@/lib/api'
import toast from 'react-hot-toast'

interface RecentCustomer {
  id: string
  account_no: string | null
  name: string | null
  status: string | null
  created_at: string | null
}

interface DashboardData {
  total_customers: number
  active_customers: number
  total_facilities: number
  expiring_soon_facilities: number
  total_exposure: { amount: number; currency: string }
  recent_customers: RecentCustomer[]
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadStats = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await statsApi.dashboard()
      setStats(data)
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to load dashboard data'
      setError(errorMessage)
      toast.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadStats()
  }, [])

  const formatCurrency = (amount: number, currency: string = 'AED') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      minimumFractionDigits: 0,
    }).format(amount)
  }

  return (
    <Layout>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Dashboard</h2>
        <button
          onClick={loadStats}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={loadStats}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      ) : stats ? (
        <div className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <p className="text-sm text-gray-500 mb-1">Total Customers</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_customers}</p>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-6">
              <p className="text-sm text-gray-500 mb-1">Active Customers</p>
              <p className="text-3xl font-bold text-green-600">{stats.active_customers}</p>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-6">
              <p className="text-sm text-gray-500 mb-1">Total Facilities</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_facilities}</p>
              {stats.expiring_soon_facilities > 0 && (
                <p className="text-xs text-orange-500 mt-1">
                  {stats.expiring_soon_facilities} expiring soon
                </p>
              )}
            </div>
            <div className="bg-white rounded-lg shadow-sm p-6">
              <p className="text-sm text-gray-500 mb-1">Total Exposure</p>
              <p className="text-3xl font-bold text-blue-600">
                {formatCurrency(stats.total_exposure.amount, stats.total_exposure.currency)}
              </p>
            </div>
          </div>

          {/* Recent Customers */}
          {stats.recent_customers.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold mb-4">Recent Customers</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-500 border-b">
                      <th className="pb-2 pr-4">Name</th>
                      <th className="pb-2 pr-4">Account No</th>
                      <th className="pb-2 pr-4">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.recent_customers.map((c) => (
                      <tr key={c.id} className="border-b last:border-0">
                        <td className="py-2 pr-4 font-medium">{c.name || 'Unknown'}</td>
                        <td className="py-2 pr-4 text-gray-600">{c.account_no || '-'}</td>
                        <td className="py-2 pr-4">
                          <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                            c.status === 'active' ? 'bg-green-100 text-green-700' :
                            c.status === 'inactive' ? 'bg-gray-100 text-gray-700' :
                            'bg-yellow-100 text-yellow-700'
                          }`}>
                            {c.status || 'unknown'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      ) : null}
    </Layout>
  )
}