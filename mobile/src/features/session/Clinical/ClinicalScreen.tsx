/**
 * ClinicalScreen — the single clinical screen of AraFlow.
 *
 * Three internal phases (per the brief: "Tela inicial → Selecionar
 * protocolo → Start → Sessão → Fim → Feedback"):
 *
 *   select   — list of 3 protocols; tap → advance to 'session'
 *   session  — breath circle + start/pause/resume/stop; on terminal
 *              status → advance to 'feedback'
 *   feedback — "Como você está se sentindo agora?" with 5 emoji
 *              buttons; tap → save FeedbackRecord → back to 'select'
 *
 * No router, no auth, no history. Single screen; internal state
 * machine. No navigation library is wired.
 *
 * The screen owns a ReactNativeRenderer for the breath circle and
 * a ClinicalSession (pure TS orchestrator) for the Core wiring.
 * rAF is used to read `handle.update()` and project the latest
 * AnimationFrame to the renderer.
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';

import type { AnimationFrame } from '@core/animation-engine';
import { useTokens } from '@shared/theme/useTokens';

import {
  type ClinicalSessionHandle,
  type ClinicalSessionStatus,
  startClinicalSession,
} from './ClinicalSession';
import {
  type ClinicalProtocolEntry,
  CLINICAL_PROTOCOLS,
  DEFAULT_CLINICAL_PROTOCOL,
} from './protocols';
import { type FeedbackRecord, saveFeedback } from './feedback/FeedbackStorage';
import {
  FEELING_AFTER_EMOJI,
  type FeelingAfter,
  isFeelingAfter,
} from './feedback/FEELING_AFTER_OPTIONS';
import type { ReactNativeRenderer } from '../../../presentation/animation-renderer';
import {
  createReactNativeRenderer,
  animationFrameToScene,
} from '../../../presentation/animation-renderer';
import { createInMemoryAudioAdapter } from '@core/audio-engine';

const CANVAS_WIDTH = 320;
const CANVAS_HEIGHT = 360;
const MAX_RADIUS_PX = 130;

type ClinicalPhase = 'select' | 'session' | 'feedback';

export interface ClinicalScreenProps {
  /** Optional override for the default protocol catalog. */
  readonly protocols?: readonly ClinicalProtocolEntry[];
}

export const ClinicalScreen: React.FC<ClinicalScreenProps> = ({
  protocols = CLINICAL_PROTOCOLS,
}) => {
  const tokens = useTokens();
  const { t } = useTranslation('common');

  // Renderer — owned by this component for the breath circle.
  const rendererRef = useRef<ReactNativeRenderer | null>(null);
  if (rendererRef.current === null) {
    rendererRef.current = createReactNativeRenderer({
      canvasSize: { width: CANVAS_WIDTH, height: CANVAS_HEIGHT },
      transitionMs: 16,
    });
  }
  const renderer = rendererRef.current;

  // Phase + selection.
  const [phase, setPhase] = useState<ClinicalPhase>('select');
  const [selectedProtocol, setSelectedProtocol] =
    useState<ClinicalProtocolEntry>(DEFAULT_CLINICAL_PROTOCOL);

  // Session state.
  const handleRef = useRef<ClinicalSessionHandle | null>(null);
  const [status, setStatus] = useState<ClinicalSessionStatus>('idle');
  const [frame, setFrame] = useState<AnimationFrame | null>(null);

  // Feedback state.
  const lastSessionRef = useRef<{
    startedAtIso: string;
    completed: boolean;
    durationMs: number;
  } | null>(null);

  // rAF tick while running/paused.
  useEffect(() => {
    if (phase !== 'session') {
      return;
    }
    if (status !== 'running' && status !== 'paused') {
      return;
    }
    let rafId = 0;
    const tick = (): void => {
      const handle = handleRef.current;
      if (handle === null) {
        return;
      }
      const next = handle.update();
      if (next !== null) {
        setFrame(next);
        const scene = animationFrameToScene(next);
        renderer.render(scene);
      }
      if (handle.status() === 'running' || handle.status() === 'paused') {
        rafId = requestAnimationFrame(tick);
      } else {
        // Terminal — promote to feedback.
        lastSessionRef.current = {
          startedAtIso: handle.startedAtIso() ?? new Date().toISOString(),
          completed: handle.completedNaturally(),
          durationMs: handle.totalDurationMs(),
        };
        setStatus(handle.status());
        setPhase('feedback');
      }
    };
    rafId = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(rafId);
    };
  }, [phase, status, renderer]);

  // Cleanup on unmount.
  useEffect(() => {
    return () => {
      const handle = handleRef.current;
      if (handle !== null) {
        void handle.stop();
      }
    };
  }, []);

  const handleStartSession = useCallback(async (protocol: ClinicalProtocolEntry) => {
    const audioAdapter = createInMemoryAudioAdapter();
    const result = await startClinicalSession({
      protocol,
      audioAdapter,
    });
    if (!result.ok) {
      return;
    }
    handleRef.current = result.value;
    setSelectedProtocol(protocol);
    setStatus(result.value.status());
    setPhase('session');
    result.value.start();
    setStatus(result.value.status());
  }, []);

  const handlePause = useCallback(() => {
    handleRef.current?.pause();
    setStatus(handleRef.current?.status() ?? 'idle');
  }, []);

  const handleResume = useCallback(() => {
    handleRef.current?.resume();
    setStatus(handleRef.current?.status() ?? 'idle');
  }, []);

  const handleStop = useCallback(async () => {
    const handle = handleRef.current;
    if (handle === null) {
      setPhase('feedback');
      return;
    }
    lastSessionRef.current = {
      startedAtIso: handle.startedAtIso() ?? new Date().toISOString(),
      completed: handle.completedNaturally(),
      durationMs: handle.totalDurationMs(),
    };
    await handle.stop();
    setStatus('cancelled');
    setPhase('feedback');
  }, []);

  const handleFeedback = useCallback(
    async (feeling: FeelingAfter) => {
      if (!isFeelingAfter(feeling)) {
        return;
      }
      const last = lastSessionRef.current;
      const sessionStartIso = last?.startedAtIso ?? new Date().toISOString();
      const record: FeedbackRecord = {
        protocolId: selectedProtocol.id,
        protocolTitle: selectedProtocol.title,
        feeling,
        sessionDurationMs: last?.durationMs ?? 0,
        completed: last?.completed ?? false,
        recordedAtIso: new Date().toISOString(),
      };
      await saveFeedback({ ...record, sessionStartIso });
      handleRef.current = null;
      lastSessionRef.current = null;
      setFrame(null);
      setStatus('idle');
      setPhase('select');
    },
    [selectedProtocol],
  );

  // ──────────────────────────────────────────────────────────────
  // Render — select phase
  // ──────────────────────────────────────────────────────────────
  if (phase === 'select') {
    return (
      <View
        style={[
          styles.container,
          { backgroundColor: tokens.color.background.base, padding: tokens.spacing.lg },
        ]}
      >
        <Text
          style={[
            styles.title,
            {
              color: tokens.color.text.primary,
              fontSize: tokens.typography.size.display,
              fontWeight: tokens.typography.weight.bold,
            },
          ]}
        >
          AraFlow
        </Text>
        <Text
          style={[
            styles.subtitle,
            { color: tokens.color.text.secondary, fontSize: tokens.typography.size.body },
          ]}
        >
          {t('app.tagline')}
        </Text>
        <View style={[styles.list, { marginTop: tokens.spacing.lg }]}>
          {protocols.map((p) => (
            <Pressable
              key={p.id}
              onPress={() => {
                void handleStartSession(p);
              }}
              style={[
                styles.card,
                {
                  backgroundColor: tokens.color.background.elevated,
                  borderColor: tokens.color.border.subtle,
                  borderRadius: tokens.radius.lg,
                  padding: tokens.spacing.md,
                  marginBottom: tokens.spacing.md,
                },
              ]}
            >
              <Text
                style={[
                  styles.cardTitle,
                  {
                    color: tokens.color.text.primary,
                    fontSize: tokens.typography.size.subheading,
                    fontWeight: tokens.typography.weight.semibold,
                  },
                ]}
              >
                {t(`protocols.${p.i18nKey}`)}
              </Text>
              <Text
                style={[
                  styles.cardMeta,
                  { color: tokens.color.text.secondary, fontSize: tokens.typography.size.caption },
                ]}
              >
                {`~${Math.ceil(p.approxDurationMs / 1000)}s`}
              </Text>
            </Pressable>
          ))}
        </View>
      </View>
    );
  }

  // ──────────────────────────────────────────────────────────────
  // Render — session phase
  // ──────────────────────────────────────────────────────────────
  if (phase === 'session') {
    const phaseLabel = frame?.label ?? t('common.loading');
    const remainingSeconds = Math.ceil((frame?.remainingTime ?? 0) / 1000);
    return (
      <View
        style={[
          styles.container,
          { backgroundColor: tokens.color.background.base, padding: tokens.spacing.lg },
        ]}
      >
        <Text
          style={[
            styles.title,
            {
              color: tokens.color.text.primary,
              fontSize: tokens.typography.size.display,
              fontWeight: tokens.typography.weight.bold,
            },
          ]}
        >
          AraFlow
        </Text>
        <Text
          style={[
            styles.subtitle,
            { color: tokens.color.text.secondary, fontSize: tokens.typography.size.body },
          ]}
        >
          {selectedProtocol.title}
        </Text>
        <View style={styles.canvas}>
          <View style={styles.canvasInner}>
            <View style={[renderer.arcStyle]} />
            <View style={[renderer.circleStrokeStyle]} />
            <View style={[renderer.circleStyle]} />
            <Text
              style={{
                position: 'absolute',
                color: tokens.color.text.primary,
                fontSize: 22,
                fontWeight: '600',
              }}
            >
              {phaseLabel}
            </Text>
            {status === 'running' || status === 'paused' ? (
              <Text
                style={{
                  position: 'absolute',
                  top: CANVAS_HEIGHT / 2 + MAX_RADIUS_PX + 20,
                  color: tokens.color.text.secondary,
                  fontSize: 14,
                }}
              >
                {`${remainingSeconds}s`}
              </Text>
            ) : null}
          </View>
        </View>
        <View style={[styles.buttons, { marginTop: tokens.spacing.lg }]}>
          {status === 'running' ? (
            <Pressable
              onPress={handlePause}
              style={[
                styles.button,
                {
                  backgroundColor: tokens.color.brand.secondary,
                  borderRadius: tokens.radius.md,
                  paddingHorizontal: tokens.spacing.lg,
                  paddingVertical: tokens.spacing.sm,
                },
              ]}
            >
              <Text style={[styles.buttonText, { color: tokens.color.text.inverse }]}>
                {t('common.skip') === 'Pular' ? 'Pausar' : 'Pause'}
              </Text>
            </Pressable>
          ) : null}
          {status === 'paused' ? (
            <Pressable
              onPress={handleResume}
              style={[
                styles.button,
                {
                  backgroundColor: tokens.color.brand.primary,
                  borderRadius: tokens.radius.md,
                  paddingHorizontal: tokens.spacing.lg,
                  paddingVertical: tokens.spacing.sm,
                },
              ]}
            >
              <Text style={[styles.buttonText, { color: tokens.color.text.inverse }]}>
                {t('common.next') === 'Próximo' ? 'Continuar' : 'Resume'}
              </Text>
            </Pressable>
          ) : null}
          {status === 'running' || status === 'paused' ? (
            <Pressable
              onPress={() => {
                void handleStop();
              }}
              style={[
                styles.button,
                {
                  backgroundColor: tokens.color.status.danger,
                  borderRadius: tokens.radius.md,
                  paddingHorizontal: tokens.spacing.lg,
                  paddingVertical: tokens.spacing.sm,
                },
              ]}
            >
              <Text style={[styles.buttonText, { color: tokens.color.text.inverse }]}>
                {t('common.cancel') === 'Cancelar' ? 'Parar' : 'Stop'}
              </Text>
            </Pressable>
          ) : null}
        </View>
      </View>
    );
  }

  // ──────────────────────────────────────────────────────────────
  // Render — feedback phase
  // ──────────────────────────────────────────────────────────────
  return (
    <View
      style={[
        styles.container,
        { backgroundColor: tokens.color.background.base, padding: tokens.spacing.lg },
      ]}
    >
      <Text
        style={[
          styles.title,
          {
            color: tokens.color.text.primary,
            fontSize: tokens.typography.size.display,
            fontWeight: tokens.typography.weight.bold,
          },
        ]}
      >
        AraFlow
      </Text>
      <Text
        style={[
          styles.subtitle,
          { color: tokens.color.text.secondary, fontSize: tokens.typography.size.body },
        ]}
      >
        {t('common.success') === 'Sucesso'
          ? 'Como você está se sentindo agora?'
          : 'How are you feeling now?'}
      </Text>
      <View style={[styles.feedbackRow, { marginTop: tokens.spacing.lg }]}>
        {(['much-worse', 'worse', 'same', 'better', 'much-better'] as FeelingAfter[]).map((f) => (
          <Pressable
            key={f}
            onPress={() => {
              void handleFeedback(f);
            }}
            style={[
              styles.feedbackButton,
              {
                backgroundColor: tokens.color.background.elevated,
                borderColor: tokens.color.border.subtle,
                borderRadius: tokens.radius.lg,
                padding: tokens.spacing.md,
              },
            ]}
          >
            <Text style={[styles.feedbackEmoji, { fontSize: 36 }]}>{FEELING_AFTER_EMOJI[f]}</Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    marginBottom: 4,
  },
  subtitle: {
    marginBottom: 8,
  },
  list: {
    width: '100%',
  },
  card: {
    width: '100%',
    borderWidth: 1,
  },
  cardTitle: {
    marginBottom: 4,
  },
  cardMeta: {},
  canvas: {
    width: CANVAS_WIDTH,
    height: CANVAS_HEIGHT,
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 16,
  },
  canvasInner: {
    width: CANVAS_WIDTH,
    height: CANVAS_HEIGHT,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttons: {
    flexDirection: 'row',
    gap: 12,
  },
  button: {
    marginHorizontal: 6,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  feedbackRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    justifyContent: 'center',
  },
  feedbackButton: {
    minWidth: 72,
    minHeight: 72,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    margin: 6,
  },
  feedbackEmoji: {},
});
