/**
 * AraFlow — Backend entrypoint.
 *
 * Sprint 0: stub. O backend AraFlow é apenas para componentes não
 * cobertos pelo AraOS (sync de sessões, analytics ingestion, LGPD
 * export endpoint). Endpoints reais serão implementados em sprints
 * subsequentes.
 */

export const BACKEND_VERSION = '0.0.0-foundation' as const;

const main = (): void => {
  // eslint-disable-next-line no-console
  console.log(`AraFlow backend ${BACKEND_VERSION} — stub. Use AraOS endpoints for now.`);
};

if (require.main === module) {
  main();
}
