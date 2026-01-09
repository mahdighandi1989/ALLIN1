/**
 * Settings Hook
 * هوک تنظیمات
 */
import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface SettingsContextType {
  theme: 'light' | 'dark'
  language: 'en' | 'fa' | 'ar'
  setTheme: (theme: 'light' | 'dark') => void
  setLanguage: (lang: 'en' | 'fa' | 'ar') => void
  isRTL: boolean
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined)

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<'light' | 'dark'>('light')
  const [language, setLanguageState] = useState<'en' | 'fa' | 'ar'>('en')

  useEffect(() => {
    // Load from localStorage
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark'
    const savedLang = localStorage.getItem('language') as 'en' | 'fa' | 'ar'

    if (savedTheme) setThemeState(savedTheme)
    if (savedLang) setLanguageState(savedLang)
  }, [])

  useEffect(() => {
    // Apply theme
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  useEffect(() => {
    // Apply RTL
    document.documentElement.dir = language === 'en' ? 'ltr' : 'rtl'
  }, [language])

  const setTheme = (newTheme: 'light' | 'dark') => {
    setThemeState(newTheme)
    localStorage.setItem('theme', newTheme)
  }

  const setLanguage = (newLang: 'en' | 'fa' | 'ar') => {
    setLanguageState(newLang)
    localStorage.setItem('language', newLang)
  }

  return (
    <SettingsContext.Provider
      value={{
        theme,
        language,
        setTheme,
        setLanguage,
        isRTL: language !== 'en'
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
