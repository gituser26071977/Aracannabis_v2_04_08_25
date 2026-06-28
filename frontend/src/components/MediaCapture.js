import React, { useRef, useState, useEffect } from 'react';
import {
    Button,
    Box,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    IconButton,
    Typography,
    Stack
} from '@mui/material';
import {
    CameraAlt,
    Mic,
    Stop,
    RadioButtonChecked,
    Close,
    Check
} from '@mui/icons-material';

/**
 * Módulo de Captura de Mídia (Mobile-First)
 * Permite capturar fotos e áudio diretamente do navegador.
 * 
 * @param {function} onCapture - Callback recebe o arquivo capturado (File object)
 * @param {string} mode - 'camera' | 'audio' | 'both' (padrão 'both')
 * @param {boolean} open - Se o diálogo deve abrir automaticamente (opcional)
 * @param {function} onClose - Callback quando fecha sem capturar
 */
const MediaCapture = ({ onCapture, mode = 'both', onClose, triggerButton }) => {
    const [internalOpen, setInternalOpen] = useState(false);
    const [activeMode, setActiveMode] = useState(null); // 'camera' ou 'audio'
    const [mediaStream, setMediaStream] = useState(null);
    const [capturedBlob, setCapturedBlob] = useState(null);
    const [capturedPreview, setCapturedPreview] = useState(null);
    const [isRecording, setIsRecording] = useState(false);
    const [error, setError] = useState('');

    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);

    // Cleanup
    useEffect(() => {
        return () => {
            stopMediaStream();
            if (capturedPreview) URL.revokeObjectURL(capturedPreview);
        };
    }, []);

    const stopMediaStream = () => {
        if (mediaStream) {
            mediaStream.getTracks().forEach(track => track.stop());
            setMediaStream(null);
        }
    };

    const startCamera = async () => {
        try {
            stopMediaStream();
            setActiveMode('camera');
            setCapturedBlob(null);
            setCapturedPreview(null);
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment' } // Preferência pela câmera traseira em mobile
            });
            setMediaStream(stream);
            setTimeout(() => {
                if (videoRef.current) videoRef.current.srcObject = stream;
            }, 100);
        } catch (err) {
            if(process.env.NODE_ENV!=='production')console.error(err);
            setError('Erro ao acessar a câmera: ' + err.message);
            setActiveMode(null);
        }
    };

    const startAudio = async () => {
        try {
            stopMediaStream();
            setActiveMode('audio');
            setCapturedBlob(null);
            setCapturedPreview(null);
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            setMediaStream(stream);
        } catch (err) {
            if(process.env.NODE_ENV!=='production')console.error(err);
            setError('Erro ao acessar o microfone: ' + err.message);
            setActiveMode(null);
        }
    };

    const takePhoto = () => {
        if (!videoRef.current || !canvasRef.current) return;

        const video = videoRef.current;
        const canvas = canvasRef.current;
        const context = canvas.getContext('2d');

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob((blob) => {
            const file = new File([blob], "camera_capture.jpg", { type: "image/jpeg" });
            setCapturedBlob(file);
            setCapturedPreview(URL.createObjectURL(blob));
            stopMediaStream();
        }, 'image/jpeg', 0.85);
    };

    const startRecording = () => {
        if (!mediaStream) return;
        audioChunksRef.current = [];
        const mediaRecorder = new MediaRecorder(mediaStream);
        mediaRecorderRef.current = mediaRecorder;

        mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) audioChunksRef.current.push(e.data);
        };

        mediaRecorder.onstop = () => {
            const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
            const file = new File([blob], "audio_record.webm", { type: "audio/webm" });
            setCapturedBlob(file);
            setCapturedPreview(URL.createObjectURL(blob));
            stopMediaStream();
        };

        mediaRecorder.start();
        setIsRecording(true);
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
        }
    };

    const handleConfirm = () => {
        if (onCapture && capturedBlob) {
            onCapture(capturedBlob, capturedPreview);
        }
        handleClose();
    };

    const handleClose = () => {
        stopMediaStream();
        setActiveMode(null);
        setCapturedBlob(null);
        setCapturedPreview(null);
        setInternalOpen(false);
        if (onClose) onClose();
    };

    const handleOpen = (targetMode) => {
        setInternalOpen(true);
        if (targetMode === 'camera') startCamera();
        else if (targetMode === 'audio') startAudio();
    };

    // Se não houver botão de trigger externo, renderizamos botões padrão
    const renderDefaultTriggers = () => (
        <Stack direction="row" spacing={1}>
            {(mode === 'both' || mode === 'camera') && (
                <Button
                    variant="outlined"
                    startIcon={<CameraAlt />}
                    onClick={() => handleOpen('camera')}
                >
                    Foto
                </Button>
            )}
            {(mode === 'both' || mode === 'audio') && (
                <Button
                    variant="outlined"
                    startIcon={<Mic />}
                    onClick={() => handleOpen('audio')}
                >
                    Áudio
                </Button>
            )}
        </Stack>
    );

    return (
        <>
            {triggerButton ? (
                // Se passar um elemento renderizável (função ou componente), usa-o
                React.cloneElement(triggerButton, { onClick: () => handleOpen(mode === 'audio' ? 'audio' : 'camera') })
            ) : (
                renderDefaultTriggers()
            )}

            {/* Dialog FullScreen em Mobile para imersão */}
            <Dialog
                open={internalOpen}
                onClose={handleClose}
                maxWidth="md"
                fullWidth
                PaperProps={{
                    sx: {
                        borderRadius: { xs: 0, sm: 2 },
                        margin: { xs: 0, sm: 3 },
                        height: { xs: '100%', sm: 'auto' },
                        maxHeight: { xs: '100%', sm: 'calc(100% - 64px)' }
                    }
                }}
            >
                <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    {activeMode === 'camera' ? 'Capturar Imagem' : 'Capturar Áudio'}
                    <IconButton edge="end" color="inherit" onClick={handleClose} aria-label="close">
                        <Close />
                    </IconButton>
                </DialogTitle>

                <DialogContent dividers sx={{ p: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', bgcolor: '#000' }}>
                    {error && (
                        <Typography color="error" sx={{ p: 2, bgcolor: 'white' }}>{error}</Typography>
                    )}

                    {/* CAMERA PREVIEW */}
                    {activeMode === 'camera' && (
                        <Box sx={{ width: '100%', height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', position: 'relative' }}>
                            {!capturedBlob ? (
                                <video
                                    ref={videoRef}
                                    autoPlay
                                    playsInline
                                    style={{
                                        width: '100%',
                                        height: '100%',
                                        objectFit: 'cover',
                                        maxHeight: '60vh'
                                    }}
                                />
                            ) : (
                                <Box
                                    component="img"
                                    src={capturedPreview}
                                    sx={{
                                        width: '100%',
                                        height: 'auto',
                                        maxHeight: '60vh',
                                        objectFit: 'contain'
                                    }}
                                />
                            )}
                            <canvas ref={canvasRef} style={{ display: 'none' }} />
                        </Box>
                    )}

                    {/* AUDIO RECORDER UI */}
                    {activeMode === 'audio' && (
                        <Box sx={{ width: '100%', height: 300, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', bgcolor: '#121212', color: 'white' }}>
                            {isRecording ? (
                                <Box sx={{ position: 'relative', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                                    <Box sx={{
                                        position: 'absolute',
                                        width: 100,
                                        height: 100,
                                        borderRadius: '50%',
                                        bgcolor: 'rgba(244, 67, 54, 0.3)',
                                        animation: 'pulse 1.5s infinite'
                                    }} />
                                    <RadioButtonChecked sx={{ fontSize: 80, color: '#f44336', zIndex: 1 }} />
                                </Box>
                            ) : (
                                <Mic sx={{ fontSize: 80, color: 'text.secondary' }} />
                            )}

                            <Typography variant="h5" sx={{ mt: 3, mb: 1 }}>
                                {isRecording ? 'Gravando...' : capturedBlob ? 'Áudio Gravado!' : 'Toque para Gravar'}
                            </Typography>

                            {capturedBlob && (
                                <audio src={capturedPreview} controls style={{ marginTop: 20, width: '80%' }} />
                            )}
                        </Box>
                    )}

                </DialogContent>

                {/* CONTROLS */}
                <DialogActions sx={{ justifyContent: 'center', p: 3, bgcolor: '#121212' }}>
                    {capturedBlob ? (
                        // Ações pós-captura
                        <Stack direction="row" spacing={4}>
                            <Button
                                variant="outlined"
                                color="error"
                                onClick={() => {
                                    setCapturedBlob(null);
                                    setCapturedPreview(null);
                                    if (activeMode === 'camera') startCamera();
                                }}
                            >
                                Refazer
                            </Button>
                            <Button
                                variant="contained"
                                color="success"
                                startIcon={<Check />}
                                onClick={handleConfirm}
                                sx={{ px: 4 }}
                            >
                                Usar
                            </Button>
                        </Stack>
                    ) : (
                        // Ações de captura
                        activeMode === 'camera' ? (
                            <IconButton
                                onClick={takePhoto}
                                sx={{
                                    width: 70,
                                    height: 70,
                                    bgcolor: 'white',
                                    '&:hover': { bgcolor: '#f5f5f5' },
                                    border: '4px solid #ccc'
                                }}
                            >
                                <CameraAlt sx={{ fontSize: 30, color: '#333' }} />
                            </IconButton>
                        ) : (
                            <IconButton
                                onClick={isRecording ? stopRecording : startRecording}
                                sx={{
                                    width: 70,
                                    height: 70,
                                    bgcolor: isRecording ? '#f44336' : 'white',
                                    '&:hover': { bgcolor: isRecording ? '#d32f2f' : '#f5f5f5' },
                                    border: '4px solid #ccc'
                                }}
                            >
                                {isRecording ? <Stop sx={{ fontSize: 30, color: 'white' }} /> : <RadioButtonChecked sx={{ fontSize: 30, color: '#f44336' }} />}
                            </IconButton>
                        )
                    )}
                </DialogActions>

                {/* CSS Animation for Pulse */}
                <style>{`
            @keyframes pulse {
                0% { transform: scale(1); opacity: 0.7; }
                50% { transform: scale(1.2); opacity: 0.4; }
                100% { transform: scale(1); opacity: 0.7; }
            }
        `}</style>
            </Dialog>
        </>
    );
};

export default MediaCapture;
