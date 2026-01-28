import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
    Box,
    Typography,
    Button,
    Container,
    Alert,
    CircularProgress,
    Paper,
    Stack
} from '@mui/material';
import { CloudUpload, CheckCircle, ErrorOutline } from '@mui/icons-material';
import MediaCapture from '../components/MediaCapture';
import axios from 'axios';
import { api } from '../services/api';
// Assumindo que api.js exporta a instância axios configurada, 
// mas para mobile upload pode ser safer usar axios direto para evitar interceptors de auth complexos se não estiver logado

const MobileUploadPage = () => {
    const { token } = useParams();
    const [status, setStatus] = useState('loading'); // loading, active, expired, not_found, completed
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [uploadSuccess, setUploadSuccess] = useState(false);

    useEffect(() => {
        // Validar token ao carregar
        checkTokenStatus();
    }, [token]);

    const checkTokenStatus = async () => {
        try {
            // Usando rota pública
            // A URL base deve vir do env ou ser relativa (o proxy webpack ou nginx tratam)
            const API_URL = process.env.REACT_APP_API_URL || '/api';

            const response = await axios.get(`${API_URL}/mobile/status/${token}`);
            if (response.data.status === 'pending') {
                setStatus('active');
            } else if (response.data.status === 'completed') {
                setStatus('completed');
            } else {
                setStatus('expired');
            }
        } catch (err) {
            if (err.response && err.response.status === 404) {
                setStatus('not_found');
            } else if (err.response && err.response.status === 410) {
                setStatus('expired');
            } else {
                setStatus('error');
            }
        }
    };

    const handleCapture = (capturedFile, capturedPreview) => {
        setFile(capturedFile);
        setPreview(capturedPreview);
    };

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        try {
            const formData = new FormData();
            formData.append('file', file);

            const API_URL = process.env.REACT_APP_API_URL || '/api';
            await axios.post(`${API_URL}/mobile/upload/${token}`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });

            setUploadSuccess(true);
            setStatus('completed');
        } catch (err) {
            console.error(err);
            alert('Erro ao enviar arquivo. Tente novamente.');
        } finally {
            setUploading(false);
        }
    };

    if (status === 'loading') {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
                <CircularProgress />
            </Box>
        );
    }

    if (status === 'not_found' || status === 'expired') {
        return (
            <Container maxWidth="sm" sx={{ mt: 4 }}>
                <Alert severity="error" icon={<ErrorOutline fontSize="large" />}>
                    <Typography variant="h6">Link Inválido ou Expirado</Typography>
                    <Typography variant="body1">
                        Este link de captura não é mais válido. Por favor, gere um novo QR Code no computador.
                    </Typography>
                </Alert>
            </Container>
        );
    }

    if (uploadSuccess || status === 'completed') {
        return (
            <Container maxWidth="sm" sx={{ mt: 4, textAlign: 'center' }}>
                <Box sx={{ my: 4 }}>
                    <CheckCircle color="success" sx={{ fontSize: 80, mb: 2 }} />
                    <Typography variant="h4" gutterBottom>Sucesso!</Typography>
                    <Typography variant="body1">
                        O arquivo foi enviado para o computador. Você pode fechar esta janela agora.
                    </Typography>
                </Box>
            </Container>
        );
    }

    return (
        <Container maxWidth="sm" sx={{ py: 3, height: '100vh', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ mb: 3, textAlign: 'center' }}>
                <Typography variant="h5" component="h1" gutterBottom fontWeight="bold">
                    Captura Mobile
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    Tire uma foto ou grave um áudio para anexar ao prontuário no PC.
                </Typography>
            </Box>

            <Paper
                elevation={0}
                variant="outlined"
                sx={{
                    flexGrow: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center',
                    mb: 3,
                    bgcolor: '#f8f9fa',
                    overflow: 'hidden',
                    position: 'relative',
                    borderRadius: 4
                }}
            >
                {!file ? (
                    <MediaCapture
                        onCapture={handleCapture}
                        mode="both"
                    />
                ) : (
                    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                        {file.type.startsWith('image') ? (
                            <Box
                                component="img"
                                src={preview}
                                sx={{ width: '100%', height: '100%', objectFit: 'contain' }}
                            />
                        ) : (
                            <Box sx={{ p: 4, width: '100%', textAlign: 'center' }}>
                                <audio src={preview} controls style={{ width: '100%' }} />
                                <Typography sx={{ mt: 2 }}>Áudio gravado</Typography>
                            </Box>
                        )}

                        <Button
                            onClick={() => { setFile(null); setPreview(null); }}
                            sx={{ position: 'absolute', top: 10, right: 10, bgcolor: 'rgba(255,255,255,0.8)' }}
                            color="error"
                        >
                            Remover
                        </Button>
                    </Box>
                )}
            </Paper>

            {file && (
                <Button
                    variant="contained"
                    size="large"
                    fullWidth
                    onClick={handleUpload}
                    disabled={uploading}
                    startIcon={uploading ? <CircularProgress size={20} color="inherit" /> : <CloudUpload />}
                    sx={{ py: 1.5, fontSize: '1.1rem', borderRadius: 2 }}
                >
                    {uploading ? 'Enviando...' : 'Enviar para o PC'}
                </Button>
            )}
        </Container>
    );
};

export default MobileUploadPage;
