// useGenomesList — GET /knowledge/genomes.

import { useQuery } from '@tanstack/react-query';
import knowledgeApi from '../api/knowledgeApi';

export function useGenomesList(options = {}) {
  return useQuery({
    queryKey: ['genomes'],
    queryFn: () => knowledgeApi.listGenomes(),
    staleTime: 30_000,
    ...options,
  });
}

export default useGenomesList;
