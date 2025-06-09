import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  Alert,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  Tooltip,
  LinearProgress
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  CloudUpload as UploadIcon,
  Description as PdfIcon,
  Image as ImageIcon,
  Visibility as ViewIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon
} from '@mui/icons-material';

// Função helper para formatar data
const formatDate = (date) => {
  if (!date) return '';
  const d = new Date(date);
  return d.toISOString().split('T')[0];
};

const formatDisplayDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('pt-BR');
};

const ExameManager = ({ pacienteId }) => {
  const [exames, setExames] = useState([]);
  const [tiposExames, setTiposExames] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [editingExame, setEditingExame] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [viewContent, setViewContent] = useState('');
  const [openViewDialog, setOpenViewDialog] = useState(false);
  
  // Estados para busca
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTipo, setSelectedTipo] = useState('');
  const [dataInicio, setDataInicio] = useState('');
  const [dataFim, setDataFim] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // Estado do formulário
  const [formData, setFormData] = useState({
    tipo_exame: '',
    data_exame: formatDate(new Date()),
    data_resultado: '',
    observacoes: '',
    arquivo: null
  });

  useEffect(() => {
    if (pacienteId) {
      carregarExames();
      carregarTiposExames();
    }
  }, [pacienteId]);

  const carregarExames = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/exames/paciente/${pacienteId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setExames(data.exames || []);
      } else {
        throw new Error('Erro ao carregar exames');
      }
    } catch (error) {
      setError('Erro ao carregar exames: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const carregarTiposExames = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/exames/tipos', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setTiposExames(data.tipos_exames || []);
      }
    } catch (error) {
      console.error('Erro ao carregar tipos de exames:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.arquivo && !editingExame) {
      setError('É necessário selecionar um arquivo');
      return;
    }

    try {
      setLoading(true);
      setUploadProgress(0);
      
      const token = localStorage.getItem('token');

      if (editingExame) {
        // Para edição, usar PUT sem arquivo (apenas metadados)
        const updateData = {
          tipo_exame: formData.tipo_exame,
          data_exame: formData.data_exame,
          data_resultado: formData.data_resultado || null,
          observacoes: formData.observacoes
        };

        const response = await fetch(`/api/exames/${editingExame.id}`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(updateData)
        });

        if (!response.ok) {
          throw new Error('Erro ao atualizar exame');
        }
      } else {
        // Para criação, usar FormData com arquivo
        const formDataToSend = new FormData();
        
        formDataToSend.append('paciente_id', pacienteId);
        formDataToSend.append('tipo_exame', formData.tipo_exame);
        formDataToSend.append('data_exame', formData.data_exame);
        
        if (formData.data_resultado) {
          formDataToSend.append('data_resultado', formData.data_resultado);
        }
        
        formDataToSend.append('observacoes', formData.observacoes);
        formDataToSend.append('arquivo', formData.arquivo);

        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            setUploadProgress(percentComplete);
          }
        });

        const response = await new Promise((resolve, reject) => {
          xhr.onload = () => resolve(xhr);
          xhr.onerror = () => reject(new Error('Erro no upload'));
          
          xhr.open('POST', '/api/exames/');
          xhr.setRequestHeader('Authorization', `Bearer ${token}`);
          xhr.send(formDataToSend);
        });

        if (response.status !== 201) {
          throw new Error('Erro ao criar exame');
        }
      }

      setSuccess(editingExame ? 'Exame atualizado com sucesso!' : 'Exame criado com sucesso!');
      setOpenDialog(false);
      resetForm();
      carregarExames();
      
    } catch (error) {
      setError('Erro ao salvar exame: ' + error.message);
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  };

  const handleEdit = (exame) => {
    setEditingExame(exame);
    setFormData({
      tipo_exame: exame.tipo_exame,
      data_exame: formatDate(new Date(exame.data_exame)),
      data_resultado: exame.data_resultado ? formatDate(new Date(exame.data_resultado)) : '',
      observacoes: exame.observacoes || '',
      arquivo: null
    });
    setOpenDialog(true);
  };

  const handleDelete = async (exameId) => {
    if (!window.confirm('Tem certeza que deseja excluir este exame?')) {
      return;
    }

    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/exames/${exameId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setSuccess('Exame excluído com sucesso!');
        carregarExames();
      } else {
        throw new Error('Erro ao excluir exame');
      }
    } catch (error) {
      setError('Erro ao excluir exame: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (exameId, nomeArquivo) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/exames/${exameId}/download`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = nomeArquivo;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        throw new Error('Erro ao fazer download');
      }
    } catch (error) {
      setError('Erro ao fazer download: ' + error.message);
    }
  };

  const handleView = async (exameId) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/exames/${exameId}/view`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setViewContent(data.content || 'Conteúdo não disponível');
        setOpenViewDialog(true);
      } else {
        throw new Error('Erro ao visualizar exame');
      }
    } catch (error) {
      setError('Erro ao visualizar exame: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      tipo_exame: '',
      data_exame: formatDate(new Date()),
      data_resultado: '',
      observacoes: '',
      arquivo: null
    });
    setEditingExame(null);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    resetForm();
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleSearch = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Construir parâmetros de busca
      const params = new URLSearchParams();
      if (searchTerm) params.append('q', searchTerm);
      if (selectedTipo) params.append('tipo', selectedTipo);
      if (dataInicio) params.append('data_inicio', dataInicio);
      if (dataFim) params.append('data_fim', dataFim);
      
      const url = `/api/exames/buscar/${pacienteId}?${params.toString()}`;
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setExames(data.exames || []);
        setSuccess(`Encontrados ${data.total} exames`);
      } else {
        throw new Error('Erro ao buscar exames');
      }
    } catch (error) {
      setError('Erro ao buscar exames: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setSelectedTipo('');
    setDataInicio('');
    setDataFim('');
    setShowFilters(false);
    carregarExames(); // Recarregar todos os exames
  };

  const getFileIcon = (tipo) => {
    if (tipo && tipo.includes('pdf')) {
      return <PdfIcon color="error" />;
    }
    if (tipo && tipo.includes('image')) {
      return <ImageIcon color="primary" />;
    }
    return <ViewIcon />;
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Exames</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpenDialog(true)}
          disabled={loading}
        >
          Novo Exame
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {/* Barra de busca e filtros */}
      <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              placeholder="Buscar exames..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />
          </Grid>
          
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Tipo de Exame</InputLabel>
              <Select
                value={selectedTipo}
                onChange={(e) => setSelectedTipo(e.target.value)}
                label="Tipo de Exame"
              >
                <MenuItem value="">Todos os tipos</MenuItem>
                {tiposExames.map((tipo) => (
                  <MenuItem key={tipo} value={tipo}>
                    {tipo}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={2}>
            <Button
              variant="outlined"
              startIcon={<FilterIcon />}
              onClick={() => setShowFilters(!showFilters)}
              fullWidth
            >
              Filtros
            </Button>
          </Grid>

          <Grid item xs={12} md={2}>
            <Button
              variant="contained"
              startIcon={<SearchIcon />}
              onClick={handleSearch}
              fullWidth
              disabled={loading}
            >
              Buscar
            </Button>
          </Grid>

          <Grid item xs={12} md={1}>
            <Tooltip title="Limpar filtros">
              <IconButton onClick={handleClearFilters}>
                <ClearIcon />
              </IconButton>
            </Tooltip>
          </Grid>
        </Grid>

        {/* Filtros avançados */}
        {showFilters && (
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                label="Data início"
                type="date"
                value={dataInicio}
                onChange={(e) => setDataInicio(e.target.value)}
                fullWidth
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Data fim"
                type="date"
                value={dataFim}
                onChange={(e) => setDataFim(e.target.value)}
                fullWidth
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
          </Grid>
        )}
      </Paper>

      {exames.length === 0 ? (
        <Card>
          <CardContent>
            <Typography variant="body2" color="text.secondary" align="center">
              Nenhum exame cadastrado para este paciente.
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Tipo</TableCell>
                <TableCell>Data do Exame</TableCell>
                <TableCell>Data do Resultado</TableCell>
                <TableCell>Arquivo</TableCell>
                <TableCell>Observações</TableCell>
                <TableCell align="center">Ações</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {exames.map((exame) => (
                <TableRow key={exame.id}>
                  <TableCell>
                    <Chip label={exame.tipo_exame} size="small" />
                  </TableCell>
                  <TableCell>
                    {formatDisplayDate(exame.data_exame)}
                  </TableCell>
                  <TableCell>
                    {exame.data_resultado 
                      ? formatDisplayDate(exame.data_resultado)
                      : '-'
                    }
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      {getFileIcon(exame.arquivo_tipo)}
                      <Box>
                        <Typography variant="body2">
                          {exame.arquivo_nome}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {formatFileSize(exame.arquivo_tamanho)}
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" noWrap>
                      {exame.observacoes || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                <Tooltip title="Visualizar">
                  <IconButton
                    size="small"
                    onClick={() => handleView(exame.id)}
                  >
                    <ViewIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Download">
                  <IconButton
                    size="small"
                    onClick={() => handleDownload(exame.id, exame.arquivo_nome)}
                  >
                    <DownloadIcon />
                  </IconButton>
                </Tooltip>
                    <Tooltip title="Editar">
                      <IconButton
                        size="small"
                        onClick={() => handleEdit(exame)}
                      >
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Excluir">
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(exame.id)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Dialog para criar/editar exame */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <form onSubmit={handleSubmit}>
          <DialogTitle>
            {editingExame ? 'Editar Exame' : 'Novo Exame'}
          </DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth required>
                  <InputLabel>Tipo de Exame</InputLabel>
                  <Select
                    value={formData.tipo_exame}
                    onChange={(e) => setFormData({...formData, tipo_exame: e.target.value})}
                    label="Tipo de Exame"
                  >
                    {tiposExames.map((tipo) => (
                      <MenuItem key={tipo} value={tipo}>
                        {tipo}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  label="Data do Exame"
                  type="date"
                  value={formData.data_exame}
                  onChange={(e) => setFormData({...formData, data_exame: e.target.value})}
                  fullWidth
                  required
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  label="Data do Resultado"
                  type="date"
                  value={formData.data_resultado}
                  onChange={(e) => setFormData({...formData, data_resultado: e.target.value})}
                  fullWidth
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                {!editingExame && (
                  <Button
                    variant="outlined"
                    component="label"
                    startIcon={<UploadIcon />}
                    fullWidth
                    sx={{ height: '56px' }}
                  >
                    {formData.arquivo ? formData.arquivo.name : 'Selecionar Arquivo *'}
                    <input
                      type="file"
                      hidden
                      accept=".pdf,.jpg,.jpeg,.png,.gif,.bmp,.tiff,.webp"
                      onChange={(e) => setFormData({...formData, arquivo: e.target.files[0]})}
                    />
                  </Button>
                )}
                {editingExame && (
                  <Alert severity="info">
                    Para alterar o arquivo, exclua este exame e crie um novo.
                  </Alert>
                )}
              </Grid>

              <Grid item xs={12}>
                <TextField
                  label="Observações"
                  multiline
                  rows={3}
                  fullWidth
                  value={formData.observacoes}
                  onChange={(e) => setFormData({...formData, observacoes: e.target.value})}
                />
              </Grid>

              {uploadProgress > 0 && uploadProgress < 100 && (
                <Grid item xs={12}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <LinearProgress 
                      variant="determinate" 
                      value={uploadProgress} 
                      sx={{ flexGrow: 1 }}
                    />
                    <Typography variant="body2">
                      {Math.round(uploadProgress)}%
                    </Typography>
                  </Box>
                </Grid>
              )}
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog}>Cancelar</Button>
            <Button 
              type="submit" 
              variant="contained"
              disabled={loading || (!formData.arquivo && !editingExame)}
            >
              {loading ? <CircularProgress size={20} /> : (editingExame ? 'Atualizar' : 'Salvar')}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Dialog para visualizar conteúdo do exame */}
      <Dialog 
        open={openViewDialog} 
        onClose={() => setOpenViewDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Conteúdo do Exame</DialogTitle>
        <DialogContent>
          <Box sx={{ 
            p: 2, 
            border: '1px solid #e0e0e0', 
            borderRadius: 1, 
            minHeight: '300px',
            maxHeight: '70vh',
            overflow: 'auto',
            whiteSpace: 'pre-wrap'
          }}>
            {viewContent}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenViewDialog(false)}>Fechar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ExameManager;
