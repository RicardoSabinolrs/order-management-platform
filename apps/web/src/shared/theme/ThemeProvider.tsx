import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { ThemeContext, type Theme, type ThemeContextValue } from '@/shared/theme/themeContext'

// A mesma chave lida pelo script inline do index.html, que aplica o tema antes
// do React subir - sem ele a tela piscaria clara antes de escurecer.
const STORAGE_KEY = 'oms:tema'

function readStored(): Theme | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored === 'light' || stored === 'dark' ? stored : null
  } catch {
    return null
  }
}

function store(theme: Theme): void {
  try {
    localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    // sem persistencia, vale so nesta aba
  }
}

function systemTheme(): Theme {
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => readStored() ?? systemTheme())

  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

  const setTheme = useCallback((next: Theme) => {
    store(next)
    setThemeState(next)
  }, [])

  const toggleTheme = useCallback(() => {
    setThemeState((current) => {
      const next = current === 'dark' ? 'light' : 'dark'
      store(next)
      return next
    })
  }, [])

  const value = useMemo<ThemeContextValue>(
    () => ({ theme, setTheme, toggleTheme }),
    [theme, setTheme, toggleTheme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}
