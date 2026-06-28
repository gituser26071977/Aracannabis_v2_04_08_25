/**
 * ModulosPage.js — Catálogo e gestão dos Módulos de Especialidade.
 *
 * Mostra:
 *   - Cards dos módulos do catálogo (ativos para o usuário)
 *   - Status da assinatura (sem / trial / active / cancelled)
 *   - Botões: Ativar Trial (14 dias) ou Assinar
 *   - Diálogo LGPD para aceitar/revogar consentimento
 *   - Lista das minhas assinaturas
 *   - Botão "Exportar dados (LGPD)"
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
  Container,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Stack,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Checkbox,
  Tooltip,
} from '@mui/material';
import {
  Science as ScienceIcon,
  Restaurant as RestaurantIcon,
  Psychology as PsychologyIcon,
  Favorite as FavoriteIcon,
  EnergySavingsLeaf as LeafIcon,
  Extension as ExtensionIcon,
  CheckCircle as CheckCircleIcon,
  HourglassBottom as HourglassIcon,
  EventBusy as EventBusyIcon,
  Download as DownloadIcon,
  VerifiedUser as LgpdIcon,
} from '@mui/icons-material';
import modulosService from '../services/modulosService';
import useConfirm from '../hooks/useConfirm';

// Mapeamento slug → componente de ícone MUI
const ICONES = {
  'eco': LeafIcon,
  'restaurant': RestaurantIcon,
  'psychology': PsychologyIcon,
  'favorite': FavoriteIcon,
  'science': ScienceIcon,
  'dashboard': ExtensionIcon,
};

function IconBySlug({ slug }) {
  const Comp = ICONES[slug] || ExtensionIcon;
  return <Comp fontSize="medium" />;
}

const statusChip = (a) => {
  if (!a) return <Chip size="small" label="Não assinado" variant="outlined" />;
  if (a.status === 'trial')
    return <Chip size="small" color="info" icon={<HourglassIcon />} label={`Trial (${a.dias_restantes}d)`} />;
  if (a.status === 'active')
    return <Chip size="small" color="success" icon={<CheckCircleIcon />} label={`Ativo (${a.dias_restantes}d)`} />;
  if (a.status === 'cancelled')
    return <Chip size="small" color="warning" label="Cancelado" />;
  return <Chip size="small" color="default" icon={<EventBusyIcon />} label={a.status} />;
};

const ModulosPage = () => {
  const { confirm, ConfirmDialog } = useConfirm();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [catalogo, setCatalogo] = useState([]);
  const [minhas, setMinhas] = useState([]);
  const [politicaVersao, setPoliticaVersao] = useState('v1');
  const [info, setInfo] = useState(null);
  const [consentDialog, setConsentDialog] = useState(null); // {slug, acao: 'trial'|'checkout'}
  const [consentChecked, setConsentChecked] = useState(false);
  const [acting, setActing] = useState(false);

  const carregar = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [cat, min] = await Promise.all([
        modulosService.listarCatalogo(),
        modulosService.listarMinhas(),
      ]);
      setCatalogo(cat.modulos || []);
      setPoliticaVersao(cat.politica_versao || 'v1');
      setMinhas(min.assinaturas || []);
    } catch (err) {
      setError(err.message || 'Erro ao carregar módulos');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { carregar(); }, [carregar]);

  const handleAtivarClick = (slug) => {
    setConsentDialog({ slug, acao: 'trial' });
    setConsentChecked(false);
  };
  const handleAssinarClick = (slug) => {
    setConsentDialog({ slug, acao: 'checkout' });
    setConsentChecked(false);
  };

  const executarAcao = async () => {
    if (!consentDialog) return;
    setActing(true);
    setInfo(null);
    try {
      if (consentDialog.acao === 'trial') {
        const r = await modulosService.ativarTrial(consentDialog.slug, consentChecked);
        setInfo({ tipo: 'success', msg: r.message || `Trial ativado (${r.trial_dias} dias).` });
      } else {
        const r = await modulosService.iniciarCheckout(consentDialog.slug, consentChecked);
        if (r.init_point) {
          window.open(r.init_point, '_blank', 'noopener');
          setInfo({ tipo: 'info', msg: 'Abrimos o link de pagamento em uma nova aba.' });
        } else {
          setInfo({ tipo: 'info', msg: 'Checkout criado.' });
        }
      }
      setConsentDialog(null);
      await carregar();
    } catch (err) {
      setInfo({ tipo: 'error', msg: err.message || 'Falha na operação.' });
    } finally {
      setActing(false);
    }
  };

  const handleRevogar = async (slug) => {
    const ok = await confirm({
      title: 'Revogar consentimento?',
      message: `Esta ação desativará o módulo "${slug}" e revogará o consentimento LGPD. Você pode reativar depois.`,
      confirmLabel: 'Revogar',
      destructive: true,
    });
    if (!ok) return;
    try {
      const r = await modulosService.revogarConsentimento(slug);
      setInfo({ tipo: 'success', msg: r.message || 'Consentimento revogado.' });
      await carregar();
    } catch (err) {
      setInfo({ tipo: 'error', msg: err.message || 'Erro ao revogar.' });
    }
  };

  const handleExportarLgpd = async () => {
    try {
      const data = await modulosService.exportarLgpd();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `modulos_lgpd_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setInfo({ tipo: 'success', msg: 'Exportação LGPD gerada.' });
    } catch (err) {
      setInfo({ tipo: 'error', msg: err.message || 'Erro ao exportar.' });
    }
  };

  if (loading) {
    return (
      <Container sx={{ py: 6, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <>
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
        <ExtensionIcon color="primary" />
        <Typography variant="h4" fontWeight={700}>Módulos de Especialidade</Typography>
      </Stack>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Ative módulos complementares com 14 dias de trial gratuito. Após o trial, mantenha o
        acesso por uma assinatura mensal. Os dados pessoais são tratados conforme a LGPD —
        termo versão <strong>{politicaVersao}</strong>.
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {info && (
        <Alert severity={info.tipo} sx={{ mb: 2 }} onClose={() => setInfo(null)}>
          {info.msg}
        </Alert>
      )}

      <Grid container spacing={2}>
        {catalogo.map((m) => {
          const ass = m.minha_assinatura;
          const isBase = m.slug === 'base';
          return (
            <Grid item xs={12} sm={6} md={4} key={m.slug}>
              <Card
                elevation={3}
                sx={{
                  borderTop: `4px solid ${m.cor || '#0d7377'}`,
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                    <Box sx={{ color: m.cor || 'primary.main' }}>
                      <IconBySlug slug={m.icone || m.slug} />
                    </Box>
                    <Typography variant="h6" fontWeight={700}>{m.nome}</Typography>
                  </Stack>
                  <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
                    {statusChip(ass)}
                    {m.preco_mensal > 0 && (
                      <Chip
                        size="small"
                        variant="outlined"
                        label={`R$ ${m.preco_mensal.toFixed(2).replace('.', ',')}/mês`}
                      />
                    )}
                    {isBase && <Chip size="small" color="primary" label="Incluso no plano" />}
                    {m.plano_minimo_slug && m.plano_minimo_slug !== 'basico' && (
                      <Tooltip title={`Requer plano ${m.plano_minimo_slug}`}>
                        <Chip size="small" label={`≥ ${m.plano_minimo_slug}`} variant="outlined" />
                      </Tooltip>
                    )}
                  </Stack>
                  <Typography variant="body2" color="text.secondary">
                    {m.descricao_curta || m.descricao}
                  </Typography>
                </CardContent>
                {!isBase && (
                  <CardActions sx={{ p: 2, pt: 0 }}>
                    {(!ass || ass.status === 'cancelled' || !ass.acesso_ativo) && (
                      <>
                        <Button
                          variant="outlined"
                          color="primary"
                          onClick={() => handleAtivarClick(m.slug)}
                          disabled={acting}
                        >
                          Ativar Trial (14d)
                        </Button>
                        {m.preco_mensal > 0 && (
                          <Button
                            variant="contained"
                            color="primary"
                            onClick={() => handleAssinarClick(m.slug)}
                            disabled={acting}
                          >
                            Assinar
                          </Button>
                        )}
                      </>
                    )}
                    {ass && ass.acesso_ativo && (
                      <Button
                        color="warning"
                        variant="text"
                        size="small"
                        onClick={() => handleRevogar(m.slug)}
                      >
                        Revogar consentimento
                      </Button>
                    )}
                  </CardActions>
                )}
              </Card>
            </Grid>
          );
        })}
      </Grid>

      <Divider sx={{ my: 4 }} />

      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
        <Stack direction="row" alignItems="center" spacing={1}>
          <LgpdIcon color="primary" />
          <Typography variant="h6">Suas assinaturas e LGPD</Typography>
        </Stack>
        <Button startIcon={<DownloadIcon />} variant="outlined" onClick={handleExportarLgpd}>
          Exportar meus dados (LGPD)
        </Button>
      </Stack>

      {minhas.length === 0 ? (
        <Alert severity="info">Você ainda não ativou nenhum módulo complementar.</Alert>
      ) : (
        <Grid container spacing={1}>
          {minhas.map((a) => (
            <Grid item xs={12} sm={6} md={4} key={a.id}>
              <Card variant="outlined">
                <CardContent>
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Typography fontWeight={600}>{a.modulo?.nome || a.modulo_id}</Typography>
                    {statusChip(a)}
                  </Stack>
                  <Typography variant="caption" color="text.secondary">
                    {a.trial_expira_em && `Trial expira em ${new Date(a.trial_expira_em).toLocaleDateString('pt-BR')}`}
                    {a.expira_em && !a.trial_expira_em && `Expira em ${new Date(a.expira_em).toLocaleDateString('pt-BR')}`}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Diálogo de consentimento LGPD */}
      <Dialog open={Boolean(consentDialog)} onClose={() => !acting && setConsentDialog(null)}>
        <DialogTitle>Termo de Consentimento (LGPD)</DialogTitle>
        <DialogContent dividers>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Para ativar este módulo você concorda com o tratamento dos seus dados
            pessoais conforme a Lei Geral de Proteção de Dados. Versão do termo:{' '}
            <strong>{politicaVersao}</strong>. Você pode revogar este consentimento a
            qualquer momento — isso cancelará o acesso ao módulo e manterá o registro
            da revogação.
          </Typography>
          <FormControlLabel
            control={
              <Checkbox
                checked={consentChecked}
                onChange={(e) => setConsentChecked(e.target.checked)}
              />
            }
            label="Li e aceito o termo de consentimento."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConsentDialog(null)} disabled={acting}>Cancelar</Button>
          <Button
            variant="contained"
            disabled={!consentChecked || acting}
            onClick={executarAcao}
          >
            {acting ? <CircularProgress size={18} /> : 'Confirmar'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
    <ConfirmDialog />
    </>
  );
};

export default ModulosPage;
