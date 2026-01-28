import React, { useRef, useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Stack,
  Alert,
  Box,
  Chip,
  LinearProgress,
  Divider,
  FormControlLabel,
  Switch,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  CloudUpload,
  Send,
  CheckCircle,
  AutoFixHigh,
  CameraAlt,
  Mic,
  Stop,
  RadioButtonChecked,
  Delete
} from '@mui/icons-material';
import { produtosService } from '../services/api';

const ProductAIAssistant = ({ onApplySuggestion, onProductCreated, onEditSuggestion }) => {
  const [texto, setTexto] = useState('');
  const [arquivo, setArquivo] = useState(null);
  const [resultado, setResultado] = useState(null);
  const [loading, setLoading] = useState(false);
  const [autoCriar, setAutoCriar] = useState(true);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  // Estados para captura de mídia
  const [captureMode, setCaptureMode] = useState(null); // 'camera' or 'audio'
  const [mediaStream, setMediaStream] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [capturedBlob, setCapturedBlob] = useState(null);
  const [capturedPreview, setCapturedPreview] = useState(null); // URL for preview

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Limpar recursos ao desmontar
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
      setCaptureMode('camera');
      setCapturedBlob(null);
      setCapturedPreview(null);
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      setMediaStream(stream);
      // O vídeo será atribuído via ref callback ou effect quando o dialog abrir e o elemento existir
      setTimeout(() => {
        if (videoRef.current) videoRef.current.srcObject = stream;
      }, 100);
    } catch (err) {
      console.error(err);
      setError('Erro ao acessar a câmera: ' + err.message);
      setCaptureMode(null);
    }
  };

  const startAudio = async () => {
    try {
      setCaptureMode('audio');
      setCapturedBlob(null);
      setCapturedPreview(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setMediaStream(stream);
    } catch (err) {
      console.error(err);
      setError('Erro ao acessar o microfone: ' + err.message);
      setCaptureMode(null);
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

  const closeCapture = () => {
    stopMediaStream();
    setCaptureMode(null);
    // Se cancelou sem capturar, limpa tudo. Se já capturou, mantém o blob.
    if (!capturedBlob) {
      setCapturedPreview(null);
    }
  };

  const confirmCapture = () => {
    // O blob já está em capturedBlob
    setCaptureMode(null);
  };

  const clearCapture = () => {
    setCapturedBlob(null);
    setCapturedPreview(null);
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setArquivo(file);
      // Limpar captura se selecionar arquivo
      setCapturedBlob(null);
      setCapturedPreview(null);
    }
  };

  const limpar = () => {
    setTexto('');
    setArquivo(null);
    setCapturedBlob(null);
    setCapturedPreview(null);
    setResultado(null);
    setError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleEnviar = async () => {
    // Prioridade: Arquivo Capture > Arquivo Upload > Texto
    const fileToSend = capturedBlob || arquivo;

    if (!texto.trim() && !fileToSend) {
      setError('Envie um texto, arquivo, foto ou áudio para o agente cadastrador');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const formData = new FormData();
      if (texto.trim()) formData.append('texto', texto.trim());
      if (fileToSend) formData.append('arquivo', fileToSend);

      formData.append('auto_criar', autoCriar ? 'true' : 'false');

      const response = await produtosService.assistente(formData);
      setResultado(response);
      if (response?.produto_criado && response.produto && onProductCreated) {
        onProductCreated(response.produto);
      }
    } catch (err) {
      setError(err?.error || 'Não foi possível processar o produto com IA');
    } finally {
      setLoading(false);
    }
  };

  const aplicarSugestao = () => {
    if (resultado?.produto_sugerido && onApplySuggestion) {
      onApplySuggestion(resultado.produto_sugerido);
    }
  };

  return (
    <Card variant="outlined" sx={{ mb: 3 }}>
      <CardContent>
        <Stack direction="row" spacing={1} alignItems="center" mb={2}>
          <AutoFixHigh color="success" />
          <Typography variant="h6">Cadastro inteligente de produtos</Typography>
          <Chip label="Texto / Áudio / Imagem" size="small" color="success" variant="outlined" />
        </Stack>

        <Typography variant="body2" color="text.secondary" mb={2}>
          Envie um áudio, imagem ou texto com os detalhes do medicamento. O agente extrai nome, fabricante,
          concentrações e volume. Ative o modo automático para salvar diretamente quando houver confiança.
        </Typography>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {loading && <LinearProgress sx={{ mb: 2 }} />}

        <Stack spacing={2}>
          <TextField
            label="Texto livre"
            placeholder="Ex: Óleo full spectrum 30ml, 50mg/ml CBD, 5mg/ml THC, fabricante CanabCare..."
            multiline
            minRows={3}
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            fullWidth
          />

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems="center" flexWrap="wrap">
            <input
              type="file"
              ref={fileInputRef}
              hidden
              accept=".mp3,.wav,.m4a,.ogg,.flac,.png,.jpg,.jpeg,.txt"
              onChange={handleFileChange}
            />

            <Button
              variant="outlined"
              startIcon={<CloudUpload />}
              onClick={() => fileInputRef.current && fileInputRef.current.click()}
            >
              Upload
            </Button>

            <Button
              variant="outlined"
              color="secondary"
              startIcon={<CameraAlt />}
              onClick={startCamera}
            >
              Foto
            </Button>

            <Button
              variant="outlined"
              color="secondary"
              startIcon={<Mic />}
              onClick={startAudio}
            >
              Áudio
            </Button>

            <FormControlLabel
              control={
                <Switch
                  checked={autoCriar}
                  onChange={(e) => setAutoCriar(e.target.checked)}
                  color="success"
                />
              }
              label="Criar auto"
            />

            <Box flexGrow={1} />

            <Button
              variant="contained"
              startIcon={<Send />}
              onClick={handleEnviar}
              disabled={loading}
            >
              Processar IA
            </Button>
            <Button variant="text" color="inherit" onClick={limpar}>Limpar</Button>
          </Stack>

          {/* Exibir arquivo/captura selecionada */}
          {(arquivo || capturedBlob) && (
            <Box sx={{ display: 'flex', alignItems: 'center', bgcolor: 'grey.100', p: 1, borderRadius: 1 }}>
              <CheckCircle fontSize="small" color="success" sx={{ mr: 1 }} />
              <Typography variant="body2" sx={{ flexGrow: 1 }}>
                {capturedBlob ? 'Mídia capturada pronta para envio' : `Arquivo: ${arquivo.name}`}
              </Typography>
              {capturedPreview && capturedBlob?.type.startsWith('image') && (
                <Box
                  component="img"
                  src={capturedPreview}
                  sx={{ height: 40, width: 40, objectFit: 'cover', borderRadius: 1, mr: 1 }}
                />
              )}
              {capturedPreview && capturedBlob?.type.startsWith('audio') && (
                <audio src={capturedPreview} controls style={{ height: 30, width: 200 }} />
              )}
              <IconButton size="small" onClick={capturedBlob ? clearCapture : () => { setArquivo(null); fileInputRef.current.value = ''; }}>
                <Delete fontSize="small" />
              </IconButton>
            </Box>
          )}
        </Stack>

        {/* Dialog de Captura */}
        <Dialog open={!!captureMode} onClose={closeCapture} maxWidth="md">
          <DialogTitle>
            {captureMode === 'camera' ? 'Tirar Foto do Produto' : 'Gravar Áudio'}
          </DialogTitle>
          <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 300, minHeight: 200 }}>
              {captureMode === 'camera' && (
                <>
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    style={{ width: '100%', maxWidth: 500, borderRadius: 8, display: capturedBlob ? 'none' : 'block' }}
                  />
                  <canvas ref={canvasRef} style={{ display: 'none' }} />
                  {capturedBlob && (
                    <Box component="img" src={capturedPreview} sx={{ width: '100%', maxWidth: 500, borderRadius: 8 }} />
                  )}
                </>
              )}

              {captureMode === 'audio' && (
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', pt: 4 }}>
                  {isRecording ? (
                    <RadioButtonChecked sx={{ fontSize: 60, color: 'error.main', animation: 'pulse 1s infinite' }} />
                  ) : (
                    <Mic sx={{ fontSize: 60, color: 'text.secondary' }} />
                  )}
                  <Typography variant="h6" sx={{ mt: 2 }}>
                    {isRecording ? 'Gravando...' : capturedBlob ? 'Áudio gravado' : 'Pronto para gravar'}
                  </Typography>
                  {capturedBlob && (
                    <Box sx={{ mt: 2 }}>
                      <audio src={capturedPreview} controls />
                    </Box>
                  )}
                </Box>
              )}
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={closeCapture}>Cancelar</Button>

            {captureMode === 'camera' && !capturedBlob && (
              <Button variant="contained" onClick={takePhoto} startIcon={<CameraAlt />}>Capturar</Button>
            )}

            {captureMode === 'audio' && (
              !isRecording && !capturedBlob ? (
                <Button variant="contained" color="error" onClick={startRecording} startIcon={<RadioButtonChecked />}>Gravar</Button>
              ) : isRecording ? (
                <Button variant="contained" onClick={stopRecording} startIcon={<Stop />}>Parar</Button>
              ) : null
            )}

            {capturedBlob && (
              <>
                <Button onClick={() => { setCapturedBlob(null); setCapturedPreview(null); if (captureMode === 'camera') startCamera(); }}>Tentar Novamente</Button>
                <Button variant="contained" color="primary" onClick={confirmCapture}>Usar esta mídia</Button>
              </>
            )}
          </DialogActions>
        </Dialog>

        {resultado && (
          <Box mt={3}>
            <Divider sx={{ mb: 2 }} />
            <Stack direction="row" spacing={1} alignItems="center" mb={1}>
              <CheckCircle color={resultado.produto_criado ? 'success' : 'primary'} />
              <Typography variant="subtitle1">
                {resultado.produto_criado ? 'Produto criado automaticamente' : 'Sugestão gerada pela IA'}
              </Typography>
              <Chip label={`Fonte: ${resultado.fonte}`} size="small" />
              {resultado.produto_sugerido?.confianca && (
                <Chip label={`Confiança: ${resultado.produto_sugerido.confianca}%`} size="small" color="success" />
              )}
            </Stack>

            <Typography variant="body2" color="text.secondary" mb={1}>
              Texto processado: {resultado.texto_processado?.slice(0, 260) || 'N/D'}
              {resultado.texto_processado && resultado.texto_processado.length > 260 ? '...' : ''}
            </Typography>

            {resultado.produto_sugerido && (
              <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1, mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>Produto sugerido</Typography>
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  {JSON.stringify(resultado.produto_sugerido, null, 2)}
                </pre>
              </Box>
            )}

            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <Button variant="contained" color="success" onClick={aplicarSugestao}>
                Aplicar no formulário
              </Button>
              {onEditSuggestion && resultado.produto_sugerido && (
                <Button variant="outlined" color="primary" onClick={() => onEditSuggestion(resultado.produto_sugerido)}>
                  Editar sugestão
                </Button>
              )}
              {resultado.produto_criado && (
                <Alert severity="success" icon={<CheckCircle fontSize="inherit" />}>
                  Produto salvo com sucesso.
                </Alert>
              )}
            </Stack>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default ProductAIAssistant;
