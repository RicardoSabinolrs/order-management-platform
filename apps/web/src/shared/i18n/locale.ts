/** Idiomas suportados pela interface. */

export const LOCALES = ['pt-BR', 'en', 'es'] as const

export type Locale = (typeof LOCALES)[number]

export const DEFAULT_LOCALE: Locale = 'pt-BR'

/** Nome de cada idioma escrito nele mesmo: quem nao le o atual acha o seu. */
export const LOCALE_NAMES: Record<Locale, string> = {
  'pt-BR': 'Português',
  en: 'English',
  es: 'Español',
}

export const LOCALE_SHORT: Record<Locale, string> = {
  'pt-BR': 'PT',
  en: 'EN',
  es: 'ES',
}

export function isLocale(value: unknown): value is Locale {
  return typeof value === 'string' && (LOCALES as readonly string[]).includes(value)
}

/** Casa o idioma do navegador ("es-AR", "en-US") com um dos suportados. */
export function matchLocale(candidates: readonly string[]): Locale | null {
  for (const candidate of candidates) {
    const base = candidate.toLowerCase().split('-')[0]
    if (base === 'pt') return 'pt-BR'
    if (base === 'en') return 'en'
    if (base === 'es') return 'es'
  }
  return null
}
