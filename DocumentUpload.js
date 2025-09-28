import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Button,
  IconButton,
  Card,
  CardContent,
  CardMedia,
  CardActions,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Tooltip,
  Divider
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  Download as DownloadIcon,
  Edit as EditIcon,
  Image as ImageIcon,
  PictureAsPdf as PdfIcon,
  Description as FileIcon,
  Save as SaveIcon,
  Cancel as CancelIcon
} from '@mui/icons-material';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const DocumentUpload = ({ pacienteId, pacienteNome }) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [openUploadDialog, setOpenUploadDialog] = useState(false);
  const [openViewDialog, setOpenViewDialog] = useState(false);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [deleteId, setDeleteId] = useState(null);
  const [documentTitle, setDocumentTitle] = useState('');
  const [documentType, setDocumentType] = useState('');
  const [documentDescription, setDocumentDescription] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);

  // Tipos de documentos disponíveis
  const documentTypes = [
    { value: 'exame_laboratorial', label: 'Exame Laboratorial' },
    { value: 'exame_imagem', label: 'Exame de Imagem' },
    { value: 'laudo_medico', label: 'Laudo Médico' },
    { value: 'receita', label: 'Receita Médica' },
    { value: 'outro', label: 'Outro Documento' }
  ];

  // Buscar documentos do paciente
  useEffect(() => {
    const fetchDocuments = async () => {
      setLoading(true);
      setError('');
      
      try {
        // Aqui seria feita a chamada à API para buscar os documentos
        // const response = await documentService.listarDocumentos(pacienteId);
        // setDocuments(response.data.documentos);
        
        // Dados simulados para demonstração
        const mockDocuments = [
          {
            id: 1,
            paciente_id: pacienteId,
            titulo: 'Hemograma Completo',
            tipo: 'exame_laboratorial',
            descricao: 'Exame de sangue realizado em 15/04/2025',
            data_upload: new Date(),
            arquivo_url: 'https://example.com/hemograma.pdf',
            arquivo_tipo: 'application/pdf',
            arquivo_nome: 'hemograma_15042025.pdf',
            thumbnail_url: 'https://example.com/thumbnails/pdf.png'
          },
          {
            id: 2,
            paciente_id: pacienteId,
            titulo: 'Ressonância Magnética',
            tipo: 'exame_imagem',
            descricao: 'RM de crânio para avaliação de cefaleia crônica',
            data_upload: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000), // 15 dias atrás
            arquivo_url: 'https://example.com/rm.jpg',
            arquivo_tipo: 'image/jpeg',
            arquivo_nome: 'rm_cranio.jpg',
            thumbnail_url: 'https://example.com/thumbnails/rm_thumb.jpg'
          },
          {
            id: 3,
            paciente_id: pacienteId,
            titulo: 'Laudo Neurológico',
            tipo: 'laudo_medico',
            descricao: 'Avaliação neurológica para tratamento com cannabis medicinal',
            data_upload: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 dias atrás
            arquivo_url: 'https://example.com/laudo.pdf',
            arquivo_tipo: 'application/pdf',
            arquivo_nome: 'laudo_neurologico.pdf',
            thumbnail_url: 'https://example.com/thumbnails/pdf.png'
          }
        ];
        
        setDocuments(mockDocuments);
      } catch (err) {
        console.error('Erro ao buscar documentos:', err);
        setError('Não foi possível carregar os documentos do paciente.');
      } finally {
        setLoading(false);
      }
    };
    
    if (pacienteId) {
      fetchDocuments();
    }
  }, [pacienteId]);

  // Abrir diálogo de upload
  const handleOpenUploadDialog = () => {
    setDocumentTitle('');
    setDocumentType('');
    setDocumentDescription('');
    setSelectedFile(null);
    setUploadProgress(0);
    setOpenUploadDialog(true);
  };

  // Fechar diálogo de upload
  const handleCloseUploadDialog = () => {
    if (isUploading) return; // Evitar fechar durante upload
    setOpenUploadDialog(false);
  };

  // Abrir diálogo de visualização
  const handleOpenViewDialog = (document) => {
    setSelectedDocument(document);
    setOpenViewDialog(true);
  };

  // Fechar diálogo de visualização
  const handleCloseViewDialog = () => {
    setOpenViewDialog(false);
    setSelectedDocument(null);
  };

  // Abrir confirmação de exclusão
  const handleConfirmDelete = (id) => {
    setDeleteId(id);
    setConfirmDeleteOpen(true);
  };

  // Fechar confirmação de exclusão
  const handleCloseConfirmDelete = () => {
    setConfirmDeleteOpen(false);
    setDeleteId(null);
  };

  // Manipular seleção de arquivo
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      
      // Sugerir título baseado no nome do arquivo
      if (!documentTitle) {
        const fileName = file.name.split('.')[0].replace(/_/g, ' ');
        setDocumentTitle(fileName);
      }
      
      // Sugerir tipo baseado na extensão
      if (!documentType) {
        const extension = file.name.split('.').pop().toLowerCase();
        if (['jpg', 'jpeg', 'png'].includes(extension)) {
          setDocumentType('exame_imagem');
        } else if (['pdf'].includes(extension)) {
          setDocumentType('laudo_medico');
        }
      }
    }
  };

  // Upload de documento
  const handleUploadDocument = async () => {
    if (!selectedFile || !documentTitle || !documentType) {
      setError('Por favor, preencha todos os campos obrigatórios e selecione um arquivo.');
      return;
    }
    
    setIsUploading(true);
    setError('');
    
    // Simulação de progresso de upload
    const simulateProgress = () => {
      let progress = 0;
      const interval = setInterval(() => {
        progress += 10;
        setUploadProgress(progress);
        
        if (progress >= 100) {
          clearInterval(interval);
          
          // Simulação de upload concluído
          setTimeout(() => {
            try {
              // Aqui seria feita a chamada à API para upload do documento
              // const formData = new FormData();
              // formData.append('arquivo', selectedFile);
              // formData.append('titulo', documentTitle);
              // formData.append('tipo', documentType);
              // formData.append('descricao', documentDescription);
              // const response = await documentService.uploadDocumento(pacienteId, formData);
              
              // Simulação para demonstração
              const newDocument = {
                id: Date.now(), // ID temporário
                paciente_id: pacienteId,
                titulo: documentTitle,
                tipo: documentType,
                descricao: documentDescription,
                data_upload: new Date(),
                arquivo_url: URL.createObjectURL(selectedFile),
                arquivo_tipo: selectedFile.type,
                arquivo_nome: selectedFile.name,
                thumbnail_url: selectedFile.type.startsWith('image/') 
                  ? URL.createObjectURL(selectedFile) 
                  : 'https://example.com/thumbnails/pdf.png'
              };
              
              setDocuments([newDocument, ...documents]);
              setOpenUploadDialog(false);
              setIsUploading(false);
            } catch (err) {
              console.error('Erro ao fazer upload do documento:', err);
              setError('Não foi possível fazer o upload do documento.');
              setIsUploading(false);
            }
          }, 500);
        }
      }, 300);
    };
    
    simulateProgress();
  };

  // Excluir documento
  const handleDeleteDocument = async () => {
    if (!deleteId) return;
    
    setLoading(true);
    setError('');
    
    try {
      // await documentService.excluirDocumento(deleteId);
      
      // Simulação para demonstração
      setDocuments(documents.filter(doc => doc.id !== deleteId));
      
      handleCloseConfirmDelete();
    } catch (err) {
      console.error('Erro ao excluir documento:', err);
      setError('Não foi possível excluir o documento.');
    } finally {
      setLoading(false);
    }
  };

  // Formatar data
  const formatDate = (date) => {
    return format(new Date(date), "dd/MM/yyyy", { locale: ptBR });
  };

  // Obter ícone baseado no tipo de arquivo
  const getFileIcon = (fileType) => {
    if (fileType.startsWith('image/')) {
      return <ImageIcon />;
    } else if (fileType === 'application/pdf') {
      return <PdfIcon />;
    } else {
      return <FileIcon />;
    }
  };

  // Obter label do tipo de documento
  const getDocumentTypeLabel = (type) => {
    const docType = documentTypes.find(t => t.value === type);
    return docType ? docType.label : 'Documento';
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 3, borderRadius: 2, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5" component="h1" color="primary" fontWeight="bold">
            Exames e Documentos - {pacienteNome || `Paciente #${pacienteId}`}
          </Typography>
          
          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<CloudUploadIcon />}
            onClick={handleOpenUploadDialog}
          >
            Upload de Documento
          </Button>
        </Box>
        
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}
        
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : documents.length === 0 ? (
          <Card sx={{ bgcolor: '#f5f5f5', borderRadius: 2, mb: 3 }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" align="center">
                Nenhum documento ou exame encontrado
              </Typography>
              <Typography variant="body2" color="text.secondary" align="center">
                Clique em "Upload de Documento" para adicionar exames ou documentos para este paciente.
              </Typography>
            </CardContent>
          </Card>
        ) : (
          <Grid container spacing={3}>
            {documents.map((document) => (
              <Grid item xs={12} sm={6} md={4} key={document.id}>
                <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', position: 'relative' }}>
                  <CardMedia
                    component="div"
                    sx={{ 
                      height: 140, 
                      bgcolor: document.arquivo_tipo.startsWith('image/') ? 'transparent' : '#f5f5f5',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    {document.arquivo_tipo.startsWith('image/') ? (
                      <img 
                        src={document.thumbnail_url} 
                        alt={document.titulo}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    ) : (
                      <Box sx={{ fontSize: 60, color: 'primary.main' }}>
                        {getFileIcon(document.arquivo_tipo)}
                      </Box>
                    )}
                  </CardMedia>
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                      <Typography variant="subtitle1" component="h2" fontWeight="bold" noWrap>
                        {document.titulo}
                      </Typography>
                      <Chip 
                        label={formatDate(document.data_upload)} 
                        size="small" 
                        variant="outlined"
                      />
                    </Box>
                    
                    <Chip 
                      label={getDocumentTypeLabel(document.tipo)} 
                      size="small" 
                      color="primary"
                      sx={{ mb: 1 }}
                    />
                    
                    <Typography variant="body2" color="text.secondary" sx={{ 
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                    }}>
                      {document.descricao}
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Tooltip title="Visualizar">
                      <IconButton 
                        size="small" 
                        color="primary"
                        onClick={() => handleOpenViewDialog(document)}
                      >
                        <VisibilityIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Download">
                      <IconButton 
                        size="small" 
                        color="primary"
                        component="a"
                        href={document.arquivo_url}
                        download={document.arquivo_nome}
                        target="_blank"
                      >
                        <DownloadIcon />
                      </IconButton>
                    </Tooltip>
                    <Box sx={{ flexGrow: 1 }} />
                    <Tooltip title="Excluir">
                      <IconButton 
                        size="small" 
                        color="error"
                        onClick={() => handleConfirmDelete(document.id)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Paper>
      
      {/* Diálogo de Upload */}
      <Dialog open={openUploadDialog} onClose={handleCloseUploadDialog} fullWidth maxWidth="md">
        <DialogTitle>
          Upload de Documento ou Exame
        </DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}
          
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                required
                fullWidth
                label="Título do Documento"
                value={documentTitle}
                onChange={(e) => setDocumentTitle(e.target.value)}
                disabled={isUploading}
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Tipo de Documento</InputLabel>
                <Select
                  value={documentType}
                  
(Content truncated due to size limit. Use line ranges to read in chunks)