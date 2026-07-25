import React from 'react';
import PipelineCard from './PipelineCard';

export default { title: 'ClinicalPipeline/PipelineCard', component: PipelineCard };

const vm = {
  pipeline: { startedAt: '08:31:02', completedAt: '08:31:03', durationSeconds: 1.2, version: '1.0.0' },
  timeline: [{ requestId: 'req_x', correlationId: 'corr_x' }],
};

export const Success = () => <PipelineCard state="success" vm={vm} />;
export const Loading = () => <PipelineCard state="loading" />;
export const Error = () => <PipelineCard state="error" errorMessage="boom" />;
