/**
 * AraFlow — Jest global setup
 *
 * Configura mocks globais, polyfills e utilitários compartilhados por
 * todos os testes. Cada engine/feature pode estender este setup em seu
 * próprio arquivo de testes, mas a base fica aqui.
 */

// Silence React Native warnings em testes (HMR, View, etc.)
jest.mock('react-native/Libraries/Animated/NativeAnimatedHelper');

// Silent console.error quando vier de act() warnings.
// Wrap in try/catch so this file is safe to load as either setupFiles
// (pre-framework) or setupFilesAfterEach (post-framework).
try {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const g: { beforeAll?: (cb: () => void) => void; afterAll?: (cb: () => void) => void } =
    // @ts-expect-error - jest globals may not be available in setupFiles
    globalThis;
  const originalError = console.error;
  g.beforeAll?.(() => {
    console.error = (...args: unknown[]) => {
      const message = String(args[0] ?? '');
      if (message.includes('Warning: An update to') || message.includes('act(')) {
        return;
      }
      originalError(...args);
    };
  });
  g.afterAll?.(() => {
    console.error = originalError;
  });
} catch {
  // Globals not available — skip hook installation.
}
