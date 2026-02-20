'use client'

import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { statsApi } from '@/lib/api'
import toast from 'react-hot-toast'

interface DashboardData {
  total_facilities_amount: number
  facilities_count: number
  customers_count: number
  active_customers: number
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
      setError('Failed to load dashboard data')
      toast.error('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadStats()
  }, [])

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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <p className="text-sm text-gray-500 mb-1">Total Customers</p>
            <p className="text-3xl font-bold text-gray-900">{stats.customers_count}</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-6">
            <p className="text-sm text-gray-500 mb-1">Active Customers</p>
            <p className="text-3xl font-bold text-green-600">{stats.active_customers}</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-6">
            <p className="text-sm text-gray-500 mb-1">Total Facilities</p>
            <p className="text-3xl font-bold text-gray-900">{stats.facilities_count}</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-6">
            <p className="text-sm text-gray-500 mb-1">Total Amount</p>
            <p className="text-3xl font-bold text-blue-600">{formatCurrency(stats.total_facilities_amount)}</p>
          </div>
        </div>
      ) : null}
    </Layout>
  )
}
