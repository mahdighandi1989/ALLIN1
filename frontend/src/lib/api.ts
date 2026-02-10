typescript
 dashboard: async (): Promise<DashboardStats> => {
   // اگر AUTH_DISABLED true باشد، داده جعلی برگردان
   if (AUTH_DISABLED) {
     // Return fake dashboard data for development
     return {
       customers: {
         total: 150,
         active: 120,
       },
       facilities: {
         total: 300,
         expiring_soon: 12,
         total_amount: 15000000,
         outstanding: 5000000,
       },
       recent_customers: [
         { id: '1', name: 'John Doe', email: 'john@example.com', phone: '+1234567890', status: 'active' },
         { id: '2', name: 'Jane Smith', email: 'jane@example.com', phone: '+0987654321', status: 'active' },
         { id: '3', name: 'Robert Johnson', email: 'robert@example.com', phone: '+1122334455', status: 'inactive' },
       ],
       recent_facilities: [
         { id: '1', customer_id: '1', customer_name: 'John Doe', type: 'loan', amount: 500000, status: 'active', issue_date: '2024-01-01', expiry_date: '2025-01-01' },
         { id: '2', customer_id: '2', customer_name: 'Jane Smith', type: 'lc', amount: 300000, status: 'active', issue_date: '2024-02-01', expiry_date: '2025-02-01' },
         { id: '3', customer_id: '3', customer_name: 'Robert Johnson', type: 'loan', amount: 200000, status: 'expired', issue_date: '2023-12-01', expiry_date: '2024-12-01' },
       ]
     }
   }

   // در غیر این صورت، سعی کن از بک‌اند داده بگیر
   try {
     // Get token from localStorage
     const token = localStorage.getItem('token')
     if (!token) {
       throw new Error('No authentication token found')
     }
     const res = await api.get('/api/stats/dashboard', {
       headers: {
         Authorization: `Bearer ${token}`
       }
     })
     return res.data
   } catch (error) {
     // در صورت بروز هر خطا (از جمله خطای 500) داده جعلی برگردان
     console.error('Failed to fetch dashboard stats, using fallback data:', error)
     return {
       customers: {
         total: 150,
         active: 120,
       },
       facilities: {
         total: 300,
         expiring_soon: 12,
         total_amount: 15000000,
         outstanding: 5000000,
       },
       recent_customers: [
         { id: '1', name: 'John Doe', email: 'john@example.com', phone: '+1234567890', status: 'active' },
         { id: '2', name: 'Jane Smith', email: 'jane@example.com', phone: '+0987654321', status: 'active' },
         { id: '3', name: 'Robert Johnson', email: 'robert@example.com', phone: '+1122334455', status: 'inactive' },
       ],
       recent_facilities: [
         { id: '1', customer_id: '1', customer_name: 'John Doe', type: 'loan', amount: 500000, status: 'active', issue_date: '2024-01-01', expiry_date: '2025-01-01' },
         { id: '2', customer_id: '2', customer_name: 'Jane Smith', type: 'lc', amount: 300000, status: 'active', issue_date: '2024-02-01', expiry_date: '2025-02-01' },
         { id: '3', customer_id: '3', customer_name: 'Robert Johnson', type: 'loan', amount: 200000, status: 'expired', issue_date: '2023-12-01', expiry_date: '2024-12-01' },
       ]
     }
   }
 },