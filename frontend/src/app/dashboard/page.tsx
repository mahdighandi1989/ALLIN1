'use client'

import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { statsApi } from '@/lib/api'
import { DashboardStats } from '@/types'
import { Users, CreditCard, AlertTriangle, DollarSign, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await statsApi.dashboard()
      setStats(data)
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to load dashboard data'
      setError(errorMessage)
      toast.error(errorMessage)
      console.error('Dashboard stats error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRetry = () => {
    loadStats()
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'AED',
      minimumFractionDigits: 0,
    }).format(amount)
  }

  return (
    <Layout>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Dashboard</h2>
        <button
          onClick={handleRetry}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          title="Refresh dashboard data"
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-500">Loading dashboard data...</p>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <AlertTriangle className="mx-auto text-red-500 mb-4" size={48} />
          <h3 className="text-lg font-semibold text-red-800 mb-2">Unable to Load Dashboard</h3>
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={handleRetry}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      ) : stats ? (
        <div className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Users className="text-blue-600" size={24} />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total Customers</p>
                  <p className="text-2xl font-bold">{stats.customers.total.toLocaleString()}</p>
                  <p className="text-xs text-green-600">
                    {stats.customers.active} active
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-green-100 rounded-lg">
                  <CreditCard className="text-green-600" size={24} />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total Facilities</p>
                  <p className="text-2xl font-bold">{stats.facilities.total.toLocaleString()}</p>
                  <p className="text-xs text-gray-600">
                    {stats.facilities.expiring_soon} expiring soon
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-purple-100 rounded-lg">
                  <DollarSign className="text-purple-600" size={24} />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total Exposure</p>
                  <p className="text-2xl font-bold">{formatCurrency(stats.facilities.total_amount)}</p>
                  <p className="text-xs text-gray-600">
                    Outstanding: {formatCurrency(stats.facilities.outstanding)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-lg ${
                  stats.facilities.expiring_soon > 0 ? 'bg-yellow-100' : 'bg-gray-100'
                }`}>
                  <AlertTriangle className={`${
                    stats.facilities.expiring_soon > 0 ? 'text-yellow-600' : 'text-gray-600'
                  }`} size={24} />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Expiring Soon</p>
                  <p className={`text-2xl font-bold ${
                    stats.facilities.expiring_soon > 0 ? 'text-yellow-600' : 'text-gray-600'
                  }`}>
                    {stats.facilities.expiring_soon}
                  </p>
                  <p className="text-xs text-gray-600">Next 30 days</p>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Customers */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold">Recent Customers</h3>
            </div>
            <div className="p-6">
              {stats.recent_customers && stats.recent_customers.length > 0 ? (
                <div className="space-y-3">
                  {stats.recent_customers.map((customer) => (
                    <div key={customer.id} className="flex justify-between items-center py-2 hover:bg-gray-50 rounded px-2">
                      <div>
                        <span className="font-medium text-gray-900">{customer.name}</span>
                        <span className="text-sm text-gray-500 ml-2">({customer.account_no})</span>
                      </div>
                      <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                        View
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Users className="mx-auto text-gray-400 mb-3" size={48} />
                  <p className="text-gray-500">No recent customers</p>
                  <p className="text-sm text-gray-400">New customers will appear here</p>
                </div>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left">
                <Users className="text-blue-600 mb-2" size={24} />
                <h4 className="font-medium">Add Customer</h4>
                <p className="text-sm text-gray-500">Create new customer record</p>
              </button>
              <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left">
                <CreditCard className="text-green-600 mb-2" size={24} />
                <h4 className="font-medium">New Facility</h4>
                <p className="text-sm text-gray-500">Add facility for customer</p>
              </button>
              <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left">
                <AlertTriangle className="text-yellow-600 mb-2" size={24} />
                <h4 className="font-medium">Review Expiring</h4>
                <p className="text-sm text-gray-500">Check facilities expiring soon</p>
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
          <AlertTriangle className="mx-auto text-gray-400 mb-4" size={48} />
          <h3 className="text-lg font-semibold text-gray-700 mb-2">No Data Available</h3>
          <p className="text-gray-500 mb-4">Unable to load dashboard statistics</p>
          <button
            onClick={handleRetry}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Reload Data
          </button>
        </div>
      )}
    </Layout>
  )
}