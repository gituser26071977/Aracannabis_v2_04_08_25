import React, { useState, useEffect } from 'react';
import {
    Box, Typography, Button, Paper, Table, TableBody, TableCell,
    TableContainer, TableHead, TableRow, IconButton, Dialog,
    DialogTitle, DialogContent, DialogContentText, DialogActions,
    TextField, CircularProgress, Alert, Grid, Tabs, Tab,
    Card, CardContent, Divider, Tooltip
} from '@mui/material';
import ContextualTip from './ContextualTip';
import { Print, PictureAsPdf, Add, Description, AutoAwesome, CheckCircle } from '@mui/icons-material';
import api from '../services/api';

const PrescriptionPanel = ({ patientId }) => {
    const [prescricoes, setPrescricoes] = useState([]);
    const [loading, setLoading] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [openDialog, setOpenDialog] = useState(false);
    const [observacoes, setObservacoes] = useState('');
    const [message, setMessage] = useState({ type: '', text: '' });

    // IA States
    const [tabVal, setTabVal] = useState(0);
    const [textoLivre, setTextoLivre] = useState('');
    const [processandoIA, setProcessandoIA] = useState(false);
    const [medsDaIA, setMedsDaIA] = useState(null);
    const [examesDaIA, setExamesDaIA] = useState(null);

    useEffect(() => {
        loadPrescricoes();
    }, [patientId]);

    const loadPrescricoes = async () => {
        setLoading(true);
        try {
            const response = await api.get(`/prescricoes/paciente/${patientId}`);
            setPrescricoes(response.data);
        } catch (error) {
            if(process.env.NODE_ENV!=='production')console.error("Erro ao carregar prescrições", error);
        } finally {
            setLoading(false);
        }
    };

    const handleProcessarIA = async () => {
        if (!textoLivre.trim()) return;
        setProcessandoIA(true);
        try {
            const response = await api.post('/prescricoes/assistente', { texto_livre: textoLivre });
            if (response.data.success) {
                setMedsDaIA(response.data.medicamentos);
                setExamesDaIA(response.data.exames);
            }
        } catch (err) {
            if(process.env.NODE_ENV!=='production')console.error(err);
            setMessage({ type: 'error', text: 'Falha na comunicação com a IA.' });
        } finally {
            setProcessandoIA(false);
        }
    };

    const handleGerarPrescricao = async () => {
        setGenerating(true);
        setMessage({ type: '', text: '' });

        const payload = {
            paciente_id: patientId,
            observacoes: observacoes
        };

        // Se a Tab=1 (Ditado IA) e tivermos meds parseados, mandamos eles para criar as Dosagens inline
        if (tabVal === 1) {
            if (medsDaIA && medsDaIA.length > 0) {
                payload.novos_medicamentos = medsDaIA;
            }
            if (examesDaIA && examesDaIA.length > 0) {
                payload.novos_exames = examesDaIA;
            }
        }

        try {
            const response = await api.post('/prescricoes/gerar', payload);

            if (response.data.success) {
                setMessage({ type: 'success', text: 'Prescrição gerada com sucesso!' });
                setOpenDialog(false);
                setObservacoes('');
                setTextoLivre('');
                setMedsDaIA(null);
                setExamesDaIA(null);
                setTabVal(0);
                loadPrescricoes();
                window.open(`${api.defaults.baseURL}/prescricoes/${response.data.data.id}/download`, '_blank');
            }
        } catch (error) {
            if(process.env.NODE_ENV!=='production')console.error(error);
            setMessage({ type: 'error', text: 'Erro ao gerar prescrição.' });
        } finally {
            setGenerating(false);
        }
    };

    const handleDownload = (id) => {
        window.open(`${api.defaults.baseURL}/prescricoes/${id}/download`, '_blank');
    };

    return (
        <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h6">Histórico de Prescrições</Typography>
                <Button
                    variant="contained"
                    color="primary"
                    startIcon={<Add />}
                    onClick={() => {
                        setObservacoes('');
                        setTextoLivre('');
                        setMedsDaIA(null);
                        setOpenDialog(true);
                    }}
                >
                    Nova Prescrição
                </Button>
            </Box>

            {message.text && (
                <Alert severity={message.type} sx={{ mb: 2 }}>{message.text}</Alert>
            )}

            {!loading && (
                <ContextualTip
                    severity="tip"
                    storageKey="prescricao_ia_ditado"
                    title="💡 Dica IA:"
                    sx={{ mb: 2 }}
                >
                    Dentro de "Nova Prescrição" você pode ditar a consulta em texto livre e a IA extrai medicamentos + exames automaticamente (modo Consultor).
                </ContextualTip>
            )}

            {loading ? (
                <CircularProgress />
            ) : prescricoes.length === 0 ? (
                <Alert severity="info" icon={<Description />}>
                    Nenhuma prescrição gerada para este paciente. Clique em "Nova Prescrição" para gerar um documento PDF com as dosagens atuais.
                </Alert>
            ) : (
                <TableContainer component={Paper} elevation={2}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>Data Emissão</TableCell>
                                <TableCell>Observações</TableCell>
                                <TableCell align="center">Ações</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {prescricoes.map((p) => (
                                <TableRow key={p.id}>
                                    <TableCell>{new Date(p.data_emissao).toLocaleDateString()} {new Date(p.data_emissao).toLocaleTimeString()}</TableCell>
                                    <TableCell>{p.observacoes || '-'}</TableCell>
                                    <TableCell align="center">
                                        <Tooltip title="Baixar PDF da prescrição">
                                            <IconButton color="primary" onClick={() => handleDownload(p.id)} aria-label="Baixar PDF">
                                                <PictureAsPdf />
                                            </IconButton>
                                        </Tooltip>
                                        <Tooltip title="Imprimir prescrição">
                                            <IconButton color="secondary" onClick={() => handleDownload(p.id)} aria-label="Imprimir prescrição">
                                                <Print />
                                            </IconButton>
                                        </Tooltip>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            )}

            {/* Dialog Nova Prescrição */}
            <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
                <DialogTitle>Elaborar Prescrição Inteligente</DialogTitle>
                <DialogContent sx={{ minHeight: '400px' }}>
                    <Tabs value={tabVal} onChange={(e, val) => setTabVal(val)} sx={{ mb: 2, borderBottom: 1, borderColor: 'divider' }}>
                        <Tab label="Receita Padrão (Base de Exames)" />
                        <Tab label="Ditado Livre / IA" icon={<AutoAwesome />} iconPosition="start" />
                    </Tabs>

                    {tabVal === 0 && (
                        <Box mt={2}>
                            <DialogContentText sx={{ mb: 3 }}>
                                O sistema exportará para o PDF os medicamentos que já estão fixos e registrados no painel de "Dosagens" atuais deste paciente. O algoritmo formatará as margens, cabeçalho da sua clinica e assinaturas automaticamente.
                            </DialogContentText>
                            <TextField
                                label="Observações Gerais do PDF (Opcional)"
                                fullWidth multiline rows={4}
                                variant="outlined"
                                value={observacoes}
                                onChange={(e) => setObservacoes(e.target.value)}
                                placeholder="Ex: Próxima consulta em 30 dias..."
                            />
                        </Box>
                    )}

                    {tabVal === 1 && (
                        <Box mt={2}>
                            <DialogContentText sx={{ mb: 2 }}>
                                <strong>Formatação Automática:</strong> Escreva sua orientação médica livremente. A IA processará o texto e estruturará a receita no PDF. Caso seu "Modo Consultor" esteja ativo nas configurações da sua conta, a IA poderá sugerir posologias otimizadas baseadas nesses sintomas.
                            </DialogContentText>
                            <TextField
                                label="Ditado Clínico ou Medicações Livres"
                                fullWidth multiline rows={4}
                                variant="outlined"
                                value={textoLivre}
                                onChange={(e) => setTextoLivre(e.target.value)}
                                placeholder="Paciente com insônia relatando despertares. Receitar 5 gotas de CBD pela manhã e uso de THC óleo 20% 5 gotas ao dormir..."
                                sx={{ mb: 2 }}
                            />
                            <Button
                                variant="contained"
                                color="secondary"
                                startIcon={processandoIA ? <CircularProgress size={20} color="inherit" /> : <AutoAwesome />}
                                onClick={handleProcessarIA}
                                disabled={processandoIA || textoLivre.trim().length === 0}
                            >
                                Processar com IA
                            </Button>

                            {medsDaIA && medsDaIA.length > 0 && medsDaIA.map((med, idx) => (
                                <Card key={idx} sx={{ mb: 2, bgcolor: 'background.default', border: '1px solid #e0e0e0' }}>
                                    <CardContent sx={{ pb: 1 }}>
                                        <Typography variant="body1" fontWeight="bold"><CheckCircle color="success" sx={{ fontSize: 16, mr: 1, verticalAlign: 'text-bottom' }} /> {med.nome_medicamento}</Typography>
                                        <Grid container spacing={1} sx={{ mt: 1 }}>
                                            <Grid item xs={12} sm={4}>
                                                <Typography variant="caption" color="text.secondary">Uso / Via</Typography>
                                                <Typography variant="body2">{med.via_administracao}</Typography>
                                            </Grid>
                                            <Grid item xs={12} sm={8}>
                                                <Typography variant="caption" color="text.secondary">Posologia</Typography>
                                                <Typography variant="body2">{med.posologia_texto}</Typography>
                                            </Grid>
                                            {med.instrucoes && (
                                                <Grid item xs={12}>
                                                    <Typography variant="caption" color="text.secondary">Instruções Extras</Typography>
                                                    <Typography variant="body2"><i>{med.instrucoes}</i></Typography>
                                                </Grid>
                                            )}
                                        </Grid>
                                    </CardContent>
                                </Card>
                            ))}

                            {examesDaIA && examesDaIA.length > 0 && (
                                <Box mt={3} mb={2}>
                                    <Typography variant="subtitle1" fontWeight="bold" color="primary">Exames Complementares Detectados:</Typography>
                                    <Divider sx={{ mb: 2 }} />
                                    <Card sx={{ bgcolor: 'action.hover', border: '1px dashed', borderColor: 'divider' }}>
                                        <CardContent>
                                            <Grid container spacing={1}>
                                                {examesDaIA.map((exame, idx) => (
                                                    <Grid item xs={12} sm={6} key={idx}>
                                                        <Typography variant="body2"><CheckCircle color="info" sx={{ fontSize: 14, mr: 1, verticalAlign: 'text-bottom' }} /> {exame}</Typography>
                                                    </Grid>
                                                ))}
                                            </Grid>
                                        </CardContent>
                                    </Card>
                                </Box>
                            )}

                            <Alert severity="info" sx={{ mt: 2 }}>
                                Ao clicar abaixo, os dados extraídos serão salvos fisicamente no prontuário do paciente. O PDF da Prescrição será gerado mesclando suas configurações, e as solicitações de exame entrarão no painel de solicitações e poderão ser impressas a qualquer momento.
                            </Alert>
                        </Box>
                    )}
                </DialogContent>
                <DialogActions sx={{ p: 3 }}>
                    <Button onClick={() => setOpenDialog(false)} color="inherit">
                        Cancelar
                    </Button>
                    <Button
                        onClick={handleGerarPrescricao}
                        color="primary"
                        variant="contained"
                        disabled={generating || (tabVal === 1 && (!medsDaIA && !examesDaIA))}
                        startIcon={generating ? <CircularProgress size={20} color="inherit" /> : <Print />}
                    >
                        Gerar Prescrição e Assinar
                    </Button>
                </DialogActions>
            </Dialog>
        </Box >
    );
};

export default PrescriptionPanel;
