import React from 'react';
import ReplayPanel from './ReplayPanel';

export default { title: 'ClinicalPipeline/ReplayPanel', component: ReplayPanel };

const sessions = [
  { session_id: 'sess_001', analysis_type: 'CORRELATIONS' },
  { session_id: 'sess_002', analysis_type: 'HYPOTHESES' },
];

export const Empty = () => <ReplayPanel state="empty" sessionId={null} sessions={[]} onSelectSession={() => {}} onReplay={() => {}} />;

export const SuccessMatch = () => (
  <ReplayPanel
    state="success"
    sessionId="sess_001"
    sessions={sessions}
    onSelectSession={() => {}}
    onReplay={() => {}}
    replay={{ match: true, sessionId: 'sess_001_replayed', durationSeconds: 1.0 }}
  />
);

export const SuccessMismatch = () => (
  <ReplayPanel
    state="success"
    sessionId="sess_001"
    sessions={sessions}
    onSelectSession={() => {}}
    onReplay={() => {}}
    replay={{ match: false, sessionId: 'sess_001_r', durationSeconds: 1.0, diff: { original: 'h_old', replay: 'h_new' } }}
  />
);
