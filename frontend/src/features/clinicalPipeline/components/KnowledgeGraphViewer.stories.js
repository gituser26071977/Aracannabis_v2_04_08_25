import React from 'react';
import KnowledgeGraphViewer from './KnowledgeGraphViewer';

export default { title: 'ClinicalPipeline/KnowledgeGraphViewer', component: KnowledgeGraphViewer };

const graph = {
  id: 'graph_demo',
  stateHash: 'h_demo',
  builtAt: 't',
  urn: 'urn:demo',
  nodeCount: 4,
  edgeCount: 4,
  nodes: [
    { id: 'g1', label: 'SLEEP' },
    { id: 'g2', label: 'ANXIETY' },
    { id: 'g3', label: 'MOOD' },
    { id: 'g4', label: 'COGNITION' },
  ],
  edges: [
    { id: 'e1', source: 'g1', target: 'g2', type: 'POSITIVE', weight: 0.9 },
    { id: 'e2', source: 'g1', target: 'g3', type: 'POSITIVE', weight: 0.6 },
    { id: 'e3', source: 'g2', target: 'g4', type: 'NEGATIVE', weight: 0.7 },
    { id: 'e4', source: 'g3', target: 'g4', type: 'POSITIVE', weight: 0.5 },
  ],
};

export const Success = () => <KnowledgeGraphViewer state="success" graph={graph} />;
export const Empty = () => <KnowledgeGraphViewer state="empty" />;
