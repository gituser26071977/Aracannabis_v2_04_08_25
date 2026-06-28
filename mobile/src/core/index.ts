/**
 * AraFlow — Core (engines)
 *
 * Cada engine tem sua própria Clean Architecture interna
 * (domain / application / infrastructure). Engines se comunicam
 * via eventos, não chamadas diretas.
 *
 * Implementação: Sprints 1–7.
 */

export const ARAFLOW_CORE_VERSION = '0.0.0-foundation' as const;
