typescript
import type { Metadata } from 'next'
import ClientWrapper from '@/components/ClientWrapper'
import './globals.css'

export const metadata: Metadata = {
  title: 'Banking Operations',
  description: 'Banking Operations Management System',
}

// Prevent InspectorBridge errors by wrapping the application
const SafeClientWrapper = ({ children }: { children: React.ReactNode }) => {
  try {
    return <ClientWrapper>{children}</ClientWrapper>
  } catch (error) {
    console.warn('InspectorBridge error caught and handled:', error)
    return <>{children}</>
  }
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <SafeClientWrapper>
          {children}
        </SafeClientWrapper>
      </body>
    </html>
  )
}