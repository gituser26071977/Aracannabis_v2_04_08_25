// IntelligentImporter.jsx — Importador inteligente multi-tenant
// Suporta 4 intents: profissionais_saude, equipe_admin, disponibilidade, consultorios
// Fluxo: upload → analyze (preview) → usuário revisa → apply (persiste)
import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress, Divider,
  FormControl, Grid, InputLabel, LinearProgress, MenuItem, Paper, Select,
  Stack, Step, StepLabel, Stepper, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Tab, Tabs, Typography, Tooltip, IconButton, Snackbar,
} from '@mui/material';
import { CloudUpload, Refresh, CheckCircle, Warning, ErrorOutline, Info, Download } from '@mui/icons-material';
import intelligentImportService from '../../services/intelligentImportService';

const STEP_UPLOAD = 0;
const STEP_ANALYZE = 1;
const STEP_REVIEW = 2;
const STEP_APPLY = 3;

const INTENTS_FALLBACK = [
  { intent: 'profissionais_saude', label: 'Profissionais de Saúde', icon: '🩺' },
  { intent: 'equipe_admin',        label: 'Equipe Administrativa',  icon: '👩‍💼' },
  { intent: 'disponibilidade',     label: 'Disponibilidade',        icon: '📅' },
  { intent: 'consultorios',        label: 'Consultórios',           icon: '🏥' },
];

const IntelligentImporter = () => {
  // Opções de intents do backend
  const [intents, setIntents] = useState(INTENTS_FALLBACK);
  const [intentSelecionado, setIntentSelecionado] = useState('profissionais_saude');
  const [forceIntent, setForceIntent] = useState(false);

  // Arquivo + estado da análise
  const [arquivo, setArquivo] = useState(null);
  const [loadingOptions, setLoadingOptions] = useState(false);
  const [loadingAnalyze, setLoadingAnalyze] = useState(false);
  const [loadingApply, setLoadingApply] = useState(false);
  const [progress, setProgress] = useState(0);
  const [preview, setPreview] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [feedback, setFeedback] = useState({ open: false, severity: 'info', text: '' });

  useEffect(() => {
    let alive = true;
    (async () => {
      setLoadingOptions(true);
      try {
        const r = await intelligentImportService.listIntents();
        if (alive && r?.intents?.length) {
          setIntents(r.intents.map(i => ({
            intent: i.intent, label: i.label, icon: (
              i.intent === 'profissionais_saude' ? '🩺' :
              i.intent === 'equipe_admin'        ? '👩‍💼' :
              i.intent === 'disponibilidade'     ? '📅' :
              i.intent === 'consultorios'        ? '🏥' : '📄'
            ),
          })));
        }
      } catch (e) {
        console.warn('Falha ao carregar intents; usando fallback.', e);
      } finally {
        if (alive) setLoadingOptions(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  const handleFile = (e) => {
    const f = e.target.files?.[0] || null;
    setArquivo(f);
    setPreview(null);
    setActiveTab(0);
  };

  const handleAnalyze = async () => {
    if (!arquivo) return;
    setLoadingAnalyze(true);
    setProgress(0);
    setPreview(null);
    // Simula progresso (a request real retorna em segundos)
    const t = setInterval(() => setProgress(p => Math.min(p + 15, 85)), 300);
    try {
      const r = await intelligentImportService.analyze(
        arquivo,
        forceIntent ? intentSelecionado : null
      );
      clearInterval(t);
      setProgress(100);
      setPreview(r.preview);
      setActiveTab(0);
      if ((r.preview?.total_registros ?? 0) === 0) {
        setFeedback({ open: true, severity: 'warning',
          text: 'Nenhum registro detectado. Verifique o arquivo ou tente forçar um intent.' });
      } else {
        setFeedback({ open: true, severity: 'success',
          text: `${r.preview.validos} válido(s), ${r.preview.invalidos} com erro de ${r.preview.total_registros} total.` });
      }
    } catch (err) {
      clearInterval(t);
      const msg = err?.response?.data?.error || err.message || 'Erro ao analisar arquivo';
      setFeedback({ open: true, severity: 'error', text: msg });
    } finally {
      setLoadingAnalyze(false);
      setTimeout(() => setProgress(0), 800);
    }
  };

  const handleApply = async () => {
    if (!preview?.records?.length) return;
    const valid = preview.records.filter(r => r.valid);
    if (!valid.length) {
      setFeedback({ open: true, severity: 'warning', text: 'Nenhum registro válido para aplicar.' });
      return;
    }
    setLoadingApply(true);
    try {
      const r = await intelligentImportService.apply(preview.intent, valid);
      setFeedback({
        open: true, severity: 'success',
        text: `Aplicado: ${r.aplicados} criado(s), ${r.vinculados} vinculado(s), ${r.ignorados} ignorado(s).` +
              (r.warnings?.length ? ` ${r.warnings.length} aviso(s).` : ''),
      });
      setPreview(null);
      setArquivo(null);
    } catch (err) {
      const msg = err?.response?.data?.error || err.message || 'Erro ao aplicar';
      setFeedback({ open: true, severity: 'error', text: msg });
    } finally {
      setLoadingApply(false);
    }
  };

  const handleDownloadErros = () => {
    if (!preview?.records) return;
    const invalidos = preview.records.filter(r => !r.valid);
    if (!invalidos.length) return;
    const lines = ['linha,nome,email,erros'];
    invalidos.forEach(r => {
      const nome = (r.raw?.nome || '').replace(/"/g, '""');
      const email = (r.raw?.email || '').replace(/"/g, '""');
      const erros = (r.errors || []).join('; ').replace(/"/g, '""');
      lines.push(`${r.line_number},"${nome}","${email}","${erros}"`);
    });
    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `erros_${preview.intent}.csv`; a.click();
    URL.revokeObjectURL(url);
  };

  const currentStep = useMemo(() => {
    if (loadingAnalyze) return STEP_ANALYZE;
    if (preview) return STEP_REVIEW;
    if (arquivo) return STEP_UPLOAD;
    return STEP_UPLOAD;
  }, [loadingAnalyze, preview, arquivo]);

  return (
    <Box sx={{ p: 3 }}>
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            🧠 Importação Inteligente
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Importe listas de profissionais, equipe, horários e consultórios a partir de planilhas,
            PDFs ou CSVs. A IA identifica o tipo de conteúdo e valida cada registro.
          </Typography>
        </Box>
      </Stack>

      <Stepper activeStep={currentStep} sx={{ mb: 4 }}>
        <Step><StepLabel>1. Escolher arquivo</StepLabel></Step>
        <Step><StepLabel>2. Analisar com IA</StepLabel></Step>
        <Step><StepLabel>3. Revisar preview</StepLabel></Step>
        <Step><StepLabel>4. Aplicar</StepLabel></Step>
      </Stepper>

      {/* Card 1: Upload + Intent */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={5}>
            <FormControl fullWidth size="small">
              <InputLabel id="intent-label">Tipo de conteúdo</InputLabel>
              <Select
                labelId="intent-label"
                value={intentSelecionado}
                label="Tipo de conteúdo"
                onChange={(e) => setIntentSelecionado(e.target.value)}
                disabled={loadingOptions}
              >
                {intents.map(i => (
                  <MenuItem key={i.intent} value={i.intent}>
                    {i.icon} {i.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <Tooltip title="Se marcado, força o intent acima. Senão o agente detecta pelo conteúdo.">
              <FormControl fullWidth size="small">
                <Select
                  value={forceIntent ? 'sim' : 'nao'}
                  onChange={(e) => setForceIntent(e.target.value === 'sim')}
                >
                  <MenuItem value="nao">🔍 Auto-detectar</MenuItem>
                  <MenuItem value="sim">📌 Forçar intent</MenuItem>
                </Select>
              </FormControl>
            </Tooltip>
          </Grid>
          <Grid item xs={12} md={4}>
            <Button
              variant="contained" component="label" startIcon={<CloudUpload />}
              fullWidth disabled={loadingAnalyze}
            >
              {arquivo ? arquivo.name : 'Escolher arquivo'}
              <input type="file" hidden accept=".pdf,.xlsx,.xls,.csv,.docx,.doc,.txt"
                     onChange={handleFile} />
            </Button>
          </Grid>
        </Grid>

        {arquivo && (
          <Box sx={{ mt: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              {(arquivo.size / 1024).toFixed(1)} KB
            </Typography>
            <Button
              variant="outlined" onClick={handleAnalyze}
              startIcon={loadingAnalyze ? <CircularProgress size={16} /> : <Refresh />}
              disabled={loadingAnalyze}
            >
              {loadingAnalyze ? 'Analisando…' : 'Analisar com IA'}
            </Button>
            {arquivo && !loadingAnalyze && (
              <Button size="small" onClick={() => { setArquivo(null); setPreview(null); }}>
                Remover
              </Button>
            )}
          </Box>
        )}

        {loadingAnalyze && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress variant="determinate" value={progress} />
            <Typography variant="caption" color="text.secondary">
              {progress < 100 ? 'Lendo arquivo, extraindo e validando…' : 'Finalizando…'}
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Card 2: Preview */}
      {preview && (
        <Paper sx={{ p: 3 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
            <Box>
              <Typography variant="h6">
                Preview: {intents.find(i => i.intent === preview.intent)?.label || preview.intent}
                <Chip size="small" sx={{ ml: 1 }} label={`conf. ${(preview.intent_confianca * 100).toFixed(0)}%`} />
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {preview.filename} · {preview.total_registros} registro(s) ·{' '}
                {preview.validos} válido(s) · {preview.invalidos} com erro ·{' '}
                IA: {preview.ai_provider}/{preview.ai_model}
              </Typography>
            </Box>
            <Stack direction="row" spacing={1}>
              {preview.invalidos > 0 && (
                <Button size="small" startIcon={<Download />} onClick={handleDownloadErros}>
                  Baixar erros CSV
                </Button>
              )}
              <Button
                variant="contained" color="primary"
                onClick={handleApply}
                startIcon={loadingApply ? <CircularProgress size={16} /> : <CheckCircle />}
                disabled={loadingApply || preview.validos === 0}
              >
                {loadingApply ? 'Aplicando…' : `Aplicar ${preview.validos} válido(s)`}
              </Button>
            </Stack>
          </Stack>

          {Object.keys(preview.resumo_erros || {}).length > 0 && (
            <Alert severity="warning" sx={{ mb: 2 }} icon={<Warning />}>
              Resumo de erros:&nbsp;
              {Object.entries(preview.resumo_erros).map(([k, v]) => (
                <Chip key={k} size="small" label={`${k}: ${v}`} sx={{ mr: 0.5, mb: 0.5 }} />
              ))}
            </Alert>
          )}

          <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)} sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
            <Tab label={`✅ Válidos (${preview.validos})`} />
            <Tab label={`❌ Inválidos (${preview.invalidos})`} />
            <Tab label="🛈 Detalhes" />
          </Tabs>

          {activeTab === 0 && <PreviewTable records={preview.records.filter(r => r.valid)} />}
          {activeTab === 1 && <PreviewTable records={preview.records.filter(r => !r.valid)} showErrors />}
          {activeTab === 2 && <PreviewDetails preview={preview} />}
        </Paper>
      )}

      <Snackbar
        open={feedback.open}
        autoHideDuration={6000}
        onClose={() => setFeedback(f => ({ ...f, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity={feedback.severity} onClose={() => setFeedback(f => ({ ...f, open: false }))}>
          {feedback.text}
        </Alert>
      </Snackbar>
    </Box>
  );
};

// ----------------- Sub-componentes locais -----------------
const PreviewTable = ({ records, showErrors = false }) => {
  if (!records.length) {
    return (
      <Alert severity="info" sx={{ mt: 2 }}>
        Nenhum registro {showErrors ? 'com erro' : 'válido'} neste grupo.
      </Alert>
    );
  }
  // Detecta chaves do `raw` para colunas
  const sample = records[0].raw || {};
  const columns = Object.keys(sample);

  return (
    <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 480 }}>
      <Table size="small" stickyHeader>
        <TableHead>
          <TableRow>
            <TableCell>Linha</TableCell>
            {columns.map(c => <TableCell key={c}>{c}</TableCell>)}
            {showErrors && <TableCell>Erros</TableCell>}
          </TableRow>
        </TableHead>
        <TableBody>
          {records.map(r => (
            <TableRow key={r.line_number} hover>
              <TableCell>{r.line_number}</TableCell>
              {columns.map(c => (
                <TableCell key={c}>
                  {String(r.raw?.[c] ?? '').substring(0, 60)}
                </TableCell>
              ))}
              {showErrors && (
                <TableCell>
                  {r.errors?.map((e, i) => (
                    <Chip key={i} size="small" color="error" label={e.substring(0, 60)} sx={{ mr: 0.5, mb: 0.5 }} />
                  ))}
                </TableCell>
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

const PreviewDetails = ({ preview }) => (
  <Box>
    <Typography variant="subtitle2">Cabeçalhos detectados:</Typography>
    <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 2 }}>
      {(preview.headers_detectados || []).map(h => <Chip key={h} size="small" label={h} />)}
    </Stack>
    <Typography variant="subtitle2">Configuração da extração:</Typography>
    <Box component="pre" sx={{
      p: 2, bgcolor: 'grey.100', borderRadius: 1, fontSize: 12, overflow: 'auto',
    }}>
{JSON.stringify({
  intent: preview.intent,
  confianca: preview.intent_confianca,
  total: preview.total_registros,
  validos: preview.validos,
  invalidos: preview.invalidos,
  ai_provider: preview.ai_provider,
  ai_model: preview.ai_model,
  resumo_erros: preview.resumo_erros,
}, null, 2)}
    </Box>
  </Box>
);

export default IntelligentImporter;
