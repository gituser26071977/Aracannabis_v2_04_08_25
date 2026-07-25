// Composed ViewModel for the page. Combines the raw pipeline response
// with timing/request metadata and produces the timeline entries the
// TimelineRail consumes. Pure function; no React.

import {
  pipelineRunDataToViewModel,
  buildTimelineFromVm,
  replayResultToViewModel,
} from '../mappers/dtoToViewModel';

export function composePipelineVm({ data, meta, replayData }) {
  const vm = pipelineRunDataToViewModel(data);
  if (!vm) return null;
  const timeline = buildTimelineFromVm(vm, meta?.request_id, meta?.correlation_id);
  const replay = replayResultToViewModel(replayData, vm.genome?.stateHash);
  return { ...vm, timeline, replay, requestMeta: meta || null };
}

export default composePipelineVm;
