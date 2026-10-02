import { createContext } from 'react'

import type { Locale } from '@/shared/i18n/locale'
import type { Dictionary } from '@/shared/i18n/locales/pt-BR'
import type { Formatters } from '@/shared/lib/format'

export interface I18nContextValue {
  locale: Locale
  setLocale: (locale: Locale) => void
  /** Dicionario do idioma atual: `t.orders.newOrder`, `t.orders.count(3)`. */
  t: Dictionary
  /** Moeda, numero e data escritos no idioma atual. */
  format: Formatters
}

/** Separado do provider: modulo com componente e valor quebra o fast refresh. */
export const I18nContext = createContext<I18nContextValue | null>(null)
