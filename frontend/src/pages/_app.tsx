/**
 * Banking Operations System - Main App Component
 */
import type { AppProps } from 'next/app'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { useEffect, useState } from 'react'

import '@/styles/globals.css'
import { AuthProvider } from '@/hooks/useAuth'
import { SettingsProvider } from '@/hooks/useSettings'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      retry: 1,
    },
  },
})

export default function App({ Component, pageProps }: AppProps) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return null
  }

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <SettingsProvider>
          <Component {...pageProps} />
          <Toaster
            position="top-left"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
            }}
          />
        </SettingsProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}
