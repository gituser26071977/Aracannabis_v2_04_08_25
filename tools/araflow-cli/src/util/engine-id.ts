/**
 * engine-id — centralizes the EngineId used by the CLI harness when
 * constructing engines.
 *
 * Single source of truth so any audit / log line refers to the same id.
 */

import { EngineId } from '@araflow/shared-contracts';

export const CLI_ENGINE_ID: ReturnType<typeof EngineId> = EngineId('araflow-cli');
export const CLI_COMPILER_ID: ReturnType<typeof EngineId> = EngineId('araflow-cli-compiler');
export const CLI_RUNTIME_ID: ReturnType<typeof EngineId> = EngineId('araflow-cli-runtime');
export const CLI_BREATH_ID: ReturnType<typeof EngineId> = EngineId('araflow-cli-breath');
