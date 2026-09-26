import type { Metadata } from 'next'
import ClientWrapper from '@/components/ClientWrapper'
import './globals.css'

export const metadata: Metadata = {
  title: 'Banking Operations',
  description: 'Banking Operations Management System',
  // v137 — the app shipped with NO favicon, so every browser asked for
  // /favicon.ico, got a 404, and logged a console error on EVERY page. The
  // supervisor recorded it as an «/audit» fault for a whole run because that is
  // the page it happened to catch it on. The icon is generated from the single
  // BANK_LOGO source (see experiences/letterhead-brand-assets-…) rather than
  // drawn again, so the tab matches the letterhead.
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon.ico',
    apple: '/apple-touch-icon.png',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <ClientWrapper>{children}</ClientWrapper>
      </body>
    </html>
  )
}
