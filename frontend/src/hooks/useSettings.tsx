/**
 * Settings Hook
 * هوک تنظیمات
 */
import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react'
import { settingsApi } from '@/services/api'

interface AppSettings {
  theme: 'light' | 'dark' | 'system'
  language: 'en' | 'fa' | 'ar'
  primaryColor: string
  sidebarCollapsed: boolean
  denseMode: boolean
}

interface SettingsContextType {
  theme: 'light' | 'dark' | 'system'
  resolvedTheme: 'light' | 'dark'
  language: 'en' | 'fa' | 'ar'
  primaryColor: string
  sidebarCollapsed: boolean
  denseMode: boolean
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  setLanguage: (lang: 'en' | 'fa' | 'ar') => void
  setPrimaryColor: (color: string) => void
  setSidebarCollapsed: (collapsed: boolean) => void
  setDenseMode: (dense: boolean) => void
  isRTL: boolean
  saveSettings: () => Promise<void>
}

const defaultSettings: AppSettings = {
  theme: 'light',
  language: 'en',
  primaryColor: '#2563eb',
  sidebarCollapsed: false,
  denseMode: false,
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined)

// CSS variable for primary color
const applyPrimaryColor = (color: string) => {
  document.documentElement.style.setProperty('--primary-color', color)

  // Also update Tailwind-style classes dynamically
  const root = document.documentElement
  root.style.setProperty('--color-primary-50', adjustColor(color, 0.9))
  root.style.setProperty('--color-primary-100', adjustColor(color, 0.8))
  root.style.setProperty('--color-primary-200', adjustColor(color, 0.6))
  root.style.setProperty('--color-primary-500', color)
  root.style.setProperty('--color-primary-600', adjustColor(color, -0.1))
  root.style.setProperty('--color-primary-700', adjustColor(color, -0.2))
}

// Helper to lighten/darken color
const adjustColor = (hex: string, amount: number): string => {
  const num = parseInt(hex.replace('#', ''), 16)
  const r = Math.min(255, Math.max(0, (num >> 16) + Math.round(255 * amount)))
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0x00ff) + Math.round(255 * amount)))
  const b = Math.min(255, Math.max(0, (num & 0x0000ff) + Math.round(255 * amount)))
  return `#${(0x1000000 + (r << 16) + (g << 8) + b).toString(16).slice(1)}`
}

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<AppSettings>(defaultSettings)
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('light')
  const [loaded, setLoaded] = useState(false)

  // Load settings from localStorage and API
  useEffect(() => {
    const loadSettings = async () => {
      // First load from localStorage for instant UI
      const savedSettings = localStorage.getItem('appSettings')
      if (savedSettings) {
        try {
          const parsed = JSON.parse(savedSettings)
          setSettings(prev => ({ ...prev, ...parsed }))
        } catch (e) {
          console.error('Failed to parse saved settings')
        }
      }

      // Then try to load from API
      try {
        const response = await settingsApi.getUser()
        if (response.data?.settings) {
          const apiSettings = response.data.settings
          const newSettings: AppSettings = {
            theme: apiSettings.theme || settings.theme,
            language: apiSettings.language || settings.language,
            primaryColor: apiSettings.primary_color || settings.primaryColor,
            sidebarCollapsed: apiSettings.sidebar_collapsed ?? settings.sidebarCollapsed,
            denseMode: apiSettings.dense_mode ?? settings.denseMode,
          }
          setSettings(newSettings)
          localStorage.setItem('appSettings', JSON.stringify(newSettings))
        }
      } catch (e) {
        // Silently fail - use localStorage/defaults
      }

      setLoaded(true)
    }

    loadSettings()
  }, [])

  // Resolve system theme
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

    const updateResolvedTheme = () => {
      if (settings.theme === 'system') {
        setResolvedTheme(mediaQuery.matches ? 'dark' : 'light')
      } else {
        setResolvedTheme(settings.theme as 'light' | 'dark')
      }
    }

    updateResolvedTheme()
    mediaQuery.addEventListener('change', updateResolvedTheme)

    return () => mediaQuery.removeEventListener('change', updateResolvedTheme)
  }, [settings.theme])

  // Apply theme to document
  useEffect(() => {
    if (!loaded) return

    const root = document.documentElement

    if (resolvedTheme === 'dark') {
      root.classList.add('dark')
      root.style.colorScheme = 'dark'
    } else {
      root.classList.remove('dark')
      root.style.colorScheme = 'light'
    }
  }, [resolvedTheme, loaded])

  // Apply language/RTL
  useEffect(() => {
    if (!loaded) return

    const isRTL = settings.language === 'fa' || settings.language === 'ar'
    document.documentElement.dir = isRTL ? 'rtl' : 'ltr'
    document.documentElement.lang = settings.language
  }, [settings.language, loaded])

  // Apply primary color
  useEffect(() => {
    if (!loaded) return
    applyPrimaryColor(settings.primaryColor)
  }, [settings.primaryColor, loaded])

  // Apply dense mode
  useEffect(() => {
    if (!loaded) return
    document.documentElement.classList.toggle('dense', settings.denseMode)
  }, [settings.denseMode, loaded])

  const setTheme = useCallback((theme: 'light' | 'dark' | 'system') => {
    setSettings(prev => {
      const newSettings = { ...prev, theme }
      localStorage.setItem('appSettings', JSON.stringify(newSettings))
      return newSettings
    })
  }, [])

  const setLanguage = useCallback((language: 'en' | 'fa' | 'ar') => {
    setSettings(prev => {
      const newSettings = { ...prev, language }
      localStorage.setItem('appSettings', JSON.stringify(newSettings))
      return newSettings
    })
  }, [])

  const setPrimaryColor = useCallback((primaryColor: string) => {
    setSettings(prev => {
      const newSettings = { ...prev, primaryColor }
      localStorage.setItem('appSettings', JSON.stringify(newSettings))
      return newSettings
    })
  }, [])

  const setSidebarCollapsed = useCallback((sidebarCollapsed: boolean) => {
    setSettings(prev => {
      const newSettings = { ...prev, sidebarCollapsed }
      localStorage.setItem('appSettings', JSON.stringify(newSettings))
      return newSettings
    })
  }, [])

  const setDenseMode = useCallback((denseMode: boolean) => {
    setSettings(prev => {
      const newSettings = { ...prev, denseMode }
      localStorage.setItem('appSettings', JSON.stringify(newSettings))
      return newSettings
    })
  }, [])

  // Save settings to API
  const saveSettings = useCallback(async () => {
    try {
      await settingsApi.updateUser({
        theme: settings.theme,
        language: settings.language,
        primary_color: settings.primaryColor,
        sidebar_collapsed: settings.sidebarCollapsed,
        dense_mode: settings.denseMode,
      })
    } catch (e) {
      console.error('Failed to save settings to API')
      throw e
    }
  }, [settings])

  const isRTL = settings.language === 'fa' || settings.language === 'ar'

  return (
    <SettingsContext.Provider
      value={{
        theme: settings.theme,
        resolvedTheme,
        language: settings.language,
        primaryColor: settings.primaryColor,
        sidebarCollapsed: settings.sidebarCollapsed,
        denseMode: settings.denseMode,
        setTheme,
        setLanguage,
        setPrimaryColor,
        setSidebarCollapsed,
        setDenseMode,
        isRTL,
        saveSettings,
      }}
    >
      {children}
    </SettingsContext.Provider>
  )
}

export function useSettings() {
  const context = useContext(SettingsContext)
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider')
  }
  return context
}
