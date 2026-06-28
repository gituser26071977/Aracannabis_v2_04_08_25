import React, { useState } from 'react';
import {
    Container, Paper, Typography, Box, Button, Table, TableBody, TableCell,
    TableContainer, TableHead, TableRow, TextField, IconButton, CircularProgress,
    Alert, Grid, LinearProgress
} from '@mui/material';
import { CloudUpload, Delete, CheckCircle, Save, Info } from '@mui/icons-material';
import { Chip, Tooltip } from '@mui/material';
import api from '../services/api';

const BatchImportPage = () => {
    const [files, setFiles] = useState([]);
    const [analyzedData, setAnalyzedData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [importing, setImporting] = useState(false);
    const [successMsg, setSuccessMsg] = useState('');
    const [errorMsg, setErrorMsg] = useState('');

    const handleFileChange = (event) => {
        const newFiles = Array.from(event.target.files);
        setFiles([...files, ...newFiles]);
    };

    const removeFile = (index) => {
        const newFiles = [...files];
        newFiles.splice(index, 1);
        setFiles(newFiles);
    };
    const [progress, setProgress] = useState(0);
    const [statusMessage, setStatusMessage] = useState('');

    const pollJobStatus = async (jobId) => {
        const interval = setInterval(async () => {
            try {
                const response = await api.get(`/import-agent/status/${jobId}`);
                const job = response.data;

                if (job.status === 'completed') {
                    clearInterval(interval);

                    const batchItems = job.results.map(item => ({
                        ...item,
                        id: Date.now() + Math.random()
                    }));

                    setAnalyzedData(prev => [...prev, ...batchItems]);
                    setLoading(false);
                    setSuccessMsg(`Análise concluída! ${batchItems.length} documentos processados.`);
                    setProgress(0);
                } else if (job.status === 'failed') {
                    clearInterval(interval);
                    setLoading(false);
                    setErrorMsg(`Erro no processamento: ${job.error}`);
                    setProgress(0);
                } else {
                    // Processing
                    if (job.total > 0) {
                        const percent = Math.round((job.processed / job.total) * 100);
                        setProgress(percent);
                        setStatusMessage(`Processando ${job.processed}/${job.total} arquivos...`);
                    }
                }
            } catch (err) {
                if(process.env.NODE_ENV!=='production')console.error("Erro no polling:", err);
                clearInterval(interval);
                setLoading(false);
                setErrorMsg("Perda de conexão com o progresso.");
            }
        }, 2000);
    };

    const handleAnalyze = async () => {
        setLoading(true);
        setAnalyzedData([]);
        setErrorMsg('');
        setSuccessMsg('');
        setProgress(0);
        setStatusMessage('Enviando arquivos...');

        const results = [];

        // Processar arquivos um por um
        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await api.post('/import-agent/analyze', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });

                if (response.data.success) {
                    if (response.data.is_async) {
                        // Iniciar Polling
                        setStatusMessage('Processamento em background iniciado...');
                        await pollJobStatus(response.data.job_id);
                        return; // O polling vai finalizar o loading
                    } else if (response.data.is_batch && Array.isArray(response.data.data)) {
                        // (Fallback para caso síncrono que retorne lista)
                        const batchItems = response.data.data.map(item => ({
                            ...item,
                            id: Date.now() + Math.random()
                        }));
                        results.push(...batchItems);
                    } else {
                        // Arquivo único
                        results.push({
                            ...response.data.data,
                            original_filename: file.name,
                            id: Date.now() + Math.random()
                        });
                    }
                }
            } catch (err) {
                if(process.env.NODE_ENV!=='production')console.error(`Erro ao analisar ${file.name}`, err);
                results.push({
                    nome: '',
                    observacoes: `Falha na análise de ${file.name}: ${err.response?.data?.error || err.message}`,
                    original_filename: file.name,
                    id: Date.now() + Math.random(),
                    error: true
                });
            }
        }

        setAnalyzedData(results);
        setLoading(false);
    };

    const handleDataChange = (index, field, value) => {
        const newData = [...analyzedData];
        newData[index][field] = value;
        setAnalyzedData(newData);
    };

    const handleImport = async () => {
        setImporting(true);
        try {
            const response = await api.post('/import-agent/batch-create', {
                patients: analyzedData
            });

            if (response.data.success) {
                setSuccessMsg(`Importação concluída! ${response.data.created_count} pacientes criados.`);
                setAnalyzedData([]); // Limpar lista
                setFiles([]); // Limpar arquivos
            } else {
                setErrorMsg('Erro na importação: ' + response.data.errors.join(', '));
            }
        } catch (err) {
            setErrorMsg('Erro ao conectar com servidor de importação.');
            if(process.env.NODE_ENV!=='production')console.error(err);
        } finally {
            setImporting(false);
        }
    };

    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            <Paper elevation={3} sx={{ p: 4 }}>
                <Typography variant="h4" gutterBottom>
                    Agente Cadastrador Inteligente
                </Typography>
                <Typography variant="body1" color="text.secondary" paragraph>
                    Importe prescrições ou documentos (PDF/Imagem) para cadastrar múltiplos pacientes automaticamente via OCR/IA.
                </Typography>

                {/* Upload Area */}
                <Box sx={{ border: '2px dashed #ccc', p: 4, textAlign: 'center', mb: 4, borderRadius: 2 }}>
                    <Grid container spacing={2} justifyContent="center">
                        <Grid item>
                            <input
                                accept="application/pdf,image/*,.zip,application/zip"
                                style={{ display: 'none' }}
                                id="raised-button-file"
                                multiple
                                type="file"
                                onChange={handleFileChange}
                            />
                            <label htmlFor="raised-button-file">
                                <Button variant="contained" component="span" startIcon={<CloudUpload />}>
                                    Selecionar Arquivos
                                </Button>
                            </label>
                        </Grid>
                        <Grid item>
                            <input
                                style={{ display: 'none' }}
                                id="directory-upload"
                                type="file"
                                webkitdirectory=""
                                directory=""
                                multiple
                                onChange={handleFileChange}
                            />
                            <label htmlFor="directory-upload">
                                <Button variant="outlined" component="span" startIcon={<CloudUpload />}>
                                    Selecionar Pasta (OneDrive Local)
                                </Button>
                            </label>
                        </Grid>
                    </Grid>
                    <Typography variant="caption" display="block" sx={{ mt: 2 }}>
                        {files.length} arquivos selecionados
                    </Typography>
                </Box>

                {files.length > 0 && analyzedData.length === 0 && (
                    <Box sx={{ mb: 4 }}>
                        <Typography variant="h6" gutterBottom>Arquivos para Análise:</Typography>
                        <Grid container spacing={1}>
                            {files.map((f, i) => (
                                <Grid item key={i}>
                                    <Box sx={{ bgcolor: '#eee', p: 1, borderRadius: 1, display: 'flex', alignItems: 'center' }}>
                                        {f.name}
                                        <IconButton size="small" onClick={() => removeFile(i)}><Delete fontSize="small" /></IconButton>
                                    </Box>
                                </Grid>
                            ))}
                        </Grid>
                        <Button
                            variant="contained"
                            color="secondary"
                            fullWidth
                            sx={{ mt: 2 }}
                            onClick={handleAnalyze}
                            disabled={loading}
                        >
                            {loading ? <CircularProgress size={24} /> : 'Iniciar Análise Inteligente'}
                        </Button>

                        {loading && (
                            <Box sx={{ width: '100%', mt: 2 }}>
                                <LinearProgress variant={progress > 0 ? "determinate" : "indeterminate"} value={progress} />
                                <Typography variant="caption" color="text.secondary">{statusMessage || 'Analisando documentos...'}</Typography>
                            </Box>
                        )}
                    </Box>
                )}

                {/* Results Table */}
                {analyzedData.length > 0 && (
                    <Box>
                        <Typography variant="h6" gutterBottom color="primary">
                            Pré-visualização e Correção (Verifique os dados extraídos)
                        </Typography>

                        {successMsg && <Alert severity="success" sx={{ mb: 2 }}>{successMsg}</Alert>}
                        {errorMsg && <Alert severity="error" sx={{ mb: 2 }}>{errorMsg}</Alert>}

                        <TableContainer sx={{ maxHeight: 600 }}>
                            <Table stickyHeader size="small">
                                <TableHead>
                                    <TableRow>
                                        <TableCell>Arquivo</TableCell>
                                        <TableCell>Nome do Paciente</TableCell>
                                        <TableCell>Nascimento</TableCell>
                                        <TableCell>CPF / RG</TableCell>
                                        <TableCell>Endereço / Contato</TableCell>
                                        <TableCell>Associação</TableCell>
                                        <TableCell>Diagnóstico / Medicamentos</TableCell>
                                        <TableCell>Confiança</TableCell>
                                        <TableCell>Ações</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {analyzedData.map((row, index) => (
                                        <TableRow key={row.id} sx={row.error ? { bgcolor: '#ffebee' } : {}}>
                                            <TableCell>{row.original_filename}</TableCell>
                                            <TableCell>
                                                <TextField
                                                    value={row.nome || ''}
                                                    onChange={(e) => handleDataChange(index, 'nome', e.target.value)}
                                                    size="small"
                                                    error={!row.nome}
                                                    fullWidth
                                                />
                                            </TableCell>
                                            <TableCell>
                                                <TextField
                                                    value={row.data_nascimento || ''}
                                                    onChange={(e) => handleDataChange(index, 'data_nascimento', e.target.value)}
                                                    size="small"
                                                    placeholder="YYYY-MM-DD"
                                                    sx={{ width: 140 }}
                                                />
                                            </TableCell>
                                            <TableCell>
                                                <TextField
                                                    value={row.cpf || ''}
                                                    onChange={(e) => handleDataChange(index, 'cpf', e.target.value)}
                                                    size="small"
                                                    placeholder="CPF"
                                                    sx={{ width: 130, mb: 1 }}
                                                />
                                                <TextField
                                                    value={row.rg || ''}
                                                    onChange={(e) => handleDataChange(index, 'rg', e.target.value)}
                                                    size="small"
                                                    placeholder="RG"
                                                    sx={{ width: 130 }}
                                                />
                                            </TableCell>
                                            <TableCell>
                                                <TextField
                                                    value={row.endereco || ''}
                                                    onChange={(e) => handleDataChange(index, 'endereco', e.target.value)}
                                                    size="small"
                                                    placeholder="Endereço"
                                                    multiline
                                                    rows={2}
                                                    fullWidth
                                                    sx={{ mb: 1 }}
                                                />
                                                <Box display="flex" gap={1}>
                                                    <TextField
                                                        value={row.telefone || ''}
                                                        onChange={(e) => handleDataChange(index, 'telefone', e.target.value)}
                                                        size="small"
                                                        placeholder="Tel"
                                                    />
                                                    <TextField
                                                        value={row.email || ''}
                                                        onChange={(e) => handleDataChange(index, 'email', e.target.value)}
                                                        size="small"
                                                        placeholder="Email"
                                                    />
                                                </Box>
                                            </TableCell>
                                            <TableCell>
                                                <TextField
                                                    value={row.associacao || ''}
                                                    onChange={(e) => handleDataChange(index, 'associacao', e.target.value)}
                                                    size="small"
                                                    placeholder="Associação"
                                                />
                                            </TableCell>
                                            <TableCell>
                                                <TextField
                                                    value={row.diagnostico || ''}
                                                    onChange={(e) => handleDataChange(index, 'diagnostico', e.target.value)}
                                                    size="small"
                                                    sx={{ mb: 1 }}
                                                    fullWidth
                                                />
                                                <Typography variant="caption" display="block">
                                                    <strong>Medicamentos:</strong> {row.medicamentos && row.medicamentos.length > 0
                                                        ? row.medicamentos.map(m => m.nome).join(', ')
                                                        : 'Nenhum detectado'}
                                                </Typography>
                                            </TableCell>
                                            <TableCell>
                                                <Tooltip title={`Score: ${row.confianca || 0}%`}>
                                                    <Chip
                                                        label={row.confianca ? `${row.confianca}%` : 'N/A'}
                                                        size="small"
                                                        color={(row.confianca || 0) > 80 ? "success" : (row.confianca || 0) > 50 ? "warning" : "error"}
                                                    />
                                                </Tooltip>
                                            </TableCell>
                                            <TableCell>
                                                <IconButton onClick={() => {
                                                    const newData = [...analyzedData];
                                                    newData.splice(index, 1);
                                                    setAnalyzedData(newData);
                                                }}>
                                                    <Delete />
                                                </IconButton>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>

                        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
                            <Button variant="outlined" onClick={() => setAnalyzedData([])}>Cancelar</Button>
                            <Button
                                variant="contained"
                                color="primary"
                                onClick={handleImport}
                                disabled={importing || analyzedData.some(d => !d.nome)}
                                startIcon={importing ? <CircularProgress size={20} /> : <Save />}
                            >
                                Confirmar e Cadastrar {analyzedData.length} Pacientes
                            </Button>
                        </Box>
                    </Box>
                )}

            </Paper>
        </Container>
    );
};

export default BatchImportPage;
