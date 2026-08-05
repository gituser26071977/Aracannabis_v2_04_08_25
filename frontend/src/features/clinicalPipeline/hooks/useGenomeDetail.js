// useGenomeDetail — GET /knowledge/genomes/{id} query.

import { useQuery } from '@tanstack/react-query';
import knowledgeApi from '../api/knowledgeApi';

export function useGenomeDetail(genomeId, options = {}) {
  return useQuery({
    queryKey: ['genomes', genomeId],
    queryFn: () => knowledgeApi.getGenome(genomeId),
    enabled: !!genomeId,
    staleTime: 30_000,
    ...options,
  });
}

export default useGenomeDetail;
