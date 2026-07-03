/**
 * AraFlow — react-native-gesture-handler web shim.
 *
 * The mobile bundle imports `GestureHandlerRootView` from
 * `react-native-gesture-handler` (a native-only package). On web we
 * expose a transparent passthrough `<div>` so the tree shape is
 * preserved but no gesture handler is wired up.
 *
 * The component accepts the same `style` prop the native view expects.
 * `children` are rendered directly.
 */

import React from 'react';

interface GestureHandlerRootViewProps {
  readonly children?: React.ReactNode;
  readonly style?: React.CSSProperties;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  readonly [key: string]: any;
}

export const GestureHandlerRootView: React.FC<GestureHandlerRootViewProps> = ({
  children,
  style,
  ...rest
}) => {
  return React.createElement('div', { style: { ...style }, ...rest }, children);
};

export default GestureHandlerRootView;
