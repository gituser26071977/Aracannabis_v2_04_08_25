import React, { useState, useRef, useCallback } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  Grid,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardMedia,
  CardContent,
  Alert,
  LinearProgress,
  IconButton,
  Chip,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  CloudUpload,
  CameraAlt,
  CheckCircle,
  Error as ErrorIcon,
  PersonAdd,
  Close,
} from '@mui/icons-material';
import api from '../services/api';

const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf'];

const IntelligentOnboardingPage = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [cameraOpen, setCameraOpen] = useState(false);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  const streamRef = useRef(null);

  const steps = ['Upload do Documento', 'Análise por IA', 'Revisar & Finalizar'];

  const handleFile = useCallback(async (file) => {
    if (!file) return;
    if (!ALLOWED_TYPES.includes(file.type)) {
      setError('Formato não suportado. Use PNG, JPEG ou PDF.');
      return;
    }
    setError('');
    setFile(file);
    setPreview(URL.createObjectURL(file));
    setActiveStep(0);

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    try {
      const response = await api.post('/onboarding/documento/upload', formData);
      setResult(response.data);
      setActiveStep(1);
    } catch (err) {
      const msg =
        err.response?.data?.error || err.response?.data?.mensagem || 'Erro ao processar documento';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      const droppedFile = e.dataTransfer.files[0];
      handleFile(droppedFile);
    },
    [handleFile],
  );

  const handleCameraStart = async () => {
    setCameraOpen(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      setError('Câmera não disponível. Use upload de arquivo.');
      setCameraOpen(false);
    }
  };

  const handleCameraCapture = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const video = videoRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    canvas.toBlob((blob) => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
      setCameraOpen(false);
      const file = new File([blob], `camera_${Date.now()}.jpg`, { type: 'image/jpeg' });
      handleFile(file);
    }, 'image/jpeg');
  };

  const handleCameraStop = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }
    setCameraOpen(false);
  };

  const handleCriarPaciente = async () => {
    setLoading(true);
    try {
      const dados = result?.analise?.dados_paciente || {};
      const payload = {
        nome: dados.nome || '',
        cpf: dados.cpf || '',
        telefone: dados.telefone || '',
        email: dados.email || '',
        data_nascimento: dados.data_nascimento || '',
        endereco: dados.endereco || '',
        documento_id: result?.documento_id,
      };
      const response = await api.post('/onboarding/paciente', payload);
      setResult((prev) => ({ ...prev, finalizacao: response.data }));
      setActiveStep(2);
    } catch (err) {
      setError(err.response?.data?.error || 'Erro ao cadastrar paciente');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmarPendencia = async (acao) => {
    if (!result?.onboarding_id) return;
    setLoading(true);
    try {
      const response = await api.post(`/onboarding/pendentes/${result.onboarding_id}/confirmar`, {
        acao,
      });
      setResult((prev) => ({ ...prev, finalizacao: response.data }));
      setActiveStep(2);
    } catch (err) {
      setError(err.response?.data?.error || 'Erro ao confirmar pendência');
    } finally {
      setLoading(false);
    }
  };

  const renderStatusBadge = (status) => {
    const config = {
      criado: { color: 'success', icon: <CheckCircle />, label: 'Paciente Criado' },
      pendente: { color: 'warning', icon: <ErrorIcon />, label: 'Pendente' },
      duplicado: { color: 'info', icon: <PersonAdd />, label: 'Já Existe' },
      lote_processado: { color: 'success', icon: <CheckCircle />, label: 'Lote Processado' },
    };
    const cfg = config[status] || { color: 'default', icon: null, label: status };
    return <Chip icon={cfg.icon} label={cfg.label} color={cfg.color} />;
  };

  return (
    <Box sx={{ maxWidth: 900, mx: 'auto', p: 2 }}>
      <Typography variant="h4" gutterBottom>
        📋 Onboarding Inteligente de Pacientes
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Faça upload de documentos (RG, CPF, receita, exames) ou fotografe com a câmera. A IA
        identifica automaticamente os dados e cria o cadastro.
      </Typography>

      <Stepper activeStep={activeStep} sx={{ my: 3 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Step 0: Upload */}
      {activeStep === 0 && !loading && (
        <Paper
          elevation={3}
          sx={{
            p: 4,
            textAlign: 'center',
            border: '2px dashed #ccc',
            cursor: 'pointer',
            ':hover': { borderColor: 'primary.main' },
          }}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*,application/pdf"
            hidden
            onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])}
          />
          <CloudUpload sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
          <Typography variant="h6">Arraste um documento aqui ou clique para selecionar</Typography>
          <Typography variant="body2" color="text.secondary">
            Formatos: PNG, JPEG, PDF
          </Typography>
          <Divider sx={{ my: 2 }}>ou</Divider>
          <Button
            variant="contained"
            startIcon={<CameraAlt />}
            onClick={(e) => {
              e.stopPropagation();
              handleCameraStart();
            }}
          >
            Abrir Câmera
          </Button>
        </Paper>
      )}

      {/* Camera Dialog */}
      <Dialog open={cameraOpen} maxWidth="sm" fullWidth>
        <DialogTitle>
          Fotografar Documento
          <IconButton sx={{ position: 'absolute', right: 8, top: 8 }} onClick={handleCameraStop}>
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <video ref={videoRef} autoPlay playsInline style={{ width: '100%', borderRadius: 8 }} />
          <canvas ref={canvasRef} style={{ display: 'none' }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCameraStop}>Cancelar</Button>
          <Button variant="contained" onClick={handleCameraCapture} startIcon={<CameraAlt />}>
            Capturar
          </Button>
        </DialogActions>
      </Dialog>

      {loading && (
        <Box sx={{ my: 4, textAlign: 'center' }}>
          <LinearProgress />
          <Typography sx={{ mt: 2 }}>Processando documento com IA...</Typography>
        </Box>
      )}

      {/* Step 1: Resultado */}
      {result && activeStep === 1 && !loading && (
        <Box>
          <Grid container spacing={3}>
            <Grid item xs={12} md={5}>
              {preview && (
                <Card>
                  <CardMedia
                    component={file?.type === 'application/pdf' ? 'object' : 'img'}
                    data={file?.type === 'application/pdf' ? preview : undefined}
                    src={file?.type !== 'application/pdf' ? preview : undefined}
                    type="application/pdf"
                    sx={{ maxHeight: 300, objectFit: 'contain' }}
                  />
                  <CardContent>
                    <Typography variant="caption" color="text.secondary">
                      {file?.name}
                    </Typography>
                  </CardContent>
                </Card>
              )}
            </Grid>

            <Grid item xs={12} md={7}>
              {renderStatusBadge(result.status)}
              <Typography variant="h6" sx={{ mt: 1 }}>
                {result.mensagem}
              </Typography>

              {result.analise && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2">Tipo do Documento:</Typography>
                  <Chip label={result.analise.tipo || 'N/A'} size="small" sx={{ mb: 1 }} />

                  {result.analise.dados_paciente && (
                    <>
                      <Typography variant="subtitle2" sx={{ mt: 1 }}>
                        Dados Extraídos:
                      </Typography>
                      <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1, mt: 0.5 }}>
                        {Object.entries(result.analise.dados_paciente).map(
                          ([key, val]) =>
                            val && (
                              <Typography key={key} variant="body2">
                                <strong>{key}:</strong> {val}
                              </Typography>
                            ),
                        )}
                      </Box>
                    </>
                  )}

                  {result.analise.texto_extraido && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="subtitle2">Texto Extraído:</Typography>
                      <Typography
                        variant="body2"
                        sx={{
                          whiteSpace: 'pre-wrap',
                          maxHeight: 150,
                          overflow: 'auto',
                          bgcolor: 'grey.50',
                          p: 1,
                          borderRadius: 1,
                        }}
                      >
                        {result.analise.texto_extraido.slice(0, 500)}
                      </Typography>
                    </Box>
                  )}
                </Box>
              )}

              {result.duplicados && result.duplicados.length > 0 && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  <Typography variant="subtitle2">Paciente(s) existente(s):</Typography>
                  {result.duplicados.map((d, i) => (
                    <Typography key={i}>
                      {d.nome} - {d.cpf}
                    </Typography>
                  ))}
                </Alert>
              )}

              <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
                {result.status === 'criado' && (
                  <Button variant="contained" disabled={loading} onClick={handleCriarPaciente}>
                    Confirmar Cadastro
                  </Button>
                )}
                {result.status === 'pendente' && result.motivo === 'duplicado' && (
                  <>
                    <Button
                      variant="contained"
                      onClick={() => handleConfirmarPendencia('usar_existente')}
                    >
                      Vincular ao Existente
                    </Button>
                    <Button variant="outlined" onClick={() => handleConfirmarPendencia('criar')}>
                      Criar Novo
                    </Button>
                  </>
                )}
                {result.status === 'pendente' && result.motivo === 'dados_incompletos' && (
                  <Button variant="contained" onClick={handleCriarPaciente}>
                    Revisar e Cadastrar
                  </Button>
                )}
                <Button
                  variant="text"
                  onClick={() => {
                    setFile(null);
                    setPreview(null);
                    setResult(null);
                    setActiveStep(0);
                  }}
                >
                  Novo Documento
                </Button>
              </Box>
            </Grid>
          </Grid>
        </Box>
      )}

      {/* Step 2: Finalizado */}
      {activeStep === 2 && result?.finalizacao && (
        <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
          <CheckCircle sx={{ fontSize: 60, color: 'success.main', mb: 2 }} />
          <Typography variant="h5" gutterBottom>
            {result.finalizacao.message || 'Processo concluído com sucesso!'}
          </Typography>
          {result.finalizacao.resultado?.status === 'criado' && (
            <Typography>Paciente ID: {result.finalizacao.resultado.paciente_id}</Typography>
          )}
          {result.finalizacao.resultado?.compliance && (
            <Box sx={{ mt: 2 }}>
              <Alert
                severity={result.finalizacao.resultado.compliance.completo ? 'success' : 'warning'}
              >
                {result.finalizacao.resultado.compliance.completo
                  ? 'Todos os dados estão completos.'
                  : `Campos pendentes: ${result.finalizacao.resultado.compliance.campos_faltantes.join(', ')}. O paciente será contato para enviar os documentos.`}
              </Alert>
            </Box>
          )}
          <Button
            variant="contained"
            sx={{ mt: 3 }}
            onClick={() => {
              setFile(null);
              setPreview(null);
              setResult(null);
              setActiveStep(0);
            }}
          >
            Novo Cadastro
          </Button>
        </Paper>
      )}
    </Box>
  );
};

export default IntelligentOnboardingPage;
