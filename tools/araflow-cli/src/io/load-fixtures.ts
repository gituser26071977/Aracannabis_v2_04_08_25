/**
 * load-fixtures — discovers JSON protocol fixtures in a directory.
 *
 * Returns an alphabetical list of paths. Used by tests and by
 * `araflow validate --bundle fixtures/` style commands (future).
 */

import { readdirSync } from 'node:fs';
import { join } from 'node:path';

export const discoverFixtures = (dir: string): readonly string[] => {
  const entries = readdirSync(dir, { withFileTypes: true });
  return entries
    .filter((entry) => entry.isFile() && entry.name.endsWith('.json'))
    .map((entry) => join(dir, entry.name))
    .sort();
};
