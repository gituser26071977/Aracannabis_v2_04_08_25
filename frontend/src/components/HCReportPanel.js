import React, { useState } from 'react';
import {
    Box,
    Paper,
    Typography,
    Button,
    TextField,
    Alert,
    CircularProgress,
    Card,
    CardContent,
    Divider,
    List,
    ListItem,
    ListItemText,
    ListItemIcon
} from '@mui/material';
import {
    Description as FileIcon,
    Gavel as LawIcon,
    AutoAwesome as AIIcon,
    Download as DownloadIcon
} from '@mui/icons-material';
import api from '../services/api';

const HCReportPanel = ({ patientId }) => {
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState('');
    const [error, setError] = useState('');
    const [justificativa, setJustificativa] = useState('');
    const [generatedFile, setGeneratedFile] = useState(null);

    const handleGenerateReport = async () => {
        setLoading(true);
        setError('');
        setSuccess('');
        setGeneratedFile(null);

        try {
            const response = await api.post('/hc-report/generate', {
                paciente_id: patientId,
                justificativa_medica: justificativa
            });

            if (response.data.success) {
                setSuccess('Laudo de Habeas Corpus gerado com sucesso!');
                setGeneratedFile({
                    filename: response.data.filename,
                    url: response.data.url
                });
            }
        } catch (err) {
            if(process.env.NODE_ENV!=='production')console.error('Erro ao gerar laudo:', err);
            setError(err.response?.data?.error || 'Erro ao gerar o laudo. Verifique se há dados clínicos suficientes.');
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = () => {
        if (generatedFile) {
            const link = document.createElement('a');
            link.href = `${api.defaults.baseURL}/hc-report/download/${generatedFile.filename}`;
            link.setAttribute('download', generatedFile.filename);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    };

    return (
        <Box sx={{ width: '100%', maxWidth: 800, margin: '0 auto' }}>
            <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                    <LawIcon color="primary" sx={{ fontSize: 40, mr: 2 }} />
                    <Box>
                        <Typography variant="h5" component="h2" gutterBottom>
                            Laudo para Habeas Corpus
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                            Geração de documento pericial para instrução de processos de Salvo Conduto para auto-cultivo.
                        </Typography>
                    </Box>
                </Box>

                <Alert severity="info" sx={{ mb: 4 }}>
                    Este módulo utiliza <strong>Inteligência Artificial</strong> (GLM-4) para analisar o histórico clínico,
                    evoluções e dosagens do paciente, redigindo uma justificativa médica robusta demonstrando a
                    imprescindibilidade do tratamento.
                </Alert>

                <Box sx={{ mb: 4 }}>
                    <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center' }}>
                        <AIIcon fontSize="small" sx={{ mr: 1, color: 'secondary.main' }} />
                        Justificativa Médica (Opcional)
                    </Typography>
                    <Typography variant="caption" display="block" sx={{ mb: 1, color: 'text.secondary' }}>
                        A IA irá gerar uma justificativa baseada nos dados. Se desejar adicionar observações específicas ou manuais, digite abaixo.
                    </Typography>
                    <TextField
                        fullWidth
                        multiline
                        rows={4}
                        variant="outlined"
                        placeholder="Ex: Paciente refratário a opióides, apresentou melhora significativa na qualidade do sono e redução de 80% nas dores..."
                        value={justificativa}
                        onChange={(e) => setJustificativa(e.target.value)}
                    />
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
                    <Button
                        variant="contained"
                        color="primary"
                        size="large"
                        onClick={handleGenerateReport}
                        disabled={loading}
                        startIcon={loading ? <CircularProgress size={24} color="inherit" /> : <AIIcon />}
                        sx={{ px: 4, py: 1.5, borderRadius: 2 }}
                    >
                        {loading ? 'Analisando Dados e Gerando Laudo...' : 'Gerar Laudo com IA'}
                    </Button>
                </Box>

                {error && (
                    <Alert severity="error" sx={{ mt: 2 }}>
                        {error}
                    </Alert>
                )}

                {success && (
                    <Box sx={{ mt: 4, animation: 'fadeIn 0.5s ease-in' }}>
                        <Alert severity="success" sx={{ mb: 2 }}>
                            {success}
                        </Alert>

                        <Card variant="outlined" sx={{ bgcolor: 'grey.50' }}>
                            <CardContent>
                                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                                    Documento Gerado
                                </Typography>
                                <List>
                                    <ListItem>
                                        <ListItemIcon>
                                            <FileIcon color="error" />
                                        </ListItemIcon>
                                        <ListItemText
                                            primary={generatedFile?.filename}
                                            secondary="PDF - Pronto para assinatura digital"
                                        />
                                        <Button
                                            variant="outlined"
                                            color="primary"
                                            startIcon={<DownloadIcon />}
                                            onClick={handleDownload}
                                        >
                                            Baixar PDF
                                        </Button>
                                    </ListItem>
                                </List>
                            </CardContent>
                        </Card>
                    </Box>
                )}
            </Paper>
        </Box>
    );
};

export default HCReportPanel;
