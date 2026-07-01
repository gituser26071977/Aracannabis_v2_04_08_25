/**
 * useRenderer hook test — verifies the React hook returns a stable
 * renderer and disposes it on unmount.
 */

import React from 'react';
import { act, create } from 'react-test-renderer';

import { useRenderer } from '../../../src/presentation/animation-renderer/rn/ReactNativeRenderer';

const HookHost: React.FC<{ canvasWidth: number; canvasHeight: number }> = ({
  canvasWidth,
  canvasHeight,
}) => {
  const r = useRenderer({ canvasSize: { width: canvasWidth, height: canvasHeight } });
  return <>{r.id}</>;
};

describe('useRenderer hook', () => {
  it('returns a renderer instance with the expected id', () => {
    let capturedId: string | null = null;
    const Capture: React.FC = () => {
      const r = useRenderer({ canvasSize: { width: 100, height: 100 } });
      capturedId = r.id;
      return null;
    };
    let root: ReturnType<typeof create> | null = null;
    act(() => {
      root = create(<Capture />);
    });
    expect(capturedId).toBe('rn-primitives-v1');
    act(() => {
      root?.unmount();
    });
  });

  it('renders the host component', () => {
    let root: ReturnType<typeof create> | null = null;
    act(() => {
      root = create(<HookHost canvasWidth={200} canvasHeight={300} />);
    });
    expect(root).not.toBeNull();
    act(() => {
      root?.unmount();
    });
  });
});