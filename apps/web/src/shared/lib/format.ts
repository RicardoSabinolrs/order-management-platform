/**
 * Formatacao de valores exibidos ao usuario, no idioma da interface.
 *
 * A moeda e sempre BRL - e a moeda em que a plataforma opera. O idioma muda
 * so a escrita ("R$ 12,40" / "R$12.40"), nunca o valor.
 */

import type { Locale } from '@/shared/i18n/locale'

export interface Formatters {
  /** Recebe centavos e devolve moeda: valor monetario nunca trafega como float. */
  currency: (amountInCents: number) => string
  /** Forma curta para eixos e tooltips: "R$ 12,4 mil" em vez de "R$ 12.400,00". */
  compactCurrency: (amountInCents: number) => string
  number: (value: number) => string
  dateTime: (isoDate: string) => string
  date: (isoDate: string) => string
  /** "17/09" - eixo de graficos diarios. */
  dayShort: (isoDate: string) => string
  /** "quinta-feira, 17 de setembro de 2026" - tooltip. */
  dayLong: (isoDate: string) => string
  /** "quinta-feira, 1 de outubro" - cabecalho. */
  today: (date: Date) => string
}

const cache = new Map<Locale, Formatters>()

/** Os `Intl.*Format` sao caros de criar: um conjunto por idioma, reaproveitado. */
export function createFormatters(locale: Locale): Formatters {
  const cached = cache.get(locale)
  if (cached) return cached

  const currency = new Intl.NumberFormat(locale, { style: 'currency', currency: 'BRL' })
  const compactCurrency = new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: 'BRL',
    notation: 'compact',
    maximumFractionDigits: 1,
  })
  const number = new Intl.NumberFormat(locale)
  const dateTime = new Intl.DateTimeFormat(locale, { dateStyle: 'short', timeStyle: 'short' })
  const date = new Intl.DateTimeFormat(locale, { dateStyle: 'medium' })
  const dayShort = new Intl.DateTimeFormat(locale, { day: '2-digit', month: '2-digit' })
  const dayLong = new Intl.DateTimeFormat(locale, { dateStyle: 'full' })
  const today = new Intl.DateTimeFormat(locale, { weekday: 'long', day: 'numeric', month: 'long' })

  const formatters: Formatters = {
    currency: (cents) => currency.format(cents / 100),
    compactCurrency: (cents) => compactCurrency.format(cents / 100),
    number: (value) => number.format(value),
    dateTime: (iso) => dateTime.format(new Date(iso)),
    date: (iso) => date.format(new Date(iso)),
    dayShort: (iso) => dayShort.format(new Date(iso)),
    dayLong: (iso) => dayLong.format(new Date(iso)),
    today: (value) => today.format(value),
  }
  cache.set(locale, formatters)
  return formatters
}
