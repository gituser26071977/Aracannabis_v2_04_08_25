/**
 * Componente de Upload de Catálogo de Produtos
 * Suporta: PDF, XLSX, CSV, DOCX, TXT
 */
import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  Alert,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Chip,
  Divider,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import { uploadCatalogo } from '../../services/catalogoService';

const CatalogoUpload = ({ onUploadSuccess }) => {
  const [file, setFile] = useState(null);
  const [empresaOrigem, setEmpresaOrigem] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setError(null);
      setResult(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    maxFiles: 1,
  });

  const handleUpload = async () => {
    if (!file) {
      setError('Selecione um arquivo para upload');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await uploadCatalogo(file, empresaOrigem);
      setResult(response);
      
      if (response.success && onUploadSuccess) {
        onUploadSuccess(response);
      }
    } catch (err) {
      setError(err.message || 'Erro ao processar o catálogo');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'concluido':
        return 'success';
      case 'parcial':
        return 'warning';
      case 'erro':
        return 'error';
      default:
        return 'info';
    }
  };

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Importar Catálogo de Produtos
      </Typography>
      
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Formatos suportados: PDF, Excel (XLSX/XLS), CSV, Word (DOCX), TXT
      </Typography>

      {/* Área de Drop */}
      <Box
        {...getRootProps()}
        sx={{
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          borderRadius: 2,
          p: 3,
          textAlign: 'center',
          cursor: 'pointer',
          bgcolor: isDragActive ? 'action.hover' : 'background.paper',
          transition: 'all 0.2s',
          mb: 2,
        }}
      >
        <input {...getInputProps()} />
        <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
        
        {isDragActive ? (
          <Typography>Solte o arquivo aqui...</Typography>
        ) : (
          <Typography>
            Arraste e solte um arquivo aqui, ou clique para selecionar
          </Typography>
        )}
      </Box>

      {/* Arquivo selecionado */}
      {file && (
        <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="subtitle2">Arquivo selecionado:</Typography>
          <Typography variant="body1">{file.name}</Typography>
          <Typography variant="caption" color="text.secondary">
            Tamanho: {(file.size / 1024).toFixed(2)} KB
          </Typography>
        </Box>
      )}

      {/* Campo de empresa */}
      <TextField
        fullWidth
        label="Empresa/Origem (opcional)"
        placeholder="Ex: Prisma, Phexia, Verd..."
        value={empresaOrigem}
        onChange={(e) => setEmpresaOrigem(e.target.value)}
        sx={{ mb: 2 }}
        helperText="Informe a empresa/fabricante do catálogo para melhor organização"
      />

      {/* Botão de upload */}
      <Button
        variant="contained"
        fullWidth
        onClick={handleUpload}
        disabled={!file || loading}
        startIcon={loading ? <CircularProgress size={20} /> : <CloudUploadIcon />}
      >
        {loading ? 'Processando...' : 'Processar Catálogo'}
      </Button>

      {/* Mensagens de erro */}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      {/* Resultado do processamento */}
      {result && (
        <Box sx={{ mt: 3 }}>
          <Divider sx={{ my: 2 }} />
          
          <Alert severity={getStatusColor(result.status)} sx={{ mb: 2 }}>
            <Typography variant="subtitle2">
              Processamento {result.status === 'concluido' ? 'Concluído' : 
                           result.status === 'parcial' ? 'Parcial' : 'Finalizado'}
            </Typography>
          </Alert>

          {result.produtos_importados > 0 && (
            <Box sx={{ mb: 2 }}>
              <Chip
                icon={<CheckCircleIcon />}
                label={`${result.produtos_importados} produtos importados`}
                color="success"
                sx={{ mr: 1, mb: 1 }}
              />
              {result.produtos_atualizados > 0 && (
                <Chip
                  label={`${result.produtos_atualizados} atualizados`}
                  color="info"
                  sx={{ mb: 1 }}
                />
              )}
            </Box>
          )}

          {/* Erros individuais */}
          {result.erros && result.erros.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" color="error" gutterBottom>
                Erros encontrados:
              </Typography>
              <List dense>
                {result.erros.map((erro, index) => (
                  <ListItem key={index}>
                    <ErrorIcon color="error" sx={{ mr: 1 }} />
                    <ListItemText
                      primary={erro}
                      primaryTypographyProps={{ variant: 'body2' }}
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          {/* Detalhes técnicos (colapsável) */}
          {result.detalhes && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Detalhes técnicos:
              </Typography>
              <Typography variant="caption" component="pre" sx={{ display: 'block', mt: 1 }}>
                {JSON.stringify(result.detalhes, null, 2)}
              </Typography>
            </Box>
          )}
        </Box>
      )}
    </Paper>
  );
};

export default CatalogoUpload;