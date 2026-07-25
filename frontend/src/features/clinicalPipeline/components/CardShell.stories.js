// Storybook stories — Clinical Pipeline Explorer components.
// To activate, install @storybook/react (CRA 5 + React 18 compatible).
// Stories are written in Component Story Format 3 and will work as-is once
// the Storybook binary is wired (`npx storybook init`).

import React from 'react';
import CardShell from './CardShell';

export default {
  title: 'ClinicalPipeline/CardShell',
  component: CardShell,
  argTypes: { state: { control: 'select', options: ['loading', 'empty', 'error', 'success', 'offline'] } },
};

const Template = (args) => (
  <CardShell {...args}>
    <span>Conteúdo populado quando state=success.</span>
  </CardShell>
);

export const Loading = Template.bind({});
Loading.args = { title: 'Pipeline', state: 'loading' };

export const Empty = Template.bind({});
Empty.args = { title: 'Pipeline', state: 'empty', emptyMessage: 'Sem dados ainda.' };

export const Error = Template.bind({});
Error.args = { title: 'Pipeline', state: 'error', errorMessage: 'Falha ao executar pipeline.', onRetry: () => {} };

export const Success = Template.bind({});
Success.args = { title: 'Pipeline', subtitle: '1200 ms', state: 'success' };

export const Offline = Template.bind({});
Offline.args = { title: 'Pipeline', state: 'offline' };
