/**
 * Backup Page v2.0
 * صفحه پشتیبان‌گیری
 */
import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import {
  HardDrive,
  Cloud,
  CheckCircle,
  XCircle,
  Loader2,
  RefreshCw,
  Shield,
  Clock
} from 'lucide-react'
import toast from 'react-hot-toast'

import { useAuth } from '@/hooks/useAuth'
import Layout from '@/components/Layout'
import { reportsApi } from '@/services/api'

interface BackupStatus {
  google_drive_connected: boolean
  folder_configured: boolean
  last_backup: string | null
}

export default function BackupPage() {
  const { user, isLoading, isAuthenticated } = useAuth()
  const router = useRouter()
  const [status, setStatus] = useState<BackupStatus | null>(null)
  const [loadingStatus, setLoadingStatus] = useState(true)
  const [creatingBackup, setCreatingBackup] = useState(false)

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isLoading, isAuthenticated, router])

  useEffect(() => {
    if (isAuthenticated) {
      fetchStatus()
    }
  }, [isAuthenticated])

  const fetchStatus = async () => {
    setLoadingStatus(true)
    try {
      const response = await reportsApi.backupStatus()
      setStatus(response.data)
    } catch (error: any) {
      if (error.response?.status !== 403) {
        toast.error('Failed to fetch backup status')
      }
    } finally {
      setLoadingStatus(false)
    }
  }

  const createBackup = async () => {
    setCreatingBackup(true)
    try {
      const response = await reportsApi.backup()
      toast.success('Backup created successfully!')
      fetchStatus()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Backup failed')
    } finally {
      setCreatingBackup(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  const isAdmin = user?.role === 'admin'

  return (
    <Layout>
      <Head>
        <title>Backup | Banking Operations System</title>
      </Head>

      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Backup & Recovery</h1>
          <p className="text-gray-500">Manage your data backups to Google Drive</p>
        </div>

        {/* Admin Check */}
        {!isAdmin && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
            <div className="flex items-center gap-3">
              <Shield className="w-6 h-6 text-yellow-600" />
              <div>
                <h3 className="font-semibold text-yellow-800">Admin Access Required</h3>
                <p className="text-sm text-yellow-700 mt-1">
                  Only administrators can create backups. Contact your admin for access.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Connection Status */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
              <Cloud className="w-5 h-5 text-blue-600" />
              Google Drive Connection
            </h3>
            <button
              onClick={fetchStatus}
              disabled={loadingStatus}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <RefreshCw className={`w-5 h-5 text-gray-500 ${loadingStatus ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {loadingStatus ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  {status?.google_drive_connected ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-500" />
                  )}
                  <span className="font-medium">Google Drive API</span>
                </div>
                <span className={`text-sm ${status?.google_drive_connected ? 'text-green-600' : 'text-red-500'}`}>
                  {status?.google_drive_connected ? 'Connected' : 'Not Connected'}
                </span>
              </div>

              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  {status?.folder_configured ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-500" />
                  )}
                  <span className="font-medium">Backup Folder</span>
                </div>
                <span className={`text-sm ${status?.folder_configured ? 'text-green-600' : 'text-red-500'}`}>
                  {status?.folder_configured ? 'Configured' : 'Not Configured'}
                </span>
              </div>

              {status?.last_backup && (
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Clock className="w-5 h-5 text-blue-600" />
                    <span className="font-medium">Last Backup</span>
                  </div>
                  <span className="text-sm text-gray-600">
                    {new Date(status.last_backup).toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Create Backup */}
        {isAdmin && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-blue-50 rounded-xl">
                <HardDrive className="w-6 h-6 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">Create Backup</h3>
                <p className="text-sm text-gray-500 mt-1">
                  Create a full backup of your database to Google Drive. This includes all customers,
                  facilities, and system data.
                </p>
                <button
                  onClick={createBackup}
                  disabled={creatingBackup || !status?.google_drive_connected || !status?.folder_configured}
                  className="mt-4 flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {creatingBackup ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Creating Backup...
                    </>
                  ) : (
                    <>
                      <HardDrive className="w-5 h-5" />
                      Create Backup Now
                    </>
                  )}
                </button>
                {(!status?.google_drive_connected || !status?.folder_configured) && (
                  <p className="text-sm text-orange-600 mt-2">
                    Configure Google Drive credentials first to enable backups.
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Configuration Help */}
        <div className="bg-gradient-to-r from-slate-800 to-slate-900 rounded-xl p-6 text-white">
          <h3 className="font-semibold text-lg mb-3">Configuration Guide</h3>
          <div className="space-y-3 text-slate-300 text-sm">
            <p>To enable Google Drive backups, configure these environment variables:</p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li><code className="bg-slate-700 px-2 py-0.5 rounded">GOOGLE_CREDENTIALS_JSON</code> - Service account credentials</li>
              <li><code className="bg-slate-700 px-2 py-0.5 rounded">GOOGLE_DRIVE_FOLDER_ID</code> - Target folder ID</li>
            </ul>
            <p className="mt-4 text-slate-400">
              Need help? Check the documentation or contact your system administrator.
            </p>
          </div>
        </div>
      </div>
    </Layout>
  )
}
