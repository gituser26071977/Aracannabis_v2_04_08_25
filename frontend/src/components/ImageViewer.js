import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardMedia,
  CardContent,
  Typography,
  Button,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert,
  Chip,
  IconButton
} from '@mui/material';
import {
  ZoomIn,
  GetApp,
  TextFields,
  Close
} from '@mui/icons-material';
import { exameService } from '../services/api';

const ImageViewer = ({ exameId }) => {
  const [imagens, setImagens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const [openImageDialog, setOpenImageDialog] = useState(false);
  const [ocrResults, setOcrResults] = useState(null);
  const [processingOCR, setProcessingOCR] = useState(false);

  useEffect(() => {
    const carregarImagens = async () => {
      try {
        setLoading(true);
        const response = await exameService.listarImagens(exameId);
        setImagens(response);
        setError('');
      } catch (err) {
        setError('Falha ao carregar imagens do exame');
        console.error('Erro ao carregar imagens:', err);
      } finally {
        setLoading(false);
      }
    };

    if (exameId) {
      carregarImagens();
    }
  }, [exameId]);

  const handleImageClick = (imagem) => {
    setSelectedImage(imagem);
    setOpenImageDialog(true);
  };

  const handleProcessOCR = async () => {
    try {
      setProcessingOCR(true);
      const response = await exameService.processarOCR(exameId);
      setOcrResults(response);
    } catch (err) {
      setError('Falha ao processar OCR');
      console.error('Erro ao processar OCR:', err);
    } finally {
      setProcessingOCR(false);
    }
  };

  const getImageUrl = (filename) => {
    return exameService.obterUrlImagem(filename);
  };

  const isImageFile = (filename) => {
    const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'tiff', 'tif', 'ico'];
    const extension = filename.split('.').pop().toLowerCase();
    return imageExtensions.includes(extension);
  };

  const getFileIcon = (filename) => {
    const extension = filename.split('.').pop().toLowerCase();
    switch (extension) {
      case 'pdf':
        return '📄';
      case 'doc':
      case 'docx':
        return '📝';
      case 'txt':
        return '📃';
      default:
        return '📁';
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  if (imagens.length === 0) {
    return (
      <Alert severity="info" sx={{ mt: 2 }}>
        Nenhuma imagem encontrada para este exame.
      </Alert>
    );
  }

  return (
    <Box sx={{ mt: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="subtitle1" fontWeight="bold">
          Arquivos do Exame ({imagens.length})
        </Typography>
        <Button
          variant="outlined"
          startIcon={processingOCR ? <CircularProgress size={16} /> : <TextFields />}
          onClick={handleProcessOCR}
          disabled={processingOCR}
          size="small"
        >
          {processingOCR ? 'Processando...' : 'Processar OCR'}
        </Button>
      </Box>

      <Grid container spacing={2}>
        {imagens.map((imagem) => (
          <Grid item xs={12} sm={6} md={4} key={imagem.id}>
            <Card sx={{ height: '100%', cursor: 'pointer' }} onClick={() => handleImageClick(imagem)}>
              {isImageFile(imagem.arquivo_nome) ? (
                <CardMedia
                  component="img"
                  height="200"
                  image={getImageUrl(imagem.arquivo_caminho)}
                  alt={imagem.arquivo_nome}
                  sx={{ objectFit: 'cover' }}
                />
              ) : (
                <Box
                  sx={{
                    height: 200,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: 'grey.100',
                    fontSize: '4rem'
                  }}
                >
                  {getFileIcon(imagem.arquivo_nome)}
                </Box>
              )}
              <CardContent>
                <Typography variant="body2" noWrap title={imagem.arquivo_nome}>
                  {imagem.arquivo_nome}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {new Date(imagem.created_at).toLocaleDateString('pt-BR')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Resultados do OCR */}
      {ocrResults && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
            Resultados do OCR
          </Typography>
          <Grid container spacing={2}>
            {ocrResults.resultados_ocr.map((resultado, index) => (
              <Grid item xs={12} key={index}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle2">
                        {resultado.arquivo_nome}
                      </Typography>
                      <Chip
                        label={resultado.status}
                        color={resultado.status === 'sucesso' ? 'success' : resultado.status === 'erro' ? 'error' : 'default'}
                        size="small"
                      />
                    </Box>
                    {resultado.texto_extraido && (
                      <Typography variant="body2" sx={{ mt: 1, p: 1, backgroundColor: 'grey.50', borderRadius: 1 }}>
                        {resultado.texto_extraido}
                      </Typography>
                    )}
                    {resultado.erro && (
                      <Alert severity="error" sx={{ mt: 1 }}>
                        {resultado.erro}
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Dialog para visualizar imagem em tamanho maior */}
      <Dialog
        open={openImageDialog}
        onClose={() => setOpenImageDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">
            {selectedImage?.arquivo_nome}
          </Typography>
          <IconButton onClick={() => setOpenImageDialog(false)}>
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {selectedImage && (
            <Box>
              {isImageFile(selectedImage.arquivo_nome) ? (
                <Box sx={{ textAlign: 'center' }}>
                  <img
                    src={getImageUrl(selectedImage.arquivo_caminho)}
                    alt={selectedImage.arquivo_nome}
                    style={{
                      maxWidth: '100%',
                      maxHeight: '70vh',
                      objectFit: 'contain'
                    }}
                  />
                </Box>
              ) : (
                <Box sx={{ textAlign: 'center', p: 4 }}>
                  <Typography variant="h1" sx={{ fontSize: '6rem', mb: 2 }}>
                    {getFileIcon(selectedImage.arquivo_nome)}
                  </Typography>
                  <Typography variant="h6" gutterBottom>
                    {selectedImage.arquivo_nome}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Arquivo não é uma imagem. Clique em "Download" para baixar.
                  </Typography>
                </Box>
              )}
              
              {selectedImage.laudo && (
                <Box sx={{ mt: 2, p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Laudo/Observações:
                  </Typography>
                  <Typography variant="body2">
                    {selectedImage.laudo}
                  </Typography>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            startIcon={<GetApp />}
            onClick={() => {
              if (selectedImage) {
                window.open(getImageUrl(selectedImage.arquivo_caminho), '_blank');
              }
            }}
          >
            Download
          </Button>
          <Button onClick={() => setOpenImageDialog(false)}>
            Fechar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ImageViewer;
