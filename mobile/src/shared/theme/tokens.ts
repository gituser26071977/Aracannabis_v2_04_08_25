/**
 * AraFlow — Design Tokens
 *
 * Tokens de design são a FONTE DE VERDADE do sistema visual. Componentes
 * NÃO usam cores/valores hard-coded; sempre consomem tokens.
 *
 * Esta estrutura é compatível com Style Dictionary; em sprints futuros,
 * a geração pode ser automatizada.
 */

export type ColorScale = {
  readonly 50: string;
  readonly 100: string;
  readonly 200: string;
  readonly 300: string;
  readonly 400: string;
  readonly 500: string;
  readonly 600: string;
  readonly 700: string;
  readonly 800: string;
  readonly 900: string;
  readonly 950: string;
};

export type SemanticColors = {
  readonly brand: {
    readonly primary: string;
    readonly primaryHover: string;
    readonly primaryActive: string;
    readonly secondary: string;
  };
  readonly background: {
    readonly base: string;
    readonly elevated: string;
    readonly overlay: string;
  };
  readonly text: {
    readonly primary: string;
    readonly secondary: string;
    readonly tertiary: string;
    readonly inverse: string;
    readonly disabled: string;
  };
  readonly border: {
    readonly subtle: string;
    readonly strong: string;
    readonly focus: string;
  };
  readonly status: {
    readonly success: string;
    readonly warning: string;
    readonly danger: string;
    readonly info: string;
  };
  readonly accent: {
    readonly inhale: string;
    readonly holdIn: string;
    readonly exhale: string;
    readonly holdOut: string;
  };
};

export type SpacingScale = {
  readonly xxs: number;
  readonly xs: number;
  readonly sm: number;
  readonly md: number;
  readonly lg: number;
  readonly xl: number;
  readonly xxl: number;
};

export type RadiusScale = {
  readonly none: number;
  readonly sm: number;
  readonly md: number;
  readonly lg: number;
  readonly pill: number;
};

export type TypographySize = {
  readonly caption: number;
  readonly body: number;
  readonly subheading: number;
  readonly heading: number;
  readonly display: number;
};

export type TypographyWeight = {
  readonly regular: '400';
  readonly medium: '500';
  readonly semibold: '600';
  readonly bold: '700';
};

export type Typography = {
  readonly size: TypographySize;
  readonly weight: TypographyWeight;
  readonly lineHeight: {
    readonly tight: number;
    readonly normal: number;
    readonly relaxed: number;
  };
};

export type Tokens = {
  readonly color: SemanticColors;
  readonly spacing: SpacingScale;
  readonly radius: RadiusScale;
  readonly typography: Typography;
  readonly motion: {
    readonly fast: number;
    readonly normal: number;
    readonly slow: number;
  };
  readonly zIndex: {
    readonly base: number;
    readonly dropdown: number;
    readonly overlay: number;
    readonly modal: number;
    readonly toast: number;
  };
};
