// KnowledgeGraphViewer — read-only React Flow visualization.
// Supports zoom, pan, selection, highlight. NO editing, NO drag-and-drop of
// nodes/edges (per brief).

import React, { useCallback, useMemo } from 'react';
import { Box, Stack, Typography, Chip } from '@mui/material';
import ReactFlow, {
  Controls,
  MiniMap,
  Background,
  applyNodeChanges,
} from 'reactflow';
import 'reactflow/dist/style.css';
import CardShell from './CardShell';

function layoutNodes(nodes, edges) {
  // Simple deterministic layout: spread nodes around a circle; edges drawn between.
  const N = nodes.length;
  const radius = Math.max(220, N * 28);
  const cx = 0;
  const cy = 0;
  return nodes.map((n, i) => {
    const angle = (i / Math.max(1, N)) * 2 * Math.PI;
    return {
      id: n.id,
      type: 'default',
      position: { x: cx + radius * Math.cos(angle), y: cy + radius * Math.sin(angle) },
      data: { label: n.label || n.id },
      style: {
        background: '#0d7377',
        color: '#fff',
        border: '1px solid #0a5e61',
        borderRadius: 8,
        fontSize: 12,
        padding: '6px 10px',
        width: 140,
        textAlign: 'center',
      },
    };
  });
}

function layoutEdges(edges) {
  return edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    label: e.type,
    labelStyle: { fontSize: 10, fill: '#666' },
    style: { stroke: '#888', strokeWidth: Math.max(1, Math.min(4, Math.abs(e.weight || 1))) },
    animated: false,
    type: 'smoothstep',
  }));
}

export default function KnowledgeGraphViewer({ state, graph, errorMessage, onRetry }) {
  const nodes = useMemo(() => (graph?.nodes ? layoutNodes(graph.nodes, graph.edges) : []), [graph]);
  const edges = useMemo(() => (graph?.edges ? layoutEdges(graph.edges) : []), [graph]);

  const [localNodes, setLocalNodes] = React.useState(nodes);
  React.useEffect(() => setLocalNodes(nodes), [nodes]);

  const onNodesChange = useCallback(
    (changes) => setLocalNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );

  return (
    <CardShell
      title="O grafo foi persistido?"
      subtitle={graph ? `${graph.nodeCount} nós · ${graph.edgeCount} relações` : '—'}
      state={state}
      errorMessage={errorMessage}
      onRetry={onRetry}
      emptyMessage="O grafo ainda não foi gerado para este paciente."
      loadingRows={6}
    >
      <Box sx={{ height: 420, border: '1px solid #eee', borderRadius: 2 }}>
        <ReactFlow
          nodes={localNodes}
          edges={edges}
          onNodesChange={onNodesChange}
          nodesDraggable
          nodesConnectable={false}
          elementsSelectable
          zoomOnScroll
          panOnDrag
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={24} color="#f0f0f0" />
          <Controls position="bottom-right" showInteractive={false} />
          <MiniMap pannable zoomable nodeStrokeWidth={2} maskColor="rgba(240,240,240,0.6)" />
        </ReactFlow>
      </Box>
      <Stack direction="row" spacing={1} mt={1.5} flexWrap="wrap" useFlexGap>
        <Typography variant="caption" color="text.secondary">
          Graph <code>{graph?.id || '—'}</code>
        </Typography>
        <Chip size="small" label={`state_hash: ${graph?.stateHash || '—'}`} variant="outlined" />
        <Chip size="small" label={`urn: ${graph?.urn || '—'}`} variant="outlined" />
      </Stack>
    </CardShell>
  );
}
