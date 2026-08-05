import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PipelineInputBar from './PipelineInputBar';

describe('PipelineInputBar', () => {
  it('shows validation error when patient_id missing', async () => {
    const user = userEvent.setup();
    const onRun = jest.fn();
    render(<PipelineInputBar onRun={onRun} />);
    // Clear default value (none) and submit
    await user.click(screen.getByRole('button', { name: /rodar pipeline/i }));
    expect(onRun).not.toHaveBeenCalled();
    expect(screen.getByText(/identificador de paciente/i)).toBeInTheDocument();
  });

  it('submits a valid request', async () => {
    const user = userEvent.setup();
    const onRun = jest.fn();
    render(<PipelineInputBar onRun={onRun} />);
    await user.type(screen.getByLabelText(/identificador do paciente/i), 'patient_a1');
    await user.click(screen.getByRole('button', { name: /rodar pipeline/i }));
    expect(onRun).toHaveBeenCalledTimes(1);
    expect(onRun.mock.calls[0][0]).toMatchObject({ patient_id: 'patient_a1', include_graph: true });
  });
});
