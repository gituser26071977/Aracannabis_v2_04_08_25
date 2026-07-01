/**
 * FirstBreathScreen — the FIRST visual experience of AraFlow.
 *
 * This is the only screen of Sprint 9. It displays:
 *   - AraFlow logo (text-only placeholder for Sprint 9)
 *   - Protocol name (from compiled plan)
 *   - Remaining time counter
 *   - Phase label ("Inspire", "Segure", "Expire")
 *   - Breath circle (rendered via @presentation/animation-renderer)
 *   - Start / Pause / Stop buttons
 *
 * Composition:
 *   1. `useRenderer` owns the renderer lifecycle
 *   2. `startFirstBreathSession` wires Core → Animation → Renderer
 *   3. rAF tick drives `animation.update(now)` to refresh frames
 *
 * No navigation, no auth, no history, no analytics. Sprint 9 only.
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { AnimationFrame } from '@core/animation-engine';
import { useTokens } from '@shared/theme/useTokens';

import type { FirstBreathHandle, FirstBreathStatus } from './FirstBreathSession';
import { startFirstBreathSession } from './FirstBreathSession';
import type { ReactNativeRenderer } from '../../../presentation/animation-renderer';
import { createReactNativeRenderer } from '../../../presentation/animation-renderer';
import diaphragmaticProtocol from '../protocols/diaphragmatic-breathing.json';

const CANVAS_WIDTH = 320;
const CANVAS_HEIGHT = 360;
const MAX_RADIUS_PX = 130;

export interface FirstBreathScreenProps {
  readonly protocolSource?: string;
  readonly onSessionStarted?: (handle: FirstBreathHandle) => void;
}

export const FirstBreathScreen: React.FC<FirstBreathScreenProps> = ({
  protocolSource = JSON.stringify(diaphragmaticProtocol),
  onSessionStarted,
}) => {
  const tokens = useTokens();
  const rendererRef = useRef<ReactNativeRenderer | null>(null);
  if (rendererRef.current === null) {
    rendererRef.current = createReactNativeRenderer({
      canvasSize: { width: CANVAS_WIDTH, height: CANVAS_HEIGHT },
      transitionMs: 16,
    });
  }
  const renderer = rendererRef.current;

  const handleRef = useRef<FirstBreathHandle | null>(null);
  const [status, setStatus] = useState<FirstBreathStatus>('idle');
  const [frame, setFrame] = useState<AnimationFrame | null>(null);

  // Drive frames via rAF while running.
  useEffect(() => {
    if (status !== 'running') {
      return;
    }
    let rafId = 0;
    const tick = (): void => {
      const handle = handleRef.current;
      if (handle !== null) {
        setFrame(handle.currentFrame());
      }
      rafId = requestAnimationFrame(tick);
    };
    rafId = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(rafId);
    };
  }, [status]);

  // Cleanup on unmount.
  useEffect(() => {
    return () => {
      const handle = handleRef.current;
      if (handle !== null) {
        void handle.stop();
      }
    };
  }, []);

  const handleStart = useCallback(async () => {
    const result = await startFirstBreathSession({
      protocolSource,
      renderer,
    });
    if (result.ok) {
      handleRef.current = result.value;
      setStatus(result.value.status());
      onSessionStarted?.(result.value);
    }
  }, [protocolSource, renderer, onSessionStarted]);

  const handlePause = useCallback(() => {
    handleRef.current?.pause();
    setStatus(handleRef.current?.status() ?? 'idle');
  }, []);

  const handleResume = useCallback(() => {
    handleRef.current?.resume();
    setStatus(handleRef.current?.status() ?? 'idle');
  }, []);

  const handleStop = useCallback(async () => {
    await handleRef.current?.stop();
    handleRef.current = null;
    setStatus('stopped');
    setFrame(null);
  }, []);

  const protocolTitle = handleRef.current?.protocolTitle() ?? 'Respiração Diafragmática';
  const phaseLabel = frame?.label ?? 'Pronto';
  const remainingMs = frame?.remainingTime ?? 0;
  const remainingSeconds = Math.ceil(remainingMs / 1000);

  return (
    <View
      style={[
        styles.container,
        { backgroundColor: tokens.color.background.base, padding: tokens.spacing.lg },
      ]}
    >
      <Text
        style={{
          color: tokens.color.text.primary,
          fontSize: tokens.typography.size.display,
          fontWeight: tokens.typography.weight.bold,
          marginBottom: tokens.spacing.sm,
        }}
      >
        AraFlow
      </Text>
      <Text
        style={{
          color: tokens.color.text.secondary,
          fontSize: tokens.typography.size.body,
          marginBottom: tokens.spacing.lg,
        }}
      >
        {protocolTitle}
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

      <View style={styles.buttons}>
        {status === 'idle' || status === 'stopped' || status === 'errored' ? (
          <Pressable
            onPress={handleStart}
            style={[styles.button, { backgroundColor: tokens.color.brand.primary }]}
          >
            <Text style={[styles.buttonText, { color: tokens.color.text.inverse }]}>Iniciar</Text>
          </Pressable>
        ) : null}
        {status === 'running' ? (
          <Pressable
            onPress={handlePause}
            style={[styles.button, { backgroundColor: tokens.color.brand.secondary }]}
          >
            <Text style={[styles.buttonText, { color: tokens.color.text.inverse }]}>Pausar</Text>
          </Pressable>
        ) : null}
        {status === 'paused' ? (
          <Pressable
            onPress={handleResume}
            style={[styles.button, { backgroundColor: tokens.color.brand.primary }]}
          >
            <Text style={[styles.buttonText, { color: tokens.color.text.inverse }]}>Continuar</Text>
          </Pressable>
        ) : null}
        {status === 'running' || status === 'paused' ? (
          <Pressable
            onPress={handleStop}
            style={[styles.button, { backgroundColor: tokens.color.status.danger }]}
          >
            <Text style={[styles.buttonText, { color: tokens.color.text.inverse }]}>Parar</Text>
          </Pressable>
        ) : null}
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
    marginTop: 24,
  },
  button: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    marginHorizontal: 6,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
  },
});
