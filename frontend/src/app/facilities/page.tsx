typescript
  const loadData = async () => {
    try {
      const [facilitiesData, customersData] = await Promise.all([
        facilitiesApi.list({ page, page_size: 20 }),
        customersApi.list({ page_size: 100 }),
      ])
      setData(facilitiesData)
      setCustomers(customersData.items)
    } catch (error) {
      toast.error('Failed to load data')
    } finally {
      setLoading(false)
    }
  }