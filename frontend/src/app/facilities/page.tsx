typescript
import React, { useState, useEffect, useCallback } from 'react'
import { facilitiesApi, customersApi } from '@/lib/api'
import { toast } from 'react-hot-toast'
import FacilitiesTable from './FacilitiesTable'
import Pagination from '@/components/Pagination'
import LoadingSpinner from '@/components/LoadingSpinner'

const FacilitiesPage: React.FC = () => {
  const [data, setData] = useState<any>(null)
  const [customers, setCustomers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)

  const loadData = async () => {
    try {
      const [facilitiesResult, customersResult] = await Promise.allSettled([
        facilitiesApi.list({ page, page_size: 20 }),
        customersApi.list({ page_size: 100 }),
      ])

      if (facilitiesResult.status === 'fulfilled') {
        setData(facilitiesResult.value)
      } else {
        toast.error('Failed to load facilities data')
        console.error('Facilities load error:', facilitiesResult.reason)
      }

      if (customersResult.status === 'fulfilled') {
        setCustomers(customersResult.value.items || [])
      } else {
        toast.error('Failed to load customers data')
        console.error('Customers load error:', customersResult.reason)
      }
    } catch (error) {
      toast.error('An unexpected error occurred while loading data')
      console.error('Unexpected error:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [page])

  const handlePageChange = useCallback((newPage: number) => {
    setPage(newPage)
  }, [])

  if (loading) {
    return <LoadingSpinner />
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Facilities</h1>
        <p className="text-gray-600 mt-2">Manage your facilities</p>
      </div>

      {data && (
        <>
          <FacilitiesTable
            facilities={data.items || []}
            customers={customers}
            onRefresh={loadData}
          />
          <Pagination
            currentPage={page}
            totalPages={data.total_pages || 1}
            onPageChange={handlePageChange}
          />
        </>
      )}

      {!data && (
        <div className="text-center py-8">
          <p className="text-gray-500">No facilities data available</p>
          <button
            onClick={loadData}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry Loading Data
          </button>
        </div>
      )}
    </div>
  )
}

export default FacilitiesPage