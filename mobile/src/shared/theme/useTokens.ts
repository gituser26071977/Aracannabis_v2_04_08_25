/**
 * useTokens — alias for useTheme.
 *
 * Mantemos dois nomes para clareza semântica: useTheme para quem está
 * pensando em theming, useTokens para quem está pensando em design
 * tokens.
 */

import { useTheme } from './ThemeProvider';

export const useTokens = useTheme;
