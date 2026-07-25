// useReplaySession — POST /knowledge/research/sessions/{id}/replay mutation.

import { useMutation } from '@tanstack/react-query';
import knowledgeApi from '../api/knowledgeApi';

export function useReplaySession() {
  return useMutation({
    mutationFn: (sessionId) => knowledgeApi.replaySession(sessionId),
  });
}

export default useReplaySession;
