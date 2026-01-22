'use client'

import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { statsApi } from '@/lib/api'
import { DashboardStats } from '@/types'
import { Users, CreditCard, AlertTriangle, DollarSign } from 'lucide-react'
import toast from 'react-hot-toast'

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const data = await statsApi.dashboard()
      setStats(data)
    } catch (error) {
      toast.error('Failed to load dashboard')
    } finally {
      setLoading(false)
    }
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
      <h2 className="text-2xl font-bold mb-6">Dashboard</h2>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : stats ? (
        <div className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Users className="text-blue-600" size={24} />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total Customers</p>
                  <p className="text-2xl font-bold">{stats.customers.total}</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-green-100 rounded-lg">
                  <CreditCard className="text-green-600" size={24} />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total Facilities</p>
                  <p className="text-2xl font-bold">{stats.facilities.total}</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-purple-100 rounded-lg">
                  <DollarSign className="text-purple-600" size={24} />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total Exposure</p>
                  <p className="text-2xl font-bold">{formatCurrency(stats.facilities.total_amount)}</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-yellow-100 rounded-lg">
                  <AlertTriangle className="text-yellow-600" size={24} />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Expiring Soon</p>
                  <p className="text-2xl font-bold">{stats.facilities.expiring_soon}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Customers */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Customers</h3>
            {stats.recent_customers.length > 0 ? (
              <div className="divide-y">
                {stats.recent_customers.map((customer) => (
                  <div key={customer.id} className="py-3 flex justify-between">
                    <span className="font-medium">{customer.name}</span>
                    <span className="text-gray-500">{customer.account_no}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No customers yet</p>
            )}
          </div>
        </div>
      ) : (
        <p className="text-center text-gray-500">Failed to load data</p>
      )}
    </Layout>
  )
}
