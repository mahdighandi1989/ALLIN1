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

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  // True when the API could not be reached at all (e.g. a static export served
  // without its backend), as opposed to a normal HTTP error response.
  const [staticUnavailable, setStaticUnavailable] = useState(false)
  const router = useRouter()

  const fetchDashboardData = useCallback(async () => {
    setLoading(true)
    setError(null)
    setStaticUnavailable(false)
    try {
      const data = await statsApi.dashboard()
      setStats(data)
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
    )
  }

  if (staticUnavailable) {
    return (
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
    )
  }

  if (error) {
    return (
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
    )
  }

  return (
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
    </div>
  )
}
