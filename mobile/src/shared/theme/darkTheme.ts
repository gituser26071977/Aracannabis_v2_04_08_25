/**
 * AraFlow — Dark Theme
 *
 * Paleta escura. Pensada para uso noturno (muitos usuários fazem sessões
 * antes de dormir). Contraste mínimo WCAG AA garantido.
 */

import type { Tokens } from './tokens';

export const darkTheme: Tokens = {
  color: {
    brand: {
      primary: '#5EAE9C',
      primaryHover: '#76BCAC',
      primaryActive: '#92CCBE',
      secondary: '#9CC4BD',
    },
    background: {
      base: '#0B1220',
      elevated: '#111A2E',
      overlay: 'rgba(0, 0, 0, 0.7)',
    },
    text: {
      primary: '#F1F5F9',
      secondary: '#CBD5E1',
      tertiary: '#94A3B8',
      inverse: '#0F172A',
      disabled: '#475569',
    },
    border: {
      subtle: '#1E293B',
      strong: '#475569',
      focus: '#5EAE9C',
    },
    status: {
      success: '#22C55E',
      warning: '#F59E0B',
      danger: '#EF4444',
      info: '#38BDF8',
    },
    accent: {
      inhale: '#5EEAD4',
      holdIn: '#C4B5FD',
      exhale: '#93C5FD',
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
