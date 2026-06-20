'use client'

import { ReactNode } from 'react'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from '@/lib/auth'

/**
 * Client-side application shell: provides the auth context to the whole tree
 * and mounts the toast container. (The previous version only contained an
 * InspectorBridge console-error suppression hack, which has been removed along
 * with the Inspector Bridge tooling.)
 */
export default function ClientWrapper({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      {children}
      <Toaster position="top-right" containerClassName="app-toaster" />
    </AuthProvider>
  )
}
