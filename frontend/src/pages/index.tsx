/**
 * Dashboard Page - صفحه اصلی داشبورد
 */
import { useEffect } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import {
  Users,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Building,
  Wallet
} from 'lucide-react'

import { useAuth } from '@/hooks/useAuth'
import Layout from '@/components/Layout'
import StatsCard from '@/components/dashboard/StatsCard'
import PendingTasksWidget from '@/components/dashboard/PendingTasksWidget'
import ExpiringDocsWidget from '@/components/dashboard/ExpiringDocsWidget'
import RecentActivityWidget from '@/components/dashboard/RecentActivityWidget'

export default function Dashboard() {
  const { user, isLoading, isAuthenticated } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isLoading, isAuthenticated, router])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner w-12 h-12"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <Layout>
      <Head>
        <title>Dashboard | Banking Operations System</title>
      </Head>

      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-500">Welcome back, {user?.first_name || user?.username}</p>
          </div>
          <div className="text-sm text-gray-500">
            {new Date().toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatsCard
            title="Total Customers"
            value="1,234"
            change="+12%"
            changeType="increase"
            icon={<Users className="w-6 h-6" />}
            color="blue"
          />
          <StatsCard
            title="Active Facilities"
            value="456"
            change="+8%"
            changeType="increase"
            icon={<Wallet className="w-6 h-6" />}
            color="green"
          />
          <StatsCard
            title="Pending Tasks"
            value="23"
            change="-5"
            changeType="decrease"
            icon={<Clock className="w-6 h-6" />}
            color="orange"
          />
          <StatsCard
            title="Expiring Documents"
            value="15"
            change="+3"
            changeType="warning"
            icon={<AlertTriangle className="w-6 h-6" />}
            color="red"
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Pending Tasks */}
          <div className="lg:col-span-2">
            <PendingTasksWidget />
          </div>

          {/* Expiring Documents */}
          <div>
            <ExpiringDocsWidget />
          </div>
        </div>

        {/* Bottom Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Activity */}
          <RecentActivityWidget />

          {/* Quick Stats */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Facility Summary</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Overdraft</span>
                <span className="font-semibold">AED 15.2M</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Term Loans</span>
                <span className="font-semibold">AED 42.8M</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Letter of Guarantee</span>
                <span className="font-semibold">AED 8.5M</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">LC Outstanding</span>
                <span className="font-semibold">AED 12.1M</span>
              </div>
              <div className="pt-4 border-t">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-gray-900">Total Outstanding</span>
                  <span className="font-bold text-blue-600">AED 78.6M</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
