/**
 * AraFlow — Light Theme
 *
 * Paleta clara padrão. Inspirada em tons relaxantes (azul-sálvia, verde-
 * sálvia) com alto contraste para acessibilidade.
 */

import type { Tokens } from './tokens';

export const lightTheme: Tokens = {
  color: {
    brand: {
      primary: '#2E7D6B',
      primaryHover: '#246A5A',
      primaryActive: '#1B5546',
      secondary: '#7BA8A0',
    },
    background: {
      base: '#FAFBFC',
      elevated: '#FFFFFF',
      overlay: 'rgba(15, 23, 42, 0.5)',
    },
    text: {
      primary: '#0F172A',
      secondary: '#475569',
      tertiary: '#94A3B8',
      inverse: '#FFFFFF',
      disabled: '#CBD5E1',
    },
    border: {
      subtle: '#E2E8F0',
      strong: '#94A3B8',
      focus: '#2E7D6B',
    },
    status: {
      success: '#16A34A',
      warning: '#D97706',
      danger: '#DC2626',
      info: '#0284C7',
    },
    accent: {
      inhale: '#7DD3C0',
      holdIn: '#A78BFA',
      exhale: '#60A5FA',
      holdOut: '#94A3B8',
    },
  },
  spacing: {
    xxs: 2,
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  radius: {
    none: 0,
    sm: 4,
    md: 8,
    lg: 16,
    pill: 9999,
  },
  typography: {
    size: {
      caption: 12,
      body: 16,
      subheading: 18,
      heading: 24,
      display: 32,
    },
    weight: {
      regular: '400',
      medium: '500',
      semibold: '600',
      bold: '700',
    },
    lineHeight: {
      tight: 1.2,
      normal: 1.5,
      relaxed: 1.8,
    },
  },
  motion: {
    fast: 150,
    normal: 300,
    slow: 600,
  },
  zIndex: {
    base: 0,
    dropdown: 1000,
    overlay: 1100,
    modal: 1200,
    toast: 1300,
  },
};
