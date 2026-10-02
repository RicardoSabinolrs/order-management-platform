import { useI18n } from '@/shared/i18n/useI18n'
import { useTheme } from '@/shared/theme/useTheme'
import { IconMoon, IconSun } from '@/shared/ui/icons'

/** Alterna claro/escuro. O icone mostra o destino, o rotulo diz a acao. */
export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()
  const { t } = useI18n()
  const escuro = theme === 'dark'

  return (
    <button
      type="button"
      className="icon-btn theme-toggle"
      aria-label={escuro ? t.common.switchToLight : t.common.switchToDark}
      title={escuro ? t.common.lightTheme : t.common.darkTheme}
      onClick={toggleTheme}
    >
      {escuro ? <IconSun size={18} /> : <IconMoon size={18} />}
    </button>
  )
}
