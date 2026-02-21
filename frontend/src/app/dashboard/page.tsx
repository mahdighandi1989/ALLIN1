import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, RefreshCw, Users, Building, Calendar, DollarSign } from 'lucide-react';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';

interface DashboardStats {
  total_customers: number;
  total_facilities: number;
  active_facilities: number;
  expiring_soon: number;
  monthly_revenue: number;
  recent_activities: Array<{
    id: number;
    action: string;
    timestamp: string;
    user: string;
  }>;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/stats/dashboard');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setStats(data);
    } catch (err: any) {
      let errorMessage = 'Failed to load dashboard data';
      if (err?.response) {
        // سرور پاسخ داده اما با وضعیت خطا
        if (err.response.status === 500) {
          errorMessage = 'Server error. Please try again later.';
        } else {
          errorMessage = err.response.data?.detail || err.response.data?.message || errorMessage;
        }
      } else if (err?.request) {
        // درخواست فرستاده شده اما پاسخی دریافت نشده
        errorMessage = 'No response from server. Please check your network connection.';
      } else {
        // مشکلی در تنظیم درخواست رخ داده است
        errorMessage = err?.message || errorMessage;
      }
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleRefresh = () => {
    fetchDashboardData();
  };

  const handleNavigation = (path: string) => {
    router.push(path);
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
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
    );
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
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <div className="mt-4">
          <Button onClick={handleRefresh}>Try Again</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <Button onClick={handleRefresh} variant="outline">
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
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
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_customers || 0}</div>
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
            <Building className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_facilities || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.active_facilities || 0} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Expiring Soon</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.expiring_soon || 0}</div>
            <p className="text-xs text-muted-foreground">Next 30 days</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monthly Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${(stats?.monthly_revenue || 0).toLocaleString()}
            </div>
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
              <ul className="space-y-4">
                {stats.recent_activities.map((activity) => (
                  <li key={activity.id} className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{activity.action}</p>
                      <p className="text-sm text-muted-foreground">by {activity.user}</p>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {new Date(activity.timestamp).toLocaleDateString()}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-muted-foreground">No recent activities</p>
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
                onClick={() => handleNavigation('/customers/new')}
              >
                <Users className="mr-2 h-4 w-4" />
                Add New Customer
              </Button>
              <Button 
                className="w-full justify-start" 
                variant="outline"
                onClick={() => handleNavigation('/facilities/new')}
              >
                <Building className="mr-2 h-4 w-4" />
                Add New Facility
              </Button>
              <Button 
                className="w-full justify-start" 
                variant="outline"
                onClick={() => handleNavigation('/reports')}
              >
                <DollarSign className="mr-2 h-4 w-4" />
                View Financial Reports
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}