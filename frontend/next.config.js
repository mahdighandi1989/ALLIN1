/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  // Enable internationalization
  i18n: {
    locales: ['en', 'fa', 'ar'],
    defaultLocale: 'en',
  },

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  },

  // Image optimization
  images: {
    domains: ['localhost'],
  },

  // Redirects
  async redirects() {
    return [
      {
        source: '/dashboard',
        destination: '/',
        permanent: true,
      },
    ]
  },
}

module.exports = nextConfig
