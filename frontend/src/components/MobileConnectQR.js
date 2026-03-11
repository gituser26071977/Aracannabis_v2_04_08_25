import React, { useState, useEffect, useRef } from 'react';
import {
    Box,
    Typography,
    CircularProgress,
    Alert,
    IconButton,
    Button
} from '@mui/material';
import { Refresh, AccessTime } from '@mui/icons-material';
import api from '../services/api';

const MobileConnectQR = ({ onUploadComplete, context = 'exam' }) => {
    const [token, setToken] = useState(null);
    const [uploadUrl, setUploadUrl] = useState('');
    const [qrCodeUrl, setQrCodeUrl] = useState('');
    const [status, setStatus] = useState('loading'); // loading, waiting, completed, expired, error
    const [timeLeft, setTimeLeft] = useState(900); // 15 minutos em segundos
    const pollingInterval = useRef(null);

    useEffect(() => {
        startSession();
        return () => stopPolling();
    }, []);

    useEffect(() => {
        if (timeLeft > 0 && status === 'waiting') {
            const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
            return () => clearTimeout(timer);
        } else if (timeLeft === 0) {
            setStatus('expired');
            stopPolling();
        }
    }, [timeLeft, status]);

    const stopPolling = () => {
        if (pollingInterval.current) {
            clearInterval(pollingInterval.current);
            pollingInterval.current = null;
        }
    };

    const startSession = async () => {
        stopPolling();
        setStatus('loading');
        setToken(null);
        try {
            // Usando a instância 'api' configurada (que adiciona baseURL automaticamente)
            const response = await api.post('/mobile/start', { context });

            const { token, upload_url, expires_at } = response.data;
            setToken(token);

            // Construir URL completa para o usuário acessar
            // Como o celular acessa de fora, precisamos garantir que ele pegue o IP/Host correto
            const currentHost = window.location.protocol + '//' + window.location.host;
            const fullUrl = `${currentHost}/mobile-upload/${token}`;
            setUploadUrl(fullUrl);

            // Gerar QR Code usando API pública segura
            // O QR Code apontará para a página mobile no frontend desta aplicação
            const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(fullUrl)}`;
            setQrCodeUrl(qrUrl);

            setStatus('waiting');
            setTimeLeft(900);

            // Iniciar polling
            pollingInterval.current = setInterval(() => checkStatus(token), 2500);
        } catch (err) {
            console.error(err);
            setStatus('error');
        }
    };

    const checkStatus = async (activeToken) => {
        try {
            const response = await api.get(`/mobile/status/${activeToken}`);

            if (response.data.status === 'completed') {
                stopPolling();
                setStatus('completed');

                // Buscar o arquivo real (blob) para passar para o componente pai
                if (response.data.file_url) {
                    try {
                        // Precisamos baixar o blob. Podemos usar api.get com config específica
                        const fileRes = await api.get(response.data.file_url, { responseType: 'blob' });
                        const file = new File([fileRes.data], response.data.original_filename, { type: response.data.file_type });
                        if (onUploadComplete) onUploadComplete(file);
                    } catch (downloadErr) {
                        console.error("Erro ao baixar arquivo enviado pelo mobile", downloadErr);
                    }
                }
            } else if (response.data.status === 'expired') {
                stopPolling();
                setStatus('expired');
            }
        } catch (err) {
            // Ignorar erros de rede transientes no polling, ou se retornar 404/410 tratar como erro de sessão
            if (err.response && (err.response.status === 404 || err.response.status === 410)) {
                stopPolling();
                setStatus('expired');
            }
        }
    };

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
    };

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', p: 2 }}>
            {status === 'loading' && <CircularProgress />}

            {status === 'error' && (
                <Alert severity="error" action={
                    <IconButton size="small" onClick={startSession}><Refresh /></IconButton>
                }>
                    Erro ao iniciar sessão. Verifique a conexão.
                </Alert>
            )}

            {status === 'expired' && (
                <Box sx={{ textAlign: 'center' }}>
                    <Alert severity="warning" sx={{ mb: 2 }}>QR Code expirado.</Alert>
                    <Button startIcon={<Refresh />} variant="contained" onClick={startSession}>
                        Gerar Novo Código
                    </Button>
                </Box>
            )}

            {status === 'waiting' && (
                <>
                    <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                        {context === 'product' ? 'Escaneie para cadastrar produto' : 'Aponte a câmera do seu celular'}
                    </Typography>

                    <Box
                        component="img"
                        src={qrCodeUrl}
                        alt="QR Code para upload mobile"
                        sx={{ width: 250, height: 250, border: '1px solid #ddd', borderRadius: 2, p: 1, mb: 2 }}
                    />

                    <Box sx={{ display: 'flex', alignItems: 'center', color: 'text.secondary', mb: 2 }}>
                        <AccessTime fontSize="small" sx={{ mr: 0.5 }} />
                        <Typography variant="body2">Expira em {formatTime(timeLeft)}</Typography>
                    </Box>

                    <Box sx={{ bgcolor: 'grey.100', p: 1.5, borderRadius: 1, width: '100%', mb: 2, wordBreak: 'break-all' }}>
                        <Typography variant="caption" sx={{ display: 'block', textAlign: 'center', color: 'text.secondary' }}>
                            Ou acesse o link:
                        </Typography>
                        <Typography variant="caption" sx={{ display: 'block', textAlign: 'center', fontWeight: 'bold', mt: 0.5 }}>
                            {uploadUrl}
                        </Typography>
                    </Box>

                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <CircularProgress size={16} />
                        <Typography variant="body2">Aguardando conexão...</Typography>
                    </Box>
                </>
            )}

            {status === 'completed' && (
                <Alert severity="success" sx={{ width: '100%' }}>
                    Arquivo recebido com sucesso!
                </Alert>
            )}
        </Box>
    );
};

export default MobileConnectQR;
