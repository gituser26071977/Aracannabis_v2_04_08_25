# Audio Engine

> **Status:** Sprint 0 — Foundation stub
> **Próxima implementação:** Sprint 5

## Responsabilidade

Reproduz áudio (voz guiada, ambient tracks, beeps de transição) **sincronizado com o Breath Engine**.

## O que ele faz

- Carrega áudio (bundled, cached, streaming).
- Reproduz/Pausa/Para com fade in/out.
- Sincroniza com fases do Breath Engine.
- Ducking (reduz volume durante voz).
- Audio focus handling (interrupções iOS/Android).

## Estrutura

```
audio-engine/
├── domain/            # AudioCue, AudioTrack, AudioCueType
├── application/       # Play, Pause, Stop, ScheduleCue
└── infrastructure/    # NativeAudioAdapter, AssetLoader
```

## Dependências

- Timer Engine.
- Breath Engine (fases).

## Consumidores

- UI (botão de mute, settings).

## Documentação adicional

Ver `docs/AraFlow/33_ENGINEERING_BLUEPRINT.md` §8 (Sistema de Áudio).
