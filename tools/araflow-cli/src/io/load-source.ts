/**
 * load-source — reads a JSON file from disk and wraps it as a
 * `ProtocolSource` for the compiler.
 *
 * Errors are explicit so callers can render a friendly message instead
 * of dealing with raw fs/JSON.parse exceptions.
 */

import { readFileSync } from 'node:fs';
import { JsonSource, type ProtocolSource } from '@core/protocol-compiler';
import { AppError } from '@araflow/shared-contracts';

export const loadProtocolSource = (filepath: string): ProtocolSource => {
  let raw: string;
  try {
    raw = readFileSync(filepath, 'utf8');
  } catch (cause) {
    throw new AppError(`Could not read protocol file: ${filepath}`, {
      code: 'cli_io_read_error',
      severity: 'fatal',
      context: { filepath },
      cause,
    });
  }
  if (raw.trim().length === 0) {
    throw new AppError(`Protocol file is empty: ${filepath}`, {
      code: 'cli_io_empty_file',
      severity: 'fatal',
      context: { filepath },
    });
  }
  return JsonSource(raw, `cli://${filepath}`);
};
