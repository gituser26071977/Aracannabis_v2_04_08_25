/**
 * AraFlow — High Contrast Theme
 *
 * Paleta de alto contraste, conforme WCAG AAA. Para usuários com baixa
 * visão, ambientes externos muito iluminados, ou preferências de
 * acessibilidade.
 */

import type { Tokens } from './tokens';

export const highContrastTheme: Tokens = {
  color: {
    brand: {
      primary: '#FFFFFF',
      primaryHover: '#FFFFFF',
      primaryActive: '#FFFFFF',
      secondary: '#FFFF00',
    },
    background: {
      base: '#000000',
      elevated: '#0A0A0A',
      overlay: 'rgba(0, 0, 0, 0.9)',
    },
    text: {
      primary: '#FFFFFF',
      secondary: '#FFFF00',
      tertiary: '#FFFFFF',
      inverse: '#000000',
      disabled: '#999999',
    },
    border: {
      subtle: '#FFFFFF',
      strong: '#FFFFFF',
      focus: '#FFFF00',
    },
    status: {
      success: '#00FF00',
      warning: '#FFFF00',
      danger: '#FF0000',
      info: '#00FFFF',
    },
    accent: {
      inhale: '#00FFFF',
      holdIn: '#FFFF00',
      exhale: '#FF00FF',
      holdOut: '#FFFFFF',
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
      caption: 14,
      body: 18,
      subheading: 20,
      heading: 26,
      display: 34,
    },
    weight: {
      regular: '400',
      medium: '500',
      semibold: '600',
      bold: '700',
    },
    lineHeight: {
      tight: 1.3,
      normal: 1.6,
      relaxed: 1.9,
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
