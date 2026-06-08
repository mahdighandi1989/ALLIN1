'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  AlertCircle,
  RefreshCw,
  Users,
  Building,
  Calendar,
  DollarSign,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { useRouter } from 'next/navigation'
import { statsApi, parseApiError } from '@/lib/api'
import type { DashboardStats } from '@/types'
import { DonutChart, BarChart, LineChart } from '@/components/charts'
import Layout from '@/components/Layout'

function riskColor(label: string): string {
  const l = (label || '').toLowerCase()
  if (l === 'high') return 'bg-red-100 text-red-700'
  if (l === 'medium') return 'bg-yellow-100 text-yellow-700'
  return 'bg-green-100 text-green-700'
}

function fmtMoney(n: number, currency = 'AED'): string {
  return `${currency} ${Number(n || 0).toLocaleString()}`
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  // True when the API could not be reached at all (e.g. a static export served
  // without its backend), as opposed to a normal HTTP error response.
  const [staticUnavailable, setStaticUnavailable] = useState(false)
  const [docAlerts, setDocAlerts] = useState<any>(null)
  const router = useRouter()

  const fetchDashboardData = useCallback(async () => {
    setLoading(true)
    setError(null)
    setStaticUnavailable(false)
    try {
      const data = await statsApi.dashboard()
      setStats(data)
      statsApi.expiringDocuments(90).then(setDocAlerts).catch(() => {})
    } catch (err: any) {
      // A network error (no response) while running as a static export means
      // there is no backend to talk to.
      if (err?.request && !err?.response) {
        setStaticUnavailable(true)
        setError('Dashboard data unavailable in static mode')
      } else {
        const message = parseApiError(err)
        setError(message)
        toast.error(message)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDashboardData()
  }, [fetchDashboardData])

  const handleRefresh = () => {
    fetchDashboardData()
  }

  const handleNavigation = (path: string) => {
    router.push(path)
  }

  if (loading) {
    return (
      <Layout>
      <div className="container mx-auto p-6" data-testid="dashboard-loading">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <Button variant="outline" disabled>
            <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
            Loading...
          </Button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
      </Layout>
    )
  }

  if (staticUnavailable) {
    return (
      <Layout>
      <div className="container mx-auto p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <Button onClick={handleRefresh} variant="outline">
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
        <Alert variant="destructive" data-testid="static-mode-message">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Dashboard data unavailable in static mode</AlertDescription>
        </Alert>
      </div>
      </Layout>
    )
  }

  if (error) {
    return (
      <Layout>
      <div className="container mx-auto p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <Button onClick={handleRefresh} variant="outline">
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
        <Alert
          variant="destructive"
          data-testid="error-message"
          data-test="error-message-dashboard"
        >
          <AlertCircle className="h-4 w-4" />
          <AlertDescription data-testid="dashboard-error-message">
            {error}
          </AlertDescription>
        </Alert>
        <div className="mt-4" data-testid="error-message-dashboard">
          <Button onClick={handleRefresh} data-testid="dashboard-try-again">
            Try Again
          </Button>
        </div>
      </div>
      </Layout>
    )
  }

  return (
    <Layout>
    <div className="container mx-auto p-6" data-testid="dashboard-content">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <Button onClick={handleRefresh} variant="outline" data-testid="dashboard-refresh">
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      <div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        data-testid="dashboard-stats"
      >
        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => handleNavigation('/customers')}
          onKeyDown={(e) => e.key === 'Enter' && handleNavigation('/customers')}
          tabIndex={0}
          role="button"
          aria-label="Navigate to Customers"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Customers</CardTitle>
            <Users className="h-4 w-4 text-gray-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_customers ?? 0}</div>
            <p className="text-xs text-gray-500">{stats?.active_customers ?? 0} active</p>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => handleNavigation('/facilities')}
          onKeyDown={(e) => e.key === 'Enter' && handleNavigation('/facilities')}
          tabIndex={0}
          role="button"
          aria-label="Navigate to Facilities"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Facilities</CardTitle>
            <Building className="h-4 w-4 text-gray-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_facilities ?? 0}</div>
            <p className="text-xs text-gray-500">{stats?.active_facilities ?? 0} active</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Expiring Soon</CardTitle>
            <Calendar className="h-4 w-4 text-gray-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.expiring_soon ?? 0}</div>
            <p className="text-xs text-gray-500">Next 30 days</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monthly Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-gray-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${(stats?.monthly_revenue ?? 0).toLocaleString()}
            </div>
            <p className="text-xs text-gray-500">
              {stats?.total_exposure?.currency ?? 'AED'} exposure: $
              {(stats?.total_exposure?.amount ?? 0).toLocaleString()}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Analytics charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8" data-testid="dashboard-charts">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Facilities by Type</CardTitle>
          </CardHeader>
          <CardContent>
            <DonutChart data={stats?.facility_type_breakdown ?? []} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Exposure by Risk</CardTitle>
          </CardHeader>
          <CardContent>
            <BarChart data={stats?.risk_rating_breakdown ?? []} valueKey="amount" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Customers by Type</CardTitle>
          </CardHeader>
          <CardContent>
            <DonutChart data={stats?.customer_type_breakdown ?? []} />
          </CardContent>
        </Card>
      </div>

      {/* Exposure trend + expiring watch-list */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Exposure Trend (6 months)</CardTitle>
          </CardHeader>
          <CardContent>
            <LineChart data={stats?.monthly_trend ?? []} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Expiring Facilities (next 30 days)</CardTitle>
          </CardHeader>
          <CardContent>
            {stats?.expiring_facilities_list && stats.expiring_facilities_list.length > 0 ? (
              <div className="overflow-x-auto" data-testid="expiring-facilities">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-500 border-b">
                      <th className="py-2 pr-2">Facility</th>
                      <th className="py-2 pr-2">Customer</th>
                      <th className="py-2 pr-2 text-right">Amount</th>
                      <th className="py-2 pl-2 text-right">Days</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {stats.expiring_facilities_list.map((f) => (
                      <tr
                        key={f.id}
                        className="hover:bg-gray-50 cursor-pointer"
                        onClick={() => handleNavigation('/facilities')}
                      >
                        <td className="py-2 pr-2 font-medium">{f.name || f.facility_type || f.id}</td>
                        <td className="py-2 pr-2 text-gray-600">{f.customer_name || '-'}</td>
                        <td className="py-2 pr-2 text-right tabular-nums">
                          {fmtMoney(f.amount, f.currency)}
                        </td>
                        <td className="py-2 pl-2 text-right">
                          <span
                            className={`px-2 py-0.5 rounded text-xs ${
                              (f.days_to_expiry ?? 99) <= 15
                                ? 'bg-red-100 text-red-700'
                                : 'bg-yellow-100 text-yellow-700'
                            }`}
                          >
                            {f.days_to_expiry ?? '-'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-500 py-6 text-center">No facilities expiring soon</p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent Activities</CardTitle>
          </CardHeader>
          <CardContent>
            {stats?.recent_activities && stats.recent_activities.length > 0 ? (
              <ul className="space-y-4" data-testid="recent-activities">
                {stats.recent_activities.map((activity) => (
                  <li key={activity.id} className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{activity.action}</p>
                      <p className="text-sm text-gray-500">by {activity.user}</p>
                    </div>
                    <span className="text-sm text-gray-500">
                      {activity.timestamp
                        ? new Date(activity.timestamp).toLocaleDateString()
                        : ''}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500">No recent activities</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Button
                className="w-full justify-start"
                variant="outline"
                onClick={() => handleNavigation('/customers')}
              >
                <Users className="mr-2 h-4 w-4" />
                Manage Customers
              </Button>
              <Button
                className="w-full justify-start"
                variant="outline"
                onClick={() => handleNavigation('/facilities')}
              >
                <Building className="mr-2 h-4 w-4" />
                Manage Facilities
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* KYC / Document expiry alerts (from merged customer profiles) */}
      {docAlerts && docAlerts.total > 0 && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              Document Expiry Alerts
              <span className="text-xs font-normal text-red-600">{docAlerts.expired} expired</span>
              <span className="text-xs font-normal text-amber-600">/ {docAlerts.total} within 90 days</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-auto" style={{ maxHeight: 320 }}>
              <table className="w-full text-sm whitespace-nowrap">
                <thead className="bg-gray-50 sticky top-0">
                  <tr className="text-left text-gray-500">
                    <th className="px-3 py-2">Customer</th>
                    <th className="px-3 py-2">Account</th>
                    <th className="px-3 py-2">Document</th>
                    <th className="px-3 py-2">Expiry</th>
                    <th className="px-3 py-2">Days</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {docAlerts.items.slice(0, 40).map((a: any, i: number) => (
                    <tr key={i} className={a.expired ? 'bg-red-50' : ''}>
                      <td className="px-3 py-1.5">{a.customer_name || '—'}</td>
                      <td className="px-3 py-1.5">{a.account_no}</td>
                      <td className="px-3 py-1.5">{a.document}</td>
                      <td className="px-3 py-1.5">{a.expiry_date}</td>
                      <td className={`px-3 py-1.5 font-medium ${a.expired ? 'text-red-600' : 'text-amber-600'}`}>
                        {a.expired ? `${Math.abs(a.days_left)}d ago` : `${a.days_left}d`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
    </Layout>
  )
}
