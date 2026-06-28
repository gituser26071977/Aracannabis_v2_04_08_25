import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
    Box,
    Typography,
    Button,
    Container,
    Alert,
    CircularProgress,
    Paper
} from '@mui/material';
import { CloudUpload, CheckCircle, ErrorOutline } from '@mui/icons-material';
import MediaCapture from '../components/MediaCapture';
import api from '../services/api';
import useNotifier from '../hooks/useNotifier';

const MobileUploadPage = () => {
    const { token } = useParams();
    const [status, setStatus] = useState('loading'); // loading, active, expired, not_found, completed
    const [context, setContext] = useState('exam'); // 'exam' or 'product'
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [uploadSuccess, setUploadSuccess] = useState(false);
    const [aiProcessing, setAiProcessing] = useState(false);
    const [productData, setProductData] = useState(null);
    const [savingProduct, setSavingProduct] = useState(false);
    const { notify, NotifierElement } = useNotifier();

    useEffect(() => {
        // Validar token ao carregar
        checkTokenStatus();
    }, [token]);

    const checkTokenStatus = async () => {
        try {
            const response = await api.get(`/mobile/status/${token}`);
            const sessionContext = response.data.context || 'exam';
            setContext(sessionContext);

            if (response.data.status === 'pending') {
                setStatus('active');
            } else if (response.data.status === 'completed') {
                setStatus('completed');
            } else {
                setStatus('expired');
            }
        } catch (err) {
            if (err.response && (err.response.status === 404 || err.response.status === 410)) {
                setStatus('not_found'); // 404 ou 410 (se backend tratar expired como 410)
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

            await api.post(`/mobile/upload/${token}`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });

            // Se for produto, processar com IA
            if (context === 'product') {
                await processProduct();
            } else {
                setUploadSuccess(true);
                setStatus('completed');
            }
        } catch (err) {
            if(process.env.NODE_ENV!=='production')console.error(err);
            notify('Erro ao enviar arquivo. Tente novamente.', 'error');
        } finally {
            setUploading(false);
        }
    };

    const processProduct = async () => {
        setAiProcessing(true);
        try {
            const response = await api.post(`/mobile/process-product/${token}`);
            setProductData(response.data.produto_sugerido);
            setStatus('product_confirmation');
        } catch (err) {
            if(process.env.NODE_ENV!=='production')console.error(err);
            notify('Erro ao processar produto. Tente novamente.', 'error');
        } finally {
            setAiProcessing(false);
        }
    };

    const handleConfirmProduct = async () => {
        if (!productData) return;

        setSavingProduct(true);
        try {
            await api.post('/produtos', productData);
            setUploadSuccess(true);
            setStatus('completed');
        } catch (err) {
            if(process.env.NODE_ENV!=='production')console.error(err);
            notify('Erro ao salvar produto. Tente novamente.', 'error');
        } finally {
            setSavingProduct(false);
        }
    };

    if (status === 'loading') {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
                <CircularProgress />
            </Box>
        );
    }

    if (status === 'error') {
        return (
            <Container maxWidth="sm" sx={{ mt: 4 }}>
                <Alert severity="error">
                    <Typography variant="h6">Erro de Conexão</Typography>
                    <Typography variant="body1">
                        Não foi possível verificar o status da sessão. Verifique sua conexão.
                    </Typography>
                    <Button onClick={checkTokenStatus} sx={{ mt: 1 }}>Tentar Novamente</Button>
                </Alert>
            </Container>
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
        <>
            <NotifierElement />
            <Container maxWidth="sm" sx={{ py: 3, height: '100vh', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ mb: 3, textAlign: 'center' }}>
                <Typography variant="h5" component="h1" gutterBottom fontWeight="bold">
                    {context === 'product' ? 'Cadastro de Produto' : 'Captura Mobile'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    {context === 'product'
                        ? 'Tire uma foto do rótulo do produto ou grave uma descrição em áudio.'
                        : 'Tire uma foto ou grave um áudio para anexar ao prontuário no PC.'}
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
                    disabled={uploading || aiProcessing}
                    startIcon={(uploading || aiProcessing) ? <CircularProgress size={20} color="inherit" /> : <CloudUpload />}
                    sx={{ py: 1.5, fontSize: '1.1rem', borderRadius: 2 }}
                >
                    {uploading ? 'Enviando...' : aiProcessing ? 'Processando IA...' : context === 'product' ? 'Processar Produto' : 'Enviar para o PC'}
                </Button>
            )}

            {/* Product Confirmation UI */}
            {status === 'product_confirmation' && productData && (
                <Paper sx={{ p: 3, mt: 2 }}>
                    <Typography variant="h6" gutterBottom>Produto Identificado</Typography>
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary">Nome:</Typography>
                        <Typography variant="body1" fontWeight="bold">{productData.nome || 'N/A'}</Typography>
                    </Box>
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary">Concentrações:</Typography>
                        <Typography variant="body2">CBD: {productData.concentracao_cbd || 0} mg/ml</Typography>
                        <Typography variant="body2">THC: {productData.concentracao_thc || 0} mg/ml</Typography>
                    </Box>
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary">Volume:</Typography>
                        <Typography variant="body2">{productData.volume_ml || 30} ml</Typography>
                    </Box>
                    <Button
                        variant="contained"
                        color="success"
                        fullWidth
                        size="large"
                        onClick={handleConfirmProduct}
                        disabled={savingProduct}
                        sx={{ mt: 2 }}
                    >
                        {savingProduct ? 'Salvando...' : 'Confirmar e Salvar'}
                    </Button>
                </Paper>
            )}
        </Container>
        </>
    );
};

export default MobileUploadPage;
