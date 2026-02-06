

import type { Metadata } from 'next'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from '@/lib/auth'
import './globals.css'

import InspectorBridge from "./InspectorBridge";

export const metadata: Metadata = {
  title: 'Banking Operations',
  description: 'Banking Operations Management System',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          {<InspectorBridge />}
        {children}
          <Toaster position="top-right" />
        </AuthProvider>
      </body>
    </html>
  )
}