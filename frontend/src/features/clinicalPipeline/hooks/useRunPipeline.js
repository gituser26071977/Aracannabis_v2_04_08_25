// useRunPipeline — POST /knowledge/pipelines/run mutation.
// Returns the raw envelope payload (DTO) plus meta; the page maps to a VM.

import { useMutation, useQueryClient } from '@tanstack/react-query';
import knowledgeApi from '../api/knowledgeApi';

export function useRunPipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (request) => knowledgeApi.runPipeline(request),
    onSuccess: () => {
      // The pipeline creates a new genome and may invalidate the list.
      qc.invalidateQueries({ queryKey: ['genomes'] });
      qc.invalidateQueries({ queryKey: ['sessions'] });
    },
  });
}

export default useRunPipeline;
