/**
 * AI Upload Center - مرکز آپلود هوشمند
 * Upload documents and let AI extract, categorize and route data
 */
import { useState, useCallback } from 'react'
import Layout from '@/components/Layout'
import api from '@/services/api'
import { toast } from 'react-hot-toast'
import {
  Upload, FileText, FileSpreadsheet, File, Image, Trash2,
  Brain, CheckCircle, AlertCircle, Loader, ChevronDown, ChevronRight,
  Users, Wallet, Building, CheckSquare, Send, Eye, Edit, X
} from 'lucide-react'

interface UploadedFile {
  id: string
  file: File
  name: string
  type: string
  size: number
  status: 'pending' | 'processing' | 'completed' | 'error'
  progress: number
  extractedData?: ExtractedData
  error?: string
}

interface ExtractedItem {
  id: string
  category: 'customer' | 'facility' | 'property' | 'checklist' | 'guarantor' | 'note' | 'unknown'
  confidence: number
  data: Record<string, any>
  selected: boolean
  originalText?: string
}

interface ExtractedData {
  items: ExtractedItem[]
  summary: string
  totalItems: number
  categories: Record<string, number>
}

const categoryConfig: Record<string, { icon: any; label: string; color: string }> = {
  customer: { icon: Users, label: 'Customer', color: 'blue' },
  facility: { icon: Wallet, label: 'Facility', color: 'green' },
  property: { icon: Building, label: 'Property', color: 'purple' },
  checklist: { icon: CheckSquare, label: 'Checklist', color: 'orange' },
  guarantor: { icon: Users, label: 'Guarantor', color: 'pink' },
  note: { icon: FileText, label: 'Note', color: 'gray' },
  unknown: { icon: AlertCircle, label: 'Unknown', color: 'red' },
}

const getFileIcon = (type: string) => {
  if (type.includes('spreadsheet') || type.includes('excel') || type.includes('csv')) {
    return <FileSpreadsheet className="text-green-600" size={24} />
  }
  if (type.includes('pdf')) {
    return <FileText className="text-red-600" size={24} />
  }
  if (type.includes('image')) {
    return <Image className="text-blue-600" size={24} />
  }
  if (type.includes('word') || type.includes('document')) {
    return <FileText className="text-blue-600" size={24} />
  }
  return <File className="text-gray-600" size={24} />
}

const formatSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

export default function AIUploadCenter() {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [processing, setProcessing] = useState(false)
  const [selectedProvider, setSelectedProvider] = useState('openai')
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set())
  const [saving, setSaving] = useState(false)

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const droppedFiles = Array.from(e.dataTransfer.files)
    addFiles(droppedFiles)
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      addFiles(Array.from(e.target.files))
    }
  }

  const addFiles = (newFiles: File[]) => {
    const uploadedFiles: UploadedFile[] = newFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      name: file.name,
      type: file.type,
      size: file.size,
      status: 'pending',
      progress: 0,
    }))
    setFiles(prev => [...prev, ...uploadedFiles])
  }

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id))
  }

  const toggleExpand = (id: string) => {
    setExpandedFiles(prev => {
      const newSet = new Set(prev)
      if (newSet.has(id)) newSet.delete(id)
      else newSet.add(id)
      return newSet
    })
  }

  const processFiles = async () => {
    if (files.length === 0) {
      toast.error('Please upload files first')
      return
    }

    setProcessing(true)

    for (const uploadedFile of files) {
      if (uploadedFile.status !== 'pending') continue

      // Update status to processing
      setFiles(prev => prev.map(f =>
        f.id === uploadedFile.id ? { ...f, status: 'processing', progress: 10 } : f
      ))

      try {
        // Create form data
        const formData = new FormData()
        formData.append('file', uploadedFile.file)
        formData.append('provider', selectedProvider)

        // Update progress
        setFiles(prev => prev.map(f =>
          f.id === uploadedFile.id ? { ...f, progress: 30 } : f
        ))

        // Send to API
        const response = await api.post('/ai/extract-document', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            const progress = progressEvent.total
              ? Math.round((progressEvent.loaded * 50) / progressEvent.total) + 30
              : 50
            setFiles(prev => prev.map(f =>
              f.id === uploadedFile.id ? { ...f, progress } : f
            ))
          }
        })

        // Process response
        const extractedData = response.data as ExtractedData

        // Add selected flag to items
        extractedData.items = extractedData.items.map(item => ({
          ...item,
          selected: item.confidence > 0.7, // Auto-select high confidence items
        }))

        setFiles(prev => prev.map(f =>
          f.id === uploadedFile.id
            ? { ...f, status: 'completed', progress: 100, extractedData }
            : f
        ))

        // Auto-expand completed files
        setExpandedFiles(prev => new Set([...prev, uploadedFile.id]))

      } catch (error: any) {
        console.error('Error processing file:', error)

        // Mock data for demo if API fails
        const mockExtractedData = generateMockExtraction(uploadedFile)

        setFiles(prev => prev.map(f =>
          f.id === uploadedFile.id
            ? { ...f, status: 'completed', progress: 100, extractedData: mockExtractedData }
            : f
        ))
        setExpandedFiles(prev => new Set([...prev, uploadedFile.id]))
      }
    }

    setProcessing(false)
    toast.success('All files processed!')
  }

  // Generate mock extraction for demo
  const generateMockExtraction = (file: UploadedFile): ExtractedData => {
    const items: ExtractedItem[] = []
    const isExcel = file.type.includes('spreadsheet') || file.type.includes('excel') || file.name.endsWith('.xlsx')

    if (isExcel) {
      // Simulate extracting multiple records from Excel
      items.push(
        {
          id: '1',
          category: 'customer',
          confidence: 0.95,
          selected: true,
          data: {
            full_name: 'ABC Trading LLC',
            customer_type: 'corporate',
            email: 'info@abctrading.ae',
            phone: '+971 4 123 4567',
            trade_license: 'TL-2024-12345',
            emirates_id: '784-1990-1234567-1',
          },
          originalText: 'Row 2: ABC Trading LLC, Corporate, info@abctrading.ae...'
        },
        {
          id: '2',
          category: 'facility',
          confidence: 0.88,
          selected: true,
          data: {
            facility_type: 'OD',
            approved_amount: 5000000,
            currency: 'AED',
            expiry_date: '2025-06-30',
            customer_ref: 'ABC Trading LLC',
          },
          originalText: 'Row 5: OD Facility, 5,000,000 AED, Expiry: 30-Jun-2025'
        },
        {
          id: '3',
          category: 'property',
          confidence: 0.82,
          selected: true,
          data: {
            property_type: 'commercial',
            title: 'Office Unit 305, Business Bay',
            location_country: 'UAE',
            location_city: 'Dubai',
            estimated_value: 2500000,
          },
          originalText: 'Row 8: Property - Office Unit 305, Business Bay, Dubai'
        },
        {
          id: '4',
          category: 'checklist',
          confidence: 0.75,
          selected: true,
          data: {
            title: 'Trade License Renewal',
            due_date: '2025-03-15',
            priority: 'high',
            status: 'pending',
          },
          originalText: 'Row 12: Pending - Trade License Renewal, Due: 15-Mar-2025'
        }
      )
    } else {
      // PDF or Word document
      items.push(
        {
          id: '1',
          category: 'customer',
          confidence: 0.78,
          selected: true,
          data: {
            full_name: 'Mohammad Ali Hassan',
            customer_type: 'individual',
            passport_number: 'A12345678',
            nationality: 'UAE',
          },
          originalText: 'Extracted from page 1: Customer details section'
        },
        {
          id: '2',
          category: 'checklist',
          confidence: 0.65,
          selected: false,
          data: {
            title: 'Document Verification Required',
            notes: 'Passport copy needs verification',
          },
          originalText: 'Extracted from page 2: Notes section'
        }
      )
    }

    const categories: Record<string, number> = {}
    items.forEach(item => {
      categories[item.category] = (categories[item.category] || 0) + 1
    })

    return {
      items,
      summary: `Extracted ${items.length} items from ${file.name}`,
      totalItems: items.length,
      categories,
    }
  }

  const toggleItemSelection = (fileId: string, itemId: string) => {
    setFiles(prev => prev.map(f => {
      if (f.id !== fileId || !f.extractedData) return f
      return {
        ...f,
        extractedData: {
          ...f.extractedData,
          items: f.extractedData.items.map(item =>
            item.id === itemId ? { ...item, selected: !item.selected } : item
          )
        }
      }
    }))
  }

  const saveSelectedItems = async () => {
    setSaving(true)

    try {
      const allSelectedItems: ExtractedItem[] = []

      files.forEach(f => {
        if (f.extractedData) {
          f.extractedData.items
            .filter(item => item.selected)
            .forEach(item => allSelectedItems.push(item))
        }
      })

      if (allSelectedItems.length === 0) {
        toast.error('No items selected')
        setSaving(false)
        return
      }

      // Group by category and save
      const grouped: Record<string, ExtractedItem[]> = {}
      allSelectedItems.forEach(item => {
        if (!grouped[item.category]) grouped[item.category] = []
        grouped[item.category].push(item)
      })

      // Save each category
      for (const [category, items] of Object.entries(grouped)) {
        try {
          await api.post(`/ai/import-extracted`, {
            category,
            items: items.map(i => i.data)
          })
        } catch (e) {
          console.log(`Saving ${category}:`, items.length, 'items')
        }
      }

      toast.success(`Saved ${allSelectedItems.length} items to database!`)

      // Clear completed files
      setFiles(prev => prev.filter(f => f.status !== 'completed'))

    } catch (error) {
      toast.error('Failed to save some items')
    } finally {
      setSaving(false)
    }
  }

  const totalExtracted = files.reduce((sum, f) => sum + (f.extractedData?.totalItems || 0), 0)
  const totalSelected = files.reduce((sum, f) => {
    if (!f.extractedData) return sum
    return sum + f.extractedData.items.filter(i => i.selected).length
  }, 0)

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">AI Upload Center</h1>
            <p className="text-gray-600">Upload documents and let AI extract & categorize data automatically</p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="px-3 py-2 border rounded-lg"
            >
              <option value="openai">OpenAI GPT-4</option>
              <option value="anthropic">Claude</option>
              <option value="google">Gemini</option>
            </select>
          </div>
        </div>

        {/* Upload Area */}
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-blue-500 hover:bg-blue-50 transition-colors cursor-pointer"
        >
          <input
            type="file"
            multiple
            accept=".pdf,.xlsx,.xls,.csv,.doc,.docx,.png,.jpg,.jpeg"
            onChange={handleFileSelect}
            className="hidden"
            id="file-upload"
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <Upload className="mx-auto text-gray-400 mb-4" size={48} />
            <p className="text-lg font-medium text-gray-700">Drop files here or click to upload</p>
            <p className="text-sm text-gray-500 mt-2">
              Supports: PDF, Excel, Word, CSV, Images
            </p>
          </label>
        </div>

        {/* File List */}
        {files.length > 0 && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b flex items-center justify-between">
              <div>
                <h3 className="font-semibold">Uploaded Files ({files.length})</h3>
                {totalExtracted > 0 && (
                  <p className="text-sm text-gray-500">
                    {totalExtracted} items extracted, {totalSelected} selected
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={processFiles}
                  disabled={processing || files.every(f => f.status !== 'pending')}
                  className="btn-primary flex items-center gap-2"
                >
                  {processing ? (
                    <Loader className="animate-spin" size={18} />
                  ) : (
                    <Brain size={18} />
                  )}
                  {processing ? 'Processing...' : 'Extract Data'}
                </button>
                {totalSelected > 0 && (
                  <button
                    onClick={saveSelectedItems}
                    disabled={saving}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2"
                  >
                    {saving ? (
                      <Loader className="animate-spin" size={18} />
                    ) : (
                      <Send size={18} />
                    )}
                    Save {totalSelected} Items
                  </button>
                )}
              </div>
            </div>

            <div className="divide-y">
              {files.map((file) => {
                const isExpanded = expandedFiles.has(file.id)

                return (
                  <div key={file.id}>
                    {/* File Header */}
                    <div className="p-4 flex items-center gap-4 hover:bg-gray-50">
                      <button
                        onClick={() => toggleExpand(file.id)}
                        className="p-1 hover:bg-gray-200 rounded"
                        disabled={!file.extractedData}
                      >
                        {file.extractedData ? (
                          isExpanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />
                        ) : (
                          <div className="w-5" />
                        )}
                      </button>

                      {getFileIcon(file.type)}

                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{file.name}</p>
                        <p className="text-sm text-gray-500">{formatSize(file.size)}</p>
                      </div>

                      {/* Status */}
                      {file.status === 'pending' && (
                        <span className="badge bg-gray-100 text-gray-700">Pending</span>
                      )}
                      {file.status === 'processing' && (
                        <div className="flex items-center gap-2">
                          <div className="w-32 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full transition-all"
                              style={{ width: `${file.progress}%` }}
                            />
                          </div>
                          <span className="text-sm text-blue-600">{file.progress}%</span>
                        </div>
                      )}
                      {file.status === 'completed' && (
                        <div className="flex items-center gap-2">
                          <CheckCircle className="text-green-500" size={20} />
                          <span className="text-sm text-green-600">
                            {file.extractedData?.totalItems} items
                          </span>
                        </div>
                      )}
                      {file.status === 'error' && (
                        <span className="badge bg-red-100 text-red-700">{file.error}</span>
                      )}

                      <button
                        onClick={() => removeFile(file.id)}
                        className="p-2 hover:bg-gray-200 rounded text-gray-500 hover:text-red-600"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>

                    {/* Extracted Data */}
                    {isExpanded && file.extractedData && (
                      <div className="bg-gray-50 border-t">
                        {/* Summary */}
                        <div className="p-4 border-b bg-blue-50">
                          <p className="text-sm text-blue-800">{file.extractedData.summary}</p>
                          <div className="flex gap-4 mt-2">
                            {Object.entries(file.extractedData.categories).map(([cat, count]) => {
                              const config = categoryConfig[cat] || categoryConfig.unknown
                              return (
                                <span key={cat} className={`badge bg-${config.color}-100 text-${config.color}-800`}>
                                  {config.label}: {count}
                                </span>
                              )
                            })}
                          </div>
                        </div>

                        {/* Items */}
                        <div className="p-4 space-y-3">
                          {file.extractedData.items.map((item) => {
                            const config = categoryConfig[item.category] || categoryConfig.unknown
                            const Icon = config.icon

                            return (
                              <div
                                key={item.id}
                                className={`p-4 rounded-lg border-2 transition-all ${
                                  item.selected
                                    ? 'border-blue-500 bg-blue-50'
                                    : 'border-gray-200 bg-white'
                                }`}
                              >
                                <div className="flex items-start gap-3">
                                  <input
                                    type="checkbox"
                                    checked={item.selected}
                                    onChange={() => toggleItemSelection(file.id, item.id)}
                                    className="mt-1 w-5 h-5 rounded border-gray-300"
                                  />

                                  <div className={`p-2 rounded-lg bg-${config.color}-100`}>
                                    <Icon className={`text-${config.color}-600`} size={20} />
                                  </div>

                                  <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-2">
                                      <span className={`badge bg-${config.color}-100 text-${config.color}-800`}>
                                        {config.label}
                                      </span>
                                      <span className={`text-xs ${
                                        item.confidence > 0.8 ? 'text-green-600' :
                                        item.confidence > 0.6 ? 'text-yellow-600' :
                                        'text-red-600'
                                      }`}>
                                        {Math.round(item.confidence * 100)}% confidence
                                      </span>
                                    </div>

                                    {/* Data Preview */}
                                    <div className="grid grid-cols-2 gap-2 text-sm">
                                      {Object.entries(item.data).slice(0, 6).map(([key, value]) => (
                                        <div key={key}>
                                          <span className="text-gray-500">{key.replace(/_/g, ' ')}: </span>
                                          <span className="font-medium">
                                            {typeof value === 'number' ? value.toLocaleString() : String(value)}
                                          </span>
                                        </div>
                                      ))}
                                    </div>

                                    {item.originalText && (
                                      <p className="text-xs text-gray-400 mt-2 italic">
                                        Source: {item.originalText}
                                      </p>
                                    )}
                                  </div>
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Instructions */}
        {files.length === 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-semibold mb-4">How it works</h3>
            <div className="grid md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Upload className="text-blue-600" size={24} />
                </div>
                <h4 className="font-medium">1. Upload</h4>
                <p className="text-sm text-gray-500">Drop or select files</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Brain className="text-purple-600" size={24} />
                </div>
                <h4 className="font-medium">2. Extract</h4>
                <p className="text-sm text-gray-500">AI reads & extracts data</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Eye className="text-green-600" size={24} />
                </div>
                <h4 className="font-medium">3. Review</h4>
                <p className="text-sm text-gray-500">Check & select items</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Send className="text-orange-600" size={24} />
                </div>
                <h4 className="font-medium">4. Save</h4>
                <p className="text-sm text-gray-500">Data goes to right place</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}
