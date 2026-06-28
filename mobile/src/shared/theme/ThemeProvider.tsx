/**
 * AraFlow — Theme Provider
 *
 * Fornece o tema atual baseado no modo (light, dark, high-contrast) ou
 * na preferência do sistema operacional. O hook useTokens() resolve
 * para os tokens finais.
 */

import React, { createContext, useContext, useMemo } from 'react';

import { Tokens } from './tokens';
import { lightTheme } from './lightTheme';
import { darkTheme } from './darkTheme';
import { highContrastTheme } from './highContrastTheme';

export type ThemeMode = 'light' | 'dark' | 'high-contrast';
export type ResolvedThemeMode = 'light' | 'dark' | 'high-contrast';

const ThemeContext = createContext<Tokens>(lightTheme);

export interface ThemeProviderProps {
  readonly mode: ThemeMode;
  readonly forceHighContrast?: boolean;
  readonly children: React.ReactNode;
}

const resolveTheme = (mode: ThemeMode, forceHighContrast: boolean | undefined): Tokens => {
  if (forceHighContrast === true) {
    return highContrastTheme;
  }
  if (mode === 'dark') {
    return darkTheme;
  }
  if (mode === 'high-contrast') {
    return highContrastTheme;
  }
  return lightTheme;
};

export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  mode,
  forceHighContrast,
  children,
}) => {
  const theme = useMemo<Tokens>(() => resolveTheme(mode, forceHighContrast), [mode, forceHighContrast]);
  return <ThemeContext.Provider value={theme}>{children}</ThemeContext.Provider>;
};

export const useTheme = (): Tokens => useContext(ThemeContext);
