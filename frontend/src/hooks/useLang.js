/**
 * useLang.js — Language context hook
 * Provides language toggle (en/ta) and translation function throughout the app
 */
import { useState, useCallback } from 'react'
import { t } from '../utils/translations'

export function useLang() {
  const [lang, setLang] = useState(() => localStorage.getItem('farmstock_lang') || 'en')

  const toggleLang = useCallback(() => {
    setLang(prev => {
      const next = prev === 'en' ? 'ta' : 'en'
      localStorage.setItem('farmstock_lang', next)
      return next
    })
  }, [])

  const tr = useCallback((key) => t(lang, key), [lang])

  return { lang, toggleLang, tr }
}
