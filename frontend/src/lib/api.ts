typescript
  dashboard: async () => {
    try {
      const res = await api.get('/api/stats/dashboard')
      return res.data
    } catch (error) {
      // بازگرداندن داده پیش‌فرض بدون لاگ خطا
      return {
        total_customers: 0,
        active_customers: 0,
        total_facilities: 0,
        expiring_soon_facilities: 0,
        total_exposure: { amount: 0, currency: 'AED' },
        recent_customers: [],
      }
    }
  },