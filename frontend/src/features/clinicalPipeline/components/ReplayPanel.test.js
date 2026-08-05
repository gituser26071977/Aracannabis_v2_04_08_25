import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ReplayPanel from './ReplayPanel';

describe('ReplayPanel', () => {
  it('shows empty state when no session selected', () => {
    render(<ReplayPanel state="empty" sessionId={null} sessions={[]} onSelectSession={() => {}} onReplay={() => {}} />);
    expect(screen.getByText(/sem sessão/i)).toBeInTheDocument();
  });

  it('shows match chip when replay.match=true', () => {
    render(
      <ReplayPanel
        state="success"
        sessionId="s1"
        sessions={[{ session_id: 's1', analysis_type: 'CORRELATIONS' }]}
        onSelectSession={() => {}}
        onReplay={() => {}}
        replay={{ match: true, sessionId: 's1_replayed', durationSeconds: 1.0 }}
      />
    );
    expect(screen.getByText(/Replay OK/i)).toBeInTheDocument();
  });

  it('shows diff when replay.match=false', () => {
    render(
      <ReplayPanel
        state="success"
        sessionId="s1"
        sessions={[{ session_id: 's1', analysis_type: 'CORRELATIONS' }]}
        onSelectSession={() => {}}
        onReplay={() => {}}
        replay={{ match: false, sessionId: 's1_r', durationSeconds: 1.0, diff: { original: 'h_old', replay: 'h_new' } }}
      />
    );
    expect(screen.getByText(/Diferença encontrada/i)).toBeInTheDocument();
    expect(screen.getByText('h_old')).toBeInTheDocument();
    expect(screen.getByText('h_new')).toBeInTheDocument();
  });

  it('invokes onReplay when button clicked', async () => {
    const user = userEvent.setup();
    const onReplay = jest.fn();
    render(
      <ReplayPanel
        state="success"
        sessionId="s1"
        sessions={[{ session_id: 's1', analysis_type: 'CORRELATIONS' }]}
        onSelectSession={() => {}}
        onReplay={onReplay}
      />
    );
    await user.click(screen.getByRole('button', { name: /executar replay/i }));
    expect(onReplay).toHaveBeenCalledWith('s1');
  });
});
