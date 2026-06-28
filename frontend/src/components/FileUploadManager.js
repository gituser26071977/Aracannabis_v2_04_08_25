import React, { useState } from 'react';
import {
  Box,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Paper,
  Chip,
  LinearProgress
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  AudioFile as AudioIcon,
  VideoFile as VideoIcon,
  TextFields as TextIcon,
  AutoAwesome as AutoAwesomeIcon
} from '@mui/icons-material';
import api from '../services/api';

const FileUploadManager = ({ patientId, onProcessComplete }) => {
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [showResultDialog, setShowResultDialog] = useState(false);

  // Tipos de arquivo aceitos
  const acceptedTypes = {
    text: '.txt,.doc,.docx',
    audio: '.mp3,.wav,.m4a,.ogg,.flac',
    video: '.mp4,.avi,.mov,.mkv,.webm'
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setError('');
    setUploading(true);
    setUploadProgress(0);

    try {
      // Determinar tipo de arquivo
      const fileType = getFileType(file);
      
      // Criar FormData
      const formData = new FormData();
      formData.append('file', file);
      formData.append('paciente_id', patientId);
      formData.append('file_type', fileType);

      // Upload com progress
      const response = await api.post('/evolucoes/upload-arquivo', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(progress);
        }
      });

      setUploading(false);
      setProcessing(true);

      // Aguardar processamento
      const processResult = response.data;
      setResult(processResult);
      setShowResultDialog(true);

    } catch (err) {
      if(process.env.NODE_ENV!=='production')console.error('Erro no upload:', err);
      setError(err.response?.data?.error || 'Erro ao fazer upload do arquivo');
    } finally {
      setUploading(false);
      setProcessing(false);
      setUploadProgress(0);
    }
  };

  const getFileType = (file) => {
    const extension = file.name.toLowerCase().split('.').pop();
    
    if (['txt', 'doc', 'docx'].includes(extension)) return 'text';
    if (['mp3', 'wav', 'm4a', 'ogg', 'flac'].includes(extension)) return 'audio';
    if (['mp4', 'avi', 'mov', 'mkv', 'webm'].includes(extension)) return 'video';
    
    return 'unknown';
  };

  const getFileIcon = (type) => {
    switch (type) {
      case 'text': return <TextIcon />;
      case 'audio': return <AudioIcon />;
      case 'video': return <VideoIcon />;
      default: return <UploadIcon />;
    }
  };

  const handleApplyResult = () => {
    if (result && onProcessComplete) {
      onProcessComplete(result);
    }
    setShowResultDialog(false);
    setResult(null);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Upload de Arquivos com IA
      </Typography>
      
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Envie arquivos de texto, áudio ou vídeo para processamento automático com IA
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Área de upload */}
      <Paper
        sx={{
          p: 3,
          border: '2px dashed',
          borderColor: 'primary.main',
          borderRadius: 2,
          textAlign: 'center',
          cursor: uploading || processing ? 'not-allowed' : 'pointer',
          opacity: uploading || processing ? 0.6 : 1,
          '&:hover': {
            bgcolor: 'action.hover'
          }
        }}
      >
        <input
          type="file"
          id="file-upload"
          style={{ display: 'none' }}
          accept={`${acceptedTypes.text},${acceptedTypes.audio},${acceptedTypes.video}`}
          onChange={handleFileUpload}
          disabled={uploading || processing}
        />
        
        <label htmlFor="file-upload" style={{ cursor: 'inherit' }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
            {uploading || processing ? (
              <CircularProgress size={48} />
            ) : (
              <UploadIcon sx={{ fontSize: 48, color: 'primary.main' }} />
            )}
            
            <Typography variant="h6">
              {uploading ? 'Enviando arquivo...' : 
               processing ? 'Processando com IA...' : 
               'Clique para enviar arquivo'}
            </Typography>
            
            <Typography variant="body2" color="text.secondary">
              Suporte para: Texto (.txt, .doc, .docx), Áudio (.mp3, .wav, .m4a), Vídeo (.mp4, .avi, .mov)
            </Typography>
          </Box>
        </label>

        {uploading && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress variant="determinate" value={uploadProgress} />
            <Typography variant="body2" sx={{ mt: 1 }}>
              {uploadProgress}% enviado
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Tipos de arquivo aceitos */}
      <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        <Chip
          icon={<TextIcon />}
          label="Texto"
          variant="outlined"
          size="small"
        />
        <Chip
          icon={<AudioIcon />}
          label="Áudio"
          variant="outlined"
          size="small"
        />
        <Chip
          icon={<VideoIcon />}
          label="Vídeo"
          variant="outlined"
          size="small"
        />
      </Box>

      {/* Dialog de resultado */}
      <Dialog
        open={showResultDialog}
        onClose={() => setShowResultDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AutoAwesomeIcon color="primary" />
            Resultado do Processamento com IA
          </Box>
        </DialogTitle>
        
        <DialogContent>
          {result && (
            <Box>
              {result.transcribed_text && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Texto Transcrito:
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body2">
                      {result.transcribed_text}
                    </Typography>
                  </Paper>
                </Box>
              )}

              {result.texto_melhorado && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Texto Processado pela IA:
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'primary.50' }}>
                    <Typography variant="body1">
                      {result.texto_melhorado}
                    </Typography>
                  </Paper>
                </Box>
              )}

              {result.sugestoes && result.sugestoes.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Informações Extraídas:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {result.sugestoes.map((sugestao, index) => (
                      <Chip
                        key={index}
                        label={sugestao}
                        variant="outlined"
                        size="small"
                      />
                    ))}
                  </Box>
                </Box>
              )}

              {result.error && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  {result.error}
                </Alert>
              )}

              <Typography variant="caption" color="text.secondary">
                Fonte: {result.source || 'Arquivo processado'}
              </Typography>
            </Box>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setShowResultDialog(false)}>
            Cancelar
          </Button>
          <Button
            onClick={handleApplyResult}
            variant="contained"
            startIcon={<AutoAwesomeIcon />}
            disabled={!result?.texto_melhorado && !result?.transcribed_text}
          >
            Usar Resultado
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FileUploadManager;
