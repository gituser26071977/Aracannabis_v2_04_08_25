import React from 'react';
import PipelineInputBar from './PipelineInputBar';

export default { title: 'ClinicalPipeline/PipelineInputBar', component: PipelineInputBar };

export const Idle = () => <PipelineInputBar onRun={() => {}} />;
export const Running = () => <PipelineInputBar onRun={() => {}} isRunning />;
export const WithSummary = () => <PipelineInputBar onRun={() => {}} lastSummary="Último pipeline: genome g_abc · 66 correlações · 8 hipóteses" />;
