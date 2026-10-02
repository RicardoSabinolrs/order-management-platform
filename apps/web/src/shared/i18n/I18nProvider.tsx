import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { I18nContext, type I18nContextValue } from '@/shared/i18n/i18nContext'
import { DEFAULT_LOCALE, isLocale, matchLocale, type Locale } from '@/shared/i18n/locale'
import en from '@/shared/i18n/locales/en'
import es from '@/shared/i18n/locales/es'
import ptBR, { type Dictionary } from '@/shared/i18n/locales/pt-BR'
import { createFormatters } from '@/shared/lib/format'

const DICTIONARIES: Record<Locale, Dictionary> = { 'pt-BR': ptBR, en, es }

const STORAGE_KEY = 'oms:idioma'

// Armazenamento bloqueado (janela privada, politica do navegador) nao pode
// derrubar a tela: a escolha so deixa de ser lembrada.
function readStored(): Locale | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return isLocale(stored) ? stored : null
  } catch {
    return null
  }
}

function store(locale: Locale): void {
  try {
    localStorage.setItem(STORAGE_KEY, locale)
  } catch {
    // sem persistencia, vale so nesta aba
  }
}

/** Escolha salva primeiro; senao o idioma do navegador; senao portugues. */
function detect(): Locale {
  return readStored() ?? matchLocale(navigator.languages) ?? DEFAULT_LOCALE
}

interface I18nProviderProps {
  children: ReactNode
  /** Fixa o idioma inicial - os testes nao podem depender do navegador. */
  initialLocale?: Locale
}

export function I18nProvider({ children, initialLocale }: I18nProviderProps) {
  const [locale, setLocaleState] = useState<Locale>(() => initialLocale ?? detect())

  useEffect(() => {
    // Leitor de tela e corretor ortografico leem o idioma do documento.
    document.documentElement.lang = locale
  }, [locale])

  const setLocale = useCallback((next: Locale) => {
    store(next)
    setLocaleState(next)
  }, [])

  const value = useMemo<I18nContextValue>(
    () => ({ locale, setLocale, t: DICTIONARIES[locale], format: createFormatters(locale) }),
    [locale, setLocale],
  )

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}
