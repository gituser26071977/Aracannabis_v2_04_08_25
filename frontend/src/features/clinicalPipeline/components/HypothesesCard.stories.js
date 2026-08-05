import React from 'react';
import HypothesesCard from './HypothesesCard';

export default { title: 'ClinicalPipeline/HypothesesCard', component: HypothesesCard };

const vm = {
  count: 8,
  maxConfidence: 0.94,
  meanConfidence: 0.62,
  top3: [
    { id: 'h1', claim: 'Sono profundo correlaciona com regulação da ansiedade', confidence: 0.94, supportingGenes: ['SLEEP'], contradictingGenes: [], ruleId: 'R_SLEEP_ANX' },
    { id: 'h2', claim: 'Humor rege função cognitiva em janelas curtas', confidence: 0.78, supportingGenes: ['MOOD'], contradictingGenes: [], ruleId: 'R_MOOD_COG' },
  ],
};

export const Success = () => <HypothesesCard state="success" vm={vm} />;
export const Empty = () => <HypothesesCard state="empty" />;
