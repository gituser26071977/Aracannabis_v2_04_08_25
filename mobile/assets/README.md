# Assets

> **Status:** Sprint 0 — Foundation stub
> **Próximo:** Sprint 11 (Design System + assets)

## Estrutura

```
assets/
├── audios/         # mp3/m4a de voz guiada e ambient
├── icons/          # SVGs ou PNGs do design system
├── animations/     # Lottie JSONs
├── fonts/          # TTF/OTF de tipografia custom
└── images/         # Imagens estáticas
```

## Convenções

- **Áudios:** nome em kebab-case, formato `.m4a` (iOS-friendly) e `.mp3` (Android-friendly). Ex.: `voice-cue-inhale-pt-br.m4a`.
- **Ícones:** SVG preferido; PNG apenas quando SVG não suportar. Tamanho base 24x24.
- **Animações:** Lottie JSON. Manter tamanho < 100KB.
- **Fontes:** Inter (sans-serif) e Inter Display (display). Pesos 400, 500, 600, 700.

## Próximos passos

1. Sprint 11: importar Inter via `@expo-google-fonts/inter` ou `react-native-asset`.
2. Sprint 12: criar/contratar voice acting para áudios pt-BR e en-US.
3. Sprint 13: design system icons (componentes primitivos).
