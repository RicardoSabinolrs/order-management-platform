import { createContext } from 'react'

export type Theme = 'light' | 'dark'

export interface ThemeContextValue {
  theme: Theme
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
}

/** Separado do provider: modulo com componente e valor quebra o fast refresh. */
export const ThemeContext = createContext<ThemeContextValue | null>(null)
