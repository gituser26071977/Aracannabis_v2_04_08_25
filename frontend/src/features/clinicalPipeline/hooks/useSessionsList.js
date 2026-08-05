// useSessionsList — GET /knowledge/research/sessions.

import { useQuery } from '@tanstack/react-query';
import knowledgeApi from '../api/knowledgeApi';

export function useSessionsList(options = {}) {
  return useQuery({
    queryKey: ['sessions'],
    queryFn: () => knowledgeApi.listSessions(),
    staleTime: 30_000,
    ...options,
  });
}

export default useSessionsList;
