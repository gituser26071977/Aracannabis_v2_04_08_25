/**
 * Test helper: capture stdout while running async code.
 */

export const captureStdout = async (fn: () => Promise<unknown>): Promise<string> => {
  const original = process.stdout.write.bind(process.stdout);
  let captured = '';
  (process.stdout.write as unknown) = (chunk: string | Buffer): boolean => {
    captured += typeof chunk === 'string' ? chunk : chunk.toString('utf8');
    return true;
  };
  try {
    await fn();
  } finally {
    process.stdout.write = original;
  }
  return captured;
};
