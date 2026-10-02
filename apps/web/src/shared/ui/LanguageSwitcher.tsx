import { useCallback, useRef, useState } from 'react'

import { LOCALES, LOCALE_NAMES, LOCALE_SHORT } from '@/shared/i18n/locale'
import { useI18n } from '@/shared/i18n/useI18n'
import { useDismiss } from '@/shared/lib/useDismiss'
import { IconCheck, IconChevronDown, IconGlobe } from '@/shared/ui/icons'

/** Troca de idioma: o rotulo de cada opcao vem escrito no proprio idioma. */
export function LanguageSwitcher({ compact = false }: { compact?: boolean }) {
  const { locale, setLocale, t } = useI18n()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const close = useCallback(() => setOpen(false), [])
  useDismiss(ref, open, close)

  return (
    <div className="popover" ref={ref}>
      <button
        type="button"
        className="pill-btn"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`${t.common.language}: ${LOCALE_NAMES[locale]}`}
        onClick={() => setOpen((current) => !current)}
      >
        <IconGlobe size={16} />
        <span className="pill-btn__text">{compact ? LOCALE_SHORT[locale] : LOCALE_NAMES[locale]}</span>
        <IconChevronDown size={14} />
      </button>

      {open ? (
        <div className="popover__panel" role="menu" aria-label={t.common.language}>
          {LOCALES.map((option) => (
            <button
              key={option}
              type="button"
              role="menuitemradio"
              aria-checked={option === locale}
              className="popover__item"
              lang={option}
              onClick={() => {
                setLocale(option)
                close()
              }}
            >
              <span className="popover__code">{LOCALE_SHORT[option]}</span>
              <span className="popover__label">{LOCALE_NAMES[option]}</span>
              {option === locale ? <IconCheck size={15} /> : null}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  )
}
