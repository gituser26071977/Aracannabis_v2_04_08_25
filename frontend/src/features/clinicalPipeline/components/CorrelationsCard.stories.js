import React from 'react';
import CorrelationsCard from './CorrelationsCard';

export default { title: 'ClinicalPipeline/CorrelationsCard', component: CorrelationsCard };

const vm = {
  count: 66,
  methods: ['POSITIVE', 'NEGATIVE'],
  max: 0.92,
  mean: 0.31,
  top5: [
    { id: 'c1', geneX: 'SLEEP', geneY: 'ANXIETY', method: 'POSITIVE', coefficient: 0.92, confidence: 0.95 },
    { id: 'c2', geneX: 'MOOD', geneY: 'COGNITION', method: 'NEGATIVE', coefficient: -0.6, confidence: 0.8 },
  ],
};

export const Success = () => <CorrelationsCard state="success" vm={vm} />;
export const Empty = () => <CorrelationsCard state="empty" />;
