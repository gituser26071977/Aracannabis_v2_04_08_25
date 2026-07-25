// ClinicalPipelineExplorer — the single page of the Clinical Pipeline Explorer.
// One screen, no menu, no admin. The 6 questions are answered by glancing at the 6 cards.

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Box, Stack, Container, Alert } from '@mui/material';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '../../lib/queryClient';
import { useRunPipeline } from '../../features/clinicalPipeline/hooks/useRunPipeline';
import { useReplaySession } from '../../features/clinicalPipeline/hooks/useReplaySession';
import { useSessionsList } from '../../features/clinicalPipeline/hooks/useSessionsList';
import { composePipelineVm } from '../../features/clinicalPipeline/viewModels/pipelineViewModel';
import PipelineInputBar from '../../features/clinicalPipeline/components/PipelineInputBar';
import PatientCard from '../../features/clinicalPipeline/components/PatientCard';
import PipelineCard from '../../features/clinicalPipeline/components/PipelineCard';
import GenomeCard from '../../features/clinicalPipeline/components/GenomeCard';
import CorrelationsCard from '../../features/clinicalPipeline/components/CorrelationsCard';
import HypothesesCard from '../../features/clinicalPipeline/components/HypothesesCard';
import KnowledgeGraphViewer from '../../features/clinicalPipeline/components/KnowledgeGraphViewer';
import ReplayPanel from '../../features/clinicalPipeline/components/ReplayPanel';
import TimelineRail from '../../features/clinicalPipeline/components/TimelineRail';
import DemoBanner from '../../features/clinicalPipeline/demo/DemoBanner';
import { useDemoMode } from '../../features/clinicalPipeline/demo/useDemoMode';

function PageHeader() {
  return (
    <Box sx={{ pt: 4, pb: 2 }}>
      <Box component="h1" sx={{ m: 0, fontSize: 28, fontWeight: 600 }}>
        O que o AraOS encontrou neste paciente
      </Box>
      <Box sx={{ color: 'text.secondary', mt: 0.5, maxWidth: 720 }}>
        A cada execução, um pipeline reprodutível transforma o histórico clínico em um
        genome, encontra correlações entre os genes, formula hipóteses e persiste um
        grafo de conhecimento — sempre verificável por replay.
      </Box>
    </Box>
  );
}

function Inner() {
  const runMut = useRunPipeline();
  const replayMut = useReplaySession();
  const sessionsQuery = useSessionsList();
  const demo = useDemoMode();

  const [lastEnvelope, setLastEnvelope] = useState(null);
  const [lastRequestId, setLastRequestId] = useState(null);
  const [selectedSessionId, setSelectedSessionId] = useState('');

  // When the mutation succeeds, cache the last envelope (payload + meta).
  useEffect(() => {
    if (runMut.isSuccess && runMut.data) {
      const { payload, meta } = runMut.data || {};
      setLastEnvelope({ payload, meta: meta || null });
      setLastRequestId(meta?.request_id || null);
      // Refresh sessions list — a new research session may have been produced.
      sessionsQuery.refetch();
    }
  }, [runMut.isSuccess, runMut.data]); // eslint-disable-line react-hooks/exhaustive-deps

  // Demo Mode: auto-seed the page with the deterministic fixture on mount.
  useEffect(() => {
    if (!demo.enabled) return undefined;
    const env = demo.runDemo();
    setLastEnvelope({ payload: env.payload, meta: env.meta });
    setLastRequestId(env.meta?.request_id || null);
    setSelectedSessionId(demo.listDemoSessions()[0]?.session_id || '');
    // Auto-trigger the replay after a small delay so the user sees it "land".
    const timer = setTimeout(() => {
      const rep = demo.replayDemo();
      setLastEnvelope((prev) => (prev ? { ...prev, replay: rep.payload } : prev));
    }, 5000);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [demo.enabled]);

  const handleRun = useCallback(
    (request) => {
      runMut.mutate(request);
    },
    [runMut]
  );

  const handleReplay = useCallback(
    (sessionId) => {
      if (demo.enabled) {
        const rep = demo.replayDemo();
        setLastEnvelope((prev) => (prev ? { ...prev, replay: rep.payload } : prev));
        return;
      }
      replayMut.mutate(sessionId);
    },
    [replayMut, demo]
  );

  // Replay mutation result: copy into lastEnvelope.replay for the ReplayPanel.
  useEffect(() => {
    if (replayMut.isSuccess && replayMut.data && lastEnvelope) {
      setLastEnvelope({ ...lastEnvelope, replay: replayMut.data });
    }
  }, [replayMut.isSuccess, replayMut.data, lastEnvelope]);

  const vm = useMemo(
    () => composePipelineVm({ data: lastEnvelope?.payload, meta: lastEnvelope?.meta }),
    [lastEnvelope]
  );
  const isOnline = typeof navigator === 'undefined' ? true : navigator.onLine;

  // In Demo Mode we already have data seeded — show success immediately.
  const pipelineState = runMut.isPending
    ? 'loading'
    : runMut.isError
      ? 'error'
      : vm
        ? 'success'
        : isOnline
          ? 'empty'
          : 'offline';

  const errorMessage = runMut.isError
    ? (runMut.error?.message || 'Falha ao executar pipeline.')
    : null;

  const lastSummary = vm?.genome?.id
    ? `Último pipeline: genome ${vm.genome.id} · ${vm.correlations.count} correlações · ${vm.hypotheses.count} hipóteses`
    : null;

  const sessionsForPanel = demo.enabled
    ? demo.listDemoSessions()
    : (sessionsQuery.data?.items || []);

  return (
    <Container maxWidth="xl" sx={{ pb: 8 }}>
      <PageHeader />

      {demo.enabled ? <DemoBanner onClose={demo.disable} /> : null}

      <PipelineInputBar
        onRun={handleRun}
        isRunning={runMut.isPending}
        lastSummary={lastSummary}
        errorMessage={errorMessage}
        demoMode={demo.enabled}
      />

      {replayMut.isError ? (
        <Alert severity="error" sx={{ mt: 2 }}>
          Falha ao executar replay: {replayMut.error?.message}
        </Alert>
      ) : null}

      <Box
        sx={{
          mt: 3,
          display: 'grid',
          gap: 3,
          gridTemplateColumns: { xs: '1fr', md: '2fr 1fr' },
        }}
      >
        <Stack spacing={3}>
          <PatientCard state={pipelineState} vm={vm?.patient} errorMessage={errorMessage} onRetry={() => runMut.reset()} />
          <PipelineCard state={pipelineState} vm={vm} requestMeta={lastRequestId} errorMessage={errorMessage} onRetry={() => runMut.reset()} />
          <GenomeCard state={pipelineState} vm={vm?.genome} errorMessage={errorMessage} onRetry={() => runMut.reset()} />
          <CorrelationsCard state={pipelineState} vm={vm?.correlations} errorMessage={errorMessage} onRetry={() => runMut.reset()} />
          <HypothesesCard state={pipelineState} vm={vm?.hypotheses} errorMessage={errorMessage} onRetry={() => runMut.reset()} />
          <KnowledgeGraphViewer state={pipelineState} graph={vm?.graph} errorMessage={errorMessage} onRetry={() => runMut.reset()} />
          <ReplayPanel
            state={pipelineState}
            sessionId={selectedSessionId || null}
            sessions={sessionsForPanel}
            onSelectSession={setSelectedSessionId}
            replay={vm?.replay}
            isReplaying={replayMut.isPending}
            onReplay={handleReplay}
            errorMessage={replayMut.isError ? replayMut.error?.message : null}
          />
        </Stack>
        <Box>
          <TimelineRail entries={vm?.timeline || []} />
        </Box>
      </Box>
    </Container>
  );
}

export default function ClinicalPipelineExplorer() {
  return (
    <QueryClientProvider client={queryClient}>
      <Inner />
    </QueryClientProvider>
  );
}
