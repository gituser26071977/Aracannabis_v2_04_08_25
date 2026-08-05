import React from 'react';
import TimelineRail from './TimelineRail';

export default { title: 'ClinicalPipeline/TimelineRail', component: TimelineRail };

const entries = [
  { id: 's1', label: 'Pipeline iniciado', at: new Date().toISOString() },
  { id: 's2', label: 'Genome criado (g_abc)', at: new Date().toISOString() },
  { id: 's3', label: 'Correlações: 66', at: new Date().toISOString() },
  { id: 's4', label: 'Hipóteses: 8', at: new Date().toISOString() },
  { id: 's5', label: 'Graph persistido (12 nós, 21 arestas)', at: new Date().toISOString() },
  { id: 's6', label: 'Pipeline concluído', at: new Date().toISOString() },
];

export const WithEntries = () => <TimelineRail entries={entries} />;
export const Empty = () => <TimelineRail entries={[]} />;
