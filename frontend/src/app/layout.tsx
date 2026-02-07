import type { Metadata } from 'next'
import ClientWrapper from '@/components/ClientWrapper'
import './globals.css'

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
        <ClientWrapper>
          {children}
        </ClientWrapper>
      </body>
    </html>
  )
}
