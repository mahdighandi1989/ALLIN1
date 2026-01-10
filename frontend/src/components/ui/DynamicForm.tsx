/**
 * Dynamic Form Component
 * فرم داینامیک برای ایجاد و ویرایش رکوردها
 */
import { useState, useEffect } from 'react'
import { X, Save, Loader } from 'lucide-react'

export interface FormField {
  key: string
  label: string
  type: 'text' | 'number' | 'email' | 'tel' | 'date' | 'select' | 'textarea' | 'checkbox' | 'radio' | 'file'
  required?: boolean
  placeholder?: string
  options?: { value: string; label: string }[]
  defaultValue?: any
  validation?: (value: any) => string | null
  group?: string
  width?: 'full' | 'half' | 'third'
  disabled?: boolean
  helpText?: string
}

interface DynamicFormProps {
  title: string
  fields: FormField[]
  initialData?: Record<string, any>
  onSubmit: (data: Record<string, any>) => Promise<void>
  onCancel: () => void
  submitText?: string
  loading?: boolean
}

export default function DynamicForm({
  title,
  fields,
  initialData = {},
  onSubmit,
  onCancel,
  submitText = 'Save',
  loading = false,
}: DynamicFormProps) {
  const [formData, setFormData] = useState<Record<string, any>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    // Initialize form data
    const initial: Record<string, any> = {}
    fields.forEach((field) => {
      initial[field.key] = initialData[field.key] ?? field.defaultValue ?? ''
    })
    setFormData(initial)
  }, [fields, initialData])

  const handleChange = (key: string, value: any) => {
    setFormData((prev) => ({ ...prev, [key]: value }))
    // Clear error on change
    if (errors[key]) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[key]
        return newErrors
      })
    }
  }

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    fields.forEach((field) => {
      const value = formData[field.key]

      // Required check
      if (field.required && (value === '' || value === null || value === undefined)) {
        newErrors[field.key] = `${field.label} is required`
        return
      }

      // Custom validation
      if (field.validation && value) {
        const error = field.validation(value)
        if (error) {
          newErrors[field.key] = error
        }
      }

      // Email validation
      if (field.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        if (!emailRegex.test(value)) {
          newErrors[field.key] = 'Invalid email address'
        }
      }
    })

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validate()) return

    setSubmitting(true)
    try {
      await onSubmit(formData)
    } catch (error: any) {
      setErrors({ _form: error.message || 'An error occurred' })
    } finally {
      setSubmitting(false)
    }
  }

  // Group fields by group name
  const groupedFields = fields.reduce((acc, field) => {
    const group = field.group || 'default'
    if (!acc[group]) acc[group] = []
    acc[group].push(field)
    return acc
  }, {} as Record<string, FormField[]>)

  const renderField = (field: FormField) => {
    const value = formData[field.key]
    const error = errors[field.key]
    const baseClassName = `w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
      error ? 'border-red-500' : 'border-gray-300'
    } ${field.disabled ? 'bg-gray-100' : ''}`

    const widthClass = {
      full: 'col-span-2',
      half: 'col-span-1',
      third: 'col-span-1 md:col-span-1',
    }[field.width || 'half']

    return (
      <div key={field.key} className={widthClass}>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {field.label}
          {field.required && <span className="text-red-500 ml-1">*</span>}
        </label>

        {field.type === 'textarea' ? (
          <textarea
            value={value || ''}
            onChange={(e) => handleChange(field.key, e.target.value)}
            placeholder={field.placeholder}
            disabled={field.disabled}
            rows={3}
            className={baseClassName}
          />
        ) : field.type === 'select' ? (
          <select
            value={value || ''}
            onChange={(e) => handleChange(field.key, e.target.value)}
            disabled={field.disabled}
            className={baseClassName}
          >
            <option value="">Select {field.label}</option>
            {field.options?.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        ) : field.type === 'checkbox' ? (
          <input
            type="checkbox"
            checked={value || false}
            onChange={(e) => handleChange(field.key, e.target.checked)}
            disabled={field.disabled}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
        ) : field.type === 'radio' ? (
          <div className="flex gap-4">
            {field.options?.map((opt) => (
              <label key={opt.value} className="flex items-center gap-2">
                <input
                  type="radio"
                  name={field.key}
                  value={opt.value}
                  checked={value === opt.value}
                  onChange={(e) => handleChange(field.key, e.target.value)}
                  disabled={field.disabled}
                  className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                />
                {opt.label}
              </label>
            ))}
          </div>
        ) : (
          <input
            type={field.type}
            value={value || ''}
            onChange={(e) => handleChange(field.key, e.target.value)}
            placeholder={field.placeholder}
            disabled={field.disabled}
            className={baseClassName}
          />
        )}

        {field.helpText && (
          <p className="text-xs text-gray-500 mt-1">{field.helpText}</p>
        )}
        {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button
            onClick={onCancel}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <X size={20} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="p-4 overflow-y-auto max-h-[calc(90vh-140px)]">
            {errors._form && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700">
                {errors._form}
              </div>
            )}

            {Object.entries(groupedFields).map(([group, groupFields]) => (
              <div key={group} className="mb-6">
                {group !== 'default' && (
                  <h3 className="text-md font-medium text-gray-800 mb-3 pb-2 border-b">
                    {group}
                  </h3>
                )}
                <div className="grid grid-cols-2 gap-4">
                  {groupFields.map(renderField)}
                </div>
              </div>
            ))}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 p-4 border-t bg-gray-50">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 border rounded-lg hover:bg-gray-100"
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || loading}
              className="btn-primary flex items-center gap-2"
            >
              {submitting ? (
                <Loader className="animate-spin" size={18} />
              ) : (
                <Save size={18} />
              )}
              {submitText}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
