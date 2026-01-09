/**
 * Dashboard Page - صفحه اصلی داشبورد
 * Uses real API data
 */
import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import Link from 'next/link'
import {
  Users,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Building,
  Wallet,
  ArrowRight
} from 'lucide-react'

import { useAuth } from '@/hooks/useAuth'
import Layout from '@/components/Layout'
import { customersApi, facilitiesApi, checklistsApi, personalApi } from '@/services/api'

interface DashboardStats {
  totalCustomers: number
  activeFacilities: number
  pendingTasks: number
  expiringDocs: number
  totalFacilityAmount: number
  customerChange: number
  facilityChange: number
}

interface Task {
  id: string
  title: string
  customer: string
  priority: string
  dueDate: string
  daysOverdue: number
}

interface ExpiringDoc {
  id: string
  title: string
  customer: string
  expiryDate: string
  daysLeft: number
}

export default function Dashboard() {
  const { user, isLoading, isAuthenticated } = useAuth()
  const router = useRouter()
  const [stats, setStats] = useState<DashboardStats>({
    totalCustomers: 0,
    activeFacilities: 0,
    pendingTasks: 0,
    expiringDocs: 0,
    totalFacilityAmount: 0,
    customerChange: 0,
    facilityChange: 0,
  })
  const [tasks, setTasks] = useState<Task[]>([])
  const [expiringDocs, setExpiringDocs] = useState<ExpiringDoc[]>([])
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
      const [customersRes, facilitiesRes, checklistsRes] = await Promise.all([
        customersApi.list().catch(() => ({ data: [] })),
        facilitiesApi.list().catch(() => ({ data: [] })),
        checklistsApi.getPendingTasks().catch(() => ({ data: [] })),
      ])

      const customers = customersRes.data?.items || customersRes.data || []
      const facilities = facilitiesRes.data?.items || facilitiesRes.data || []
      const pendingTasks = checklistsRes.data?.items || checklistsRes.data || []

      // Calculate stats
      const activeFacilities = facilities.filter((f: any) => f.status === 'active')
      const totalAmount = facilities.reduce((sum: number, f: any) => sum + (f.approved_amount || 0), 0)

      // Find expiring documents (within 30 days)
      const now = new Date()
      const thirtyDays = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000)

      const expiring = facilities
        .filter((f: any) => {
          const expiry = new Date(f.expiry_date)
          return f.status === 'active' && expiry <= thirtyDays && expiry >= now
        })
        .map((f: any) => ({
          id: f.id,
          title: `${f.facility_type} - ${f.facility_number || f.id}`,
          customer: f.customer_name || 'Unknown',
          expiryDate: f.expiry_date,
          daysLeft: Math.ceil((new Date(f.expiry_date).getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
        }))

      // Map tasks
      const mappedTasks = pendingTasks.slice(0, 5).map((t: any) => ({
        id: t.id,
        title: t.title,
        customer: t.customer_name || 'Unknown',
        priority: t.priority || 'medium',
        dueDate: t.due_date,
        daysOverdue: t.due_date ? Math.max(0, Math.ceil((now.getTime() - new Date(t.due_date).getTime()) / (1000 * 60 * 60 * 24))) : 0
      }))

      setStats({
        totalCustomers: customers.length,
        activeFacilities: activeFacilities.length,
        pendingTasks: pendingTasks.length,
        expiringDocs: expiring.length,
        totalFacilityAmount: totalAmount,
        customerChange: 0,
        facilityChange: 0,
      })

      setTasks(mappedTasks)
      setExpiringDocs(expiring.slice(0, 5))
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    } finally {
      setLoadingData(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  const priorityColors: Record<string, string> = {
    high: 'bg-red-100 text-red-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-green-100 text-green-800',
  }

  return (
    <Layout>
      <Head>
        <title>Dashboard | Banking Operations System</title>
      </Head>

      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-500">Welcome back, {user?.first_name || user?.username || 'User'}</p>
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
          <Link href="/customers" className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Customers</p>
                <p className="text-3xl font-bold mt-1">
                  {loadingData ? '...' : stats.totalCustomers.toLocaleString()}
                </p>
              </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </Link>

          <Link href="/facilities" className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Facilities</p>
                <p className="text-3xl font-bold mt-1">
                  {loadingData ? '...' : stats.activeFacilities.toLocaleString()}
                </p>
              </div>
              <div className="p-3 bg-green-100 rounded-lg">
                <Wallet className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </Link>

          <Link href="/checklists" className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Pending Tasks</p>
                <p className="text-3xl font-bold mt-1">
                  {loadingData ? '...' : stats.pendingTasks.toLocaleString()}
                </p>
              </div>
              <div className="p-3 bg-orange-100 rounded-lg">
                <Clock className="w-6 h-6 text-orange-600" />
              </div>
            </div>
          </Link>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Expiring (30d)</p>
                <p className="text-3xl font-bold mt-1">
                  {loadingData ? '...' : stats.expiringDocs.toLocaleString()}
                </p>
              </div>
              <div className="p-3 bg-red-100 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Pending Tasks */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow">
            <div className="p-4 border-b flex justify-between items-center">
              <h3 className="font-semibold">Pending Tasks</h3>
              <Link href="/checklists" className="text-blue-600 text-sm hover:underline flex items-center gap-1">
                View All <ArrowRight size={14} />
              </Link>
            </div>
            <div className="p-4">
              {loadingData ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                </div>
              ) : tasks.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <CheckCircle className="mx-auto mb-2 text-green-500" size={32} />
                  <p>No pending tasks</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {tasks.map((task) => (
                    <div key={task.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium">{task.title}</p>
                        <p className="text-sm text-gray-500">{task.customer}</p>
                      </div>
                      <div className="text-right">
                        <span className={`badge ${priorityColors[task.priority] || priorityColors.medium}`}>
                          {task.priority}
                        </span>
                        {task.daysOverdue > 0 && (
                          <p className="text-xs text-red-600 mt-1">{task.daysOverdue} days overdue</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Expiring Documents */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b flex items-center gap-2">
              <AlertTriangle className="text-orange-500" size={20} />
              <h3 className="font-semibold">Expiring Soon</h3>
            </div>
            <div className="p-4">
              {loadingData ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                </div>
              ) : expiringDocs.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <CheckCircle className="mx-auto mb-2 text-green-500" size={32} />
                  <p>No expiring documents</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {expiringDocs.map((doc) => (
                    <div key={doc.id} className="p-3 border-l-4 border-orange-400 bg-orange-50 rounded-r-lg">
                      <p className="font-medium text-orange-900">{doc.title}</p>
                      <p className="text-sm text-orange-700">{doc.customer}</p>
                      <p className="text-xs text-orange-600 mt-1">
                        Expires in {doc.daysLeft} days ({new Date(doc.expiryDate).toLocaleDateString()})
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Facility Summary */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold mb-4">Portfolio Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-600">Total Facility Amount</p>
              <p className="text-2xl font-bold text-blue-900">
                AED {loadingData ? '...' : (stats.totalFacilityAmount / 1000000).toFixed(1)}M
              </p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <p className="text-sm text-green-600">Active Facilities</p>
              <p className="text-2xl font-bold text-green-900">
                {loadingData ? '...' : stats.activeFacilities}
              </p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <p className="text-sm text-purple-600">Total Customers</p>
              <p className="text-2xl font-bold text-purple-900">
                {loadingData ? '...' : stats.totalCustomers}
              </p>
            </div>
            <div className="p-4 bg-orange-50 rounded-lg">
              <p className="text-sm text-orange-600">Pending Actions</p>
              <p className="text-2xl font-bold text-orange-900">
                {loadingData ? '...' : stats.pendingTasks + stats.expiringDocs}
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
