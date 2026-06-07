import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Tooltip,
  CircularProgress,
  Alert,
  TextField,
  InputAdornment,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import ImportCatalogoIA from '../components/ImportCatalogoIA';
import { buscarProdutos, listarImportLogs } from '../services/catalogoService';

const CatalogoPage = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showImportModal, setShowImportModal] = useState(false);
  const [error, setError] = useState(null);
  const [featureEnabled, setFeatureEnabled] = useState(false);
  const [logs, setLogs] = useState([]);
  const [showLogs, setShowLogs] = useState(false);

  const checkFeatureFlag = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${process.env.REACT_APP_API_URL || 'http://localhost:5000'}/api/admin/feature-flags`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (response.ok) {
        const data = await response.json();
        const flag = (data.features || []).find((f) => f.name === 'sga_catalog_extraction');
        setFeatureEnabled(flag ? flag.enabled : false);
      }
    } catch (e) {
      // Se não conseguir verificar, assume false
      setFeatureEnabled(false);
    }
  };

  useEffect(() => {
    fetchProducts();
    checkFeatureFlag();
  }, []);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const data = await buscarProdutos({ limit: 200 });
      setProducts(data.produtos || []);
    } catch (err) {
      setError('Erro ao carregar produtos');
    } finally {
      setLoading(false);
    }
  };

  const fetchLogs = async () => {
    try {
      const data = await listarImportLogs(1, 10);
      setLogs(data.logs || []);
      setShowLogs(true);
    } catch (err) {
      // Silencioso — logs são opcionais
    }
  };

  const filteredProducts = products.filter((p) => {
    const term = searchTerm.toLowerCase();
    return (
      (p.nome && p.nome.toLowerCase().includes(term)) ||
      (p.categoria && p.categoria.toLowerCase().includes(term)) ||
      (p.fabricante && p.fabricante.toLowerCase().includes(term))
    );
  });

  return (
    <Box sx={{ py: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>
          📦 Catálogo de Produtos
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          {featureEnabled && (
            <Button
              variant="outlined"
              color="secondary"
              startIcon={<AutoFixHighIcon />}
              onClick={() => setShowImportModal(true)}
            >
              Importar por IA
            </Button>
          )}
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => { /* TODO: abrir modal de cadastro manual */ }}
          >
            Novo Produto
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <TextField
        fullWidth
        placeholder="Buscar por nome, categoria ou fabricante..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        sx={{ mb: 3 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
        }}
      />

      {loading ? (
        <Box sx={{ textAlign: 'center', py: 6 }}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow sx={{ bgcolor: 'grey.50' }}>
                <TableCell>Nome</TableCell>
                <TableCell>Categoria</TableCell>
                <TableCell>Unidade</TableCell>
                <TableCell>Concentração</TableCell>
                <TableCell>Fabricante</TableCell>
                <TableCell>Código de Barras</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredProducts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                    <Typography color="text.secondary">
                      Nenhum produto encontrado.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredProducts.map((product) => (
                  <TableRow key={product.id} hover>
                    <TableCell>
                      <Typography fontWeight={600}>{product.nome}</Typography>
                      {product.descricao && (
                        <Typography variant="caption" color="text.secondary">
                          {product.descricao}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      {product.categoria ? (
                        <Chip label={product.categoria} size="small" variant="outlined" />
                      ) : (
                        <Typography variant="caption" color="text.secondary">—</Typography>
                      )}
                    </TableCell>
                    <TableCell>{product.unidade || '—'}</TableCell>
                    <TableCell>{product.concentracao || '—'}</TableCell>
                    <TableCell>{product.fabricante || '—'}</TableCell>
                    <TableCell>{product.codigo_barras || '—'}</TableCell>
                    <TableCell>
                      <Chip
                        label={product.ativo ? 'Ativo' : 'Inativo'}
                        color={product.ativo ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Logs de importação (admin) */}
      {showLogs && logs.length > 0 && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            📝 Últimas Importações por IA
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: 'grey.50' }}>
                  <TableCell>Data</TableCell>
                  <TableCell>Arquivo</TableCell>
                  <TableCell>Detectados</TableCell>
                  <TableCell>Importados</TableCell>
                  <TableCell>Usuário</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {logs.map((log) => (
                  <TableRow key={log.id} hover>
                    <TableCell>{new Date(log.created_at).toLocaleString('pt-BR')}</TableCell>
                    <TableCell>{log.filename || '—'}</TableCell>
                    <TableCell>{log.detected_count}</TableCell>
                    <TableCell>{log.imported_count}</TableCell>
                    <TableCell>{log.user_nome || '—'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      <ImportCatalogoIA
        open={showImportModal}
        onClose={() => setShowImportModal(false)}
        onImportSuccess={() => {
          fetchProducts();
          fetchLogs();
        }}
        featureEnabled={featureEnabled}
      />
    </Box>
  );
};

export default CatalogoPage;
