'use client'

import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { trashApi, parseApiError } from '@/lib/api'
import { TrashList, TrashItem } from '@/types'
import { Trash2, RotateCcw, Users, Building, FileText } from 'lucide-react'
import toast from 'react-hot-toast'

const TYPE_META: Record<string, { label: string; entity: string; Icon: any; color: string }> = {
  customer: { label: 'Customer', entity: 'customer', Icon: Users, color: 'text-blue-600' },
  facility: { label: 'Facility', entity: 'facility', Icon: Building, color: 'text-green-600' },
  offer_letter: { label: 'Offer Letter', entity: 'offer_letter', Icon: FileText, color: 'text-purple-600' },
}

export default function TrashPage() {
  const [data, setData] = useState<TrashList | null>(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    try {
      setLoading(true)
      setData(await trashApi.list())
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const restore = async (item: TrashItem) => {
    const meta = TYPE_META[item.type]
    try {
      await trashApi.restore(meta.entity, item.id)
      toast.success(`${meta.label} restored`)
      load()
    } catch (e) {
      toast.error(parseApiError(e))
    }
  }

  return (
    <Layout>
      <div className="flex items-center gap-2 mb-6">
        <Trash2 size={22} className="text-gray-500" />
        <h2 className="text-2xl font-bold">Recycle Bin</h2>
      </div>

      {!loading && data && (
        <div className="flex gap-3 mb-6 text-sm">
          <span className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full">
            {data.counts.customers} customers
          </span>
          <span className="px-3 py-1 bg-green-50 text-green-700 rounded-full">
            {data.counts.facilities} facilities
          </span>
          <span className="px-3 py-1 bg-purple-50 text-purple-700 rounded-full">
            {data.counts.offer_letters} offer letters
          </span>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm overflow-hidden" data-testid="trash-content">
        {loading ? (
          <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>
        ) : data && data.items.length > 0 ? (
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Item</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Type</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Detail</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {data.items.map((item) => {
                const meta = TYPE_META[item.type]
                const Icon = meta?.Icon || FileText
                return (
                  <tr key={`${item.type}-${item.id}`} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium">
                      <div className="flex items-center gap-2">
                        <Icon size={16} className={meta?.color || 'text-gray-400'} />
                        {item.label}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{meta?.label || item.type}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{item.sublabel || '-'}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        data-testid={`restore-${item.type}-${item.id}`}
                        onClick={() => restore(item)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 border rounded-lg text-sm hover:bg-gray-50"
                      >
                        <RotateCcw size={14} /> Restore
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        ) : (
          <div className="py-12 text-center text-gray-500">Recycle bin is empty</div>
        )}
      </div>
    </Layout>
  )
}
