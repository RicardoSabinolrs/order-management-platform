import { useContext } from 'react'

import { ThemeContext, type ThemeContextValue } from '@/shared/theme/themeContext'

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme precisa estar dentro de <ThemeProvider>')
  }
  return context
}
