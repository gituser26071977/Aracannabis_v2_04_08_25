import React, { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Button,
  Typography,
  Paper,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Checkbox,
  TextField,
  Chip,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import DeleteIcon from '@mui/icons-material/Delete';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import { extrairCatalogoIA, importarProdutosSelecionados } from '../services/catalogoService';

const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'application/vnd.ms-excel': ['.xls'],
};

const CATEGORIAS = [
  'óleo', 'flor', 'pomada', 'gummy', 'pet', 'vaporizador',
  'medicamento', 'insumo', 'equipamento', 'suplemento', 'outro',
];

const ImportCatalogoIA = ({ open, onClose, onImportSuccess, featureEnabled = false }) => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState([]);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [error, setError] = useState(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);

  useEffect(() => {
    if (!open) {
      resetState();
    }
  }, [open]);

  const resetState = () => {
    setFile(null);
    setProducts([]);
    setSelectedIds(new Set());
    setError(null);
    setImportResult(null);
  };

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setError(null);
      setProducts([]);
      setSelectedIds(new Set());
      setImportResult(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles: 1,
    maxSize: 20 * 1024 * 1024,
  });

  const handleExtract = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setImportResult(null);

    try {
      const response = await extrairCatalogoIA(file);
      const detected = response.detected_products || [];
      // Adiciona id temporário para controle de seleção
      const withIds = detected.map((p, idx) => ({
        ...p,
        _id: idx,
        _selected: true,
      }));
      setProducts(withIds);
      setSelectedIds(new Set(withIds.map((p) => p._id)));
    } catch (err) {
      setError(err.message || 'Erro ao processar arquivo com IA');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedIds(new Set(products.map((p) => p._id)));
    } else {
      setSelectedIds(new Set());
    }
  };

  const handleUpdateProduct = (id, field, value) => {
    setProducts((prev) =>
      prev.map((p) => (p._id === id ? { ...p, [field]: value } : p))
    );
  };

  const handleRemoveProduct = (id) => {
    setProducts((prev) => prev.filter((p) => p._id !== id));
    setSelectedIds((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
  };

  const handleImport = async () => {
    const toImport = products
      .filter((p) => selectedIds.has(p._id))
      .map((p) => ({
        nome: p.nome,
        categoria: p.categoria,
        descricao: p.descricao,
        unidade: p.unidade,
        concentracao: p.concentracao,
        fabricante: p.fabricante,
        codigo_barras: p.codigo_barras,
        tipo: p.tipo || 'oleo',
      }));

    if (toImport.length === 0) {
      setError('Selecione pelo menos um produto para importar');
      return;
    }

    setImporting(true);
    setError(null);

    try {
      const result = await importarProdutosSelecionados(toImport);
      setImportResult(result);
      if (result.success && onImportSuccess) {
        onImportSuccess(result);
      }
    } catch (err) {
      setError(err.message || 'Erro ao importar produtos');
    } finally {
      setImporting(false);
    }
  };

  if (!featureEnabled) {
    return (
      <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
        <DialogTitle>Importar Catálogo por IA</DialogTitle>
        <DialogContent>
          <Alert severity="info">
            Esta funcionalidade não está disponível no momento. Entre em contato com o administrador.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Fechar</Button>
        </DialogActions>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth scroll="paper">
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <AutoFixHighIcon color="primary" />
        Importar Catálogo por IA
      </DialogTitle>

      <DialogContent dividers>
        {/* Dropzone */}
        {products.length === 0 && !importResult && (
          <Box sx={{ mb: 2 }}>
            <Paper
              {...getRootProps()}
              sx={{
                border: '2px dashed',
                borderColor: isDragActive ? 'primary.main' : 'grey.300',
                borderRadius: 2,
                p: 4,
                textAlign: 'center',
                cursor: 'pointer',
                bgcolor: isDragActive ? 'action.hover' : 'background.paper',
                transition: 'all 0.2s',
              }}
            >
              <input {...getInputProps()} />
              <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
              {isDragActive ? (
                <Typography>Solte o arquivo aqui...</Typography>
              ) : (
                <>
                  <Typography variant="h6" gutterBottom>
                    Arraste e solte um arquivo de catálogo
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    PDF, PNG, JPG ou XLSX (máx. 20MB)
                  </Typography>
                </>
              )}
            </Paper>

            {file && (
              <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Typography variant="subtitle2">Arquivo selecionado:</Typography>
                <Typography variant="body1">{file.name}</Typography>
                <Typography variant="caption" color="text.secondary">
                  Tamanho: {(file.size / 1024).toFixed(2)} KB
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Button
                    variant="contained"
                    onClick={handleExtract}
                    disabled={loading}
                    startIcon={loading ? <CircularProgress size={18} /> : <AutoFixHighIcon />}
                  >
                    {loading ? 'IA analisando seu catálogo...' : 'Extrair produtos com IA'}
                  </Button>
                </Box>
              </Box>
            )}
          </Box>
        )}

        {/* Loading durante extração */}
        {loading && (
          <Box sx={{ textAlign: 'center', py: 6 }}>
            <CircularProgress size={48} sx={{ mb: 2 }} />
            <Typography variant="h6">IA analisando seu catálogo...</Typography>
            <Typography variant="body2" color="text.secondary">
              Estamos extraindo produtos do documento. Isso pode levar alguns segundos.
            </Typography>
          </Box>
        )}

        {/* Erro */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Preview de produtos */}
        {products.length > 0 && !importResult && (
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                {products.length} produto(s) detectado(s)
              </Typography>
              <Button size="small" onClick={resetState} color="error">
                Limpar e tentar outro arquivo
              </Button>
            </Box>

            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'grey.50' }}>
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={selectedIds.size === products.length && products.length > 0}
                        indeterminate={selectedIds.size > 0 && selectedIds.size < products.length}
                        onChange={(e) => handleSelectAll(e.target.checked)}
                      />
                    </TableCell>
                    <TableCell>Nome</TableCell>
                    <TableCell>Categoria</TableCell>
                    <TableCell>Descrição</TableCell>
                    <TableCell>Unidade</TableCell>
                    <TableCell>Concentração</TableCell>
                    <TableCell>Fabricante</TableCell>
                    <TableCell align="right">Ações</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {products.map((product) => (
                    <TableRow
                      key={product._id}
                      selected={selectedIds.has(product._id)}
                      hover
                    >
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={selectedIds.has(product._id)}
                          onChange={() => handleToggleSelect(product._id)}
                        />
                      </TableCell>
                      <TableCell>
                        <TextField
                          value={product.nome || ''}
                          onChange={(e) => handleUpdateProduct(product._id, 'nome', e.target.value)}
                          variant="standard"
                          size="small"
                          fullWidth
                          placeholder="Nome do produto"
                        />
                      </TableCell>
                      <TableCell>
                        <TextField
                          select
                          value={product.categoria || 'outro'}
                          onChange={(e) => handleUpdateProduct(product._id, 'categoria', e.target.value)}
                          variant="standard"
                          size="small"
                          fullWidth
                          SelectProps={{ native: true }}
                        >
                          {CATEGORIAS.map((cat) => (
                            <option key={cat} value={cat}>
                              {cat}
                            </option>
                          ))}
                        </TextField>
                      </TableCell>
                      <TableCell>
                        <TextField
                          value={product.descricao || ''}
                          onChange={(e) => handleUpdateProduct(product._id, 'descricao', e.target.value)}
                          variant="standard"
                          size="small"
                          fullWidth
                          placeholder="Descrição"
                        />
                      </TableCell>
                      <TableCell>
                        <TextField
                          value={product.unidade || ''}
                          onChange={(e) => handleUpdateProduct(product._id, 'unidade', e.target.value)}
                          variant="standard"
                          size="small"
                          fullWidth
                          placeholder="ml, g, un..."
                        />
                      </TableCell>
                      <TableCell>
                        <TextField
                          value={product.concentracao || ''}
                          onChange={(e) => handleUpdateProduct(product._id, 'concentracao', e.target.value)}
                          variant="standard"
                          size="small"
                          fullWidth
                          placeholder="3000mg, 10%..."
                        />
                      </TableCell>
                      <TableCell>
                        <TextField
                          value={product.fabricante || ''}
                          onChange={(e) => handleUpdateProduct(product._id, 'fabricante', e.target.value)}
                          variant="standard"
                          size="small"
                          fullWidth
                          placeholder="Fabricante"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Remover">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleRemoveProduct(product._id)}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Chip
                label={`${selectedIds.size} selecionado(s)`}
                color="primary"
                variant="outlined"
              />
            </Box>
          </Box>
        )}

        {/* Resultado da importação */}
        {importResult && (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Alert severity={importResult.success ? 'success' : 'error'} sx={{ mb: 2 }}>
              {importResult.success
                ? `${importResult.imported_count} produto(s) importado(s) com sucesso!`
                : 'Erro ao importar produtos.'}
            </Alert>
            {importResult.errors && importResult.errors.length > 0 && (
              <Box sx={{ textAlign: 'left', mt: 2 }}>
                <Typography variant="subtitle2" color="error">
                  Erros:
                </Typography>
                {importResult.errors.map((err, idx) => (
                  <Typography key={idx} variant="caption" display="block">
                    • {err}
                  </Typography>
                ))}
              </Box>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={importing}>
          {importResult ? 'Fechar' : 'Cancelar'}
        </Button>
        {!importResult && products.length > 0 && (
          <Button
            variant="contained"
            onClick={handleImport}
            disabled={selectedIds.size === 0 || importing}
            startIcon={importing ? <CircularProgress size={18} /> : <AutoFixHighIcon />}
          >
            {importing
              ? 'Importando...'
              : `Importar ${selectedIds.size} selecionado(s)`}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default ImportCatalogoIA;
