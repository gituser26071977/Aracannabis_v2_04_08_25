/**
 * Design Tokens — fonte única de verdade para espaçamentos, raios, durações e
 * curvas de animação usadas em todo o frontend.
 *
 * Por que existe:
 *   - Componentes MUI herdam o theme, mas estilos `sx={{}}` ainda espalhavam valores
 *     "mágicos" (12, 16, 20, 24, 'cubic-bezier(0.4, 0, 0.2, 1)', '0.3s'...).
 *   - Centralizar aqui permite mudar UM valor e propagar para todo o app.
 *
 * NÃO inclui paleta (vai no theme.palette).
 * NÃO inclui sombras por elevação (vai no theme.shadows).
 *
 * Como usar:
 *   import { tokens } from '../theme/tokens';
 *   <Box sx={{ borderRadius: tokens.radius.lg, transition: tokens.transition.base }} />
 */
export const tokens = {
  // Raios — devem bater com theme.shape.borderRadius (12)
  radius: {
    xs: 4,
    sm: 8,
    md: 12,    // default
    lg: 16,    // Card / Paper / TableContainer
    xl: 20,    // Dialog
    '2xl': 24, // Hero
    pill: 9999,
  },

  // Espaçamentos — múltiplos de 4 (sistema 8pt)
  space: {
    0: 0,
    1: 4,
    2: 8,
    3: 12,
    4: 16,
    5: 20,
    6: 24,
    8: 32,
    10: 40,
    12: 48,
    16: 64,
  },

  // Durações padronizadas
  duration: {
    fast: '150ms',
    base: '250ms',
    slow: '400ms',
    page: '500ms',
  },

  // Curvas de easing — usado em todas as transições
  easing: {
    standard: 'cubic-bezier(0.4, 0, 0.2, 1)',     // Material standard
    decelerate: 'cubic-bezier(0.0, 0, 0.2, 1)',   // Entrada
    accelerate: 'cubic-bezier(0.4, 0, 1, 1)',     // Saída
    spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',  // Bounce sutil
  },

  // Shorthand pronto para usar em sx.transition
  transition: {
    fast: 'all 150ms cubic-bezier(0.4, 0, 0.2, 1)',
    base: 'all 250ms cubic-bezier(0.4, 0, 0.2, 1)',
    slow: 'all 400ms cubic-bezier(0.4, 0, 0.2, 1)',
    transform: 'transform 250ms cubic-bezier(0.4, 0, 0.2, 1)',
    color: 'color 150ms ease, background-color 150ms ease, border-color 150ms ease',
  },

  // Hierarquia de elevação — alinhada com theme.shadows
  elevation: {
    flat: 0,
    low: 1,
    card: 2,
    raised: 4,
    floating: 8,
    modal: 16,
    hero: 24,
  },

  // Tamanhos padronizados para áreas clicáveis (mobile-first)
  hitTarget: {
    sm: 32,
    md: 40,
    lg: 48,
  },

  // Z-index scale — evita z-index "mágicos" (10, 100, 999)
  zIndex: {
    base: 0,
    raised: 10,
    sticky: 100,
    drawer: 1100,
    modal: 1300,
    snackbar: 1400,
    tooltip: 1500,
  },
};

export default tokens;
