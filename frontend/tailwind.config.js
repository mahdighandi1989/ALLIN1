/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      // Central design tokens so colours/spacing/radius stay consistent across
      // every page instead of being hand-tuned per component.
      colors: {
        primary: {
          DEFAULT: '#2563eb', // blue-600 — the app's brand/action colour
          hover: '#1d4ed8',   // blue-700
          50: '#eff6ff',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
      borderRadius: {
        card: '0.75rem',
      },
      boxShadow: {
        card: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
      },
    },
  },
  plugins: [],
}