/**
 * Componente de Listagem e Busca de Produtos
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Chip,
  IconButton,
  Pagination,
  Alert,
  CircularProgress,
  Slider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Compare as CompareIcon,
  CheckCircle as CheckCircleIcon,
  Science as ScienceIcon,
  LocalPharmacy as PharmacyIcon,
} from '@mui/icons-material';
import { buscarProdutos, listarMarcas, listarCategorias, validarProduto, compararProdutos } from '../../services/catalogoService';

const ProdutoList = ({ onSelectProduct, onCompareProducts, modoSelecao = false }) => {
  // Estados
  const [produtos, setProdutos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filtros, setFiltros] = useState({
    nome: '',
    marca: '',
    categoria: '',
    cbd_min: '',
    cbd_max: '',
    thc_min: '',
    thc_max: '',
    quimiotipo: '',
    via_administracao: '',
    indicacao: '',
  });
  const [marcas, setMarcas] = useState([]);
  const [categorias, setCategorias] = useState([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [produtosSelecionados, setProdutosSelecionados] = useState([]);
  const [validando, setValidando] = useState(null);
  const [dialogComparacao, setDialogComparacao] = useState(null);

  const itemsPerPage = 12;

  // Carrega marcas e categorias
  useEffect(() => {
    const carregarOpcoes = async () => {
      try {
        const [marcasRes, categoriasRes] = await Promise.all([
          listarMarcas(),
          listarCategorias(),
        ]);
        setMarcas(marcasRes.marcas || []);
        setCategorias(categoriasRes.categorias || []);
      } catch (err) {
        console.error('Erro ao carregar opções:', err);
      }
    };
    carregarOpcoes();
  }, []);

  // Busca produtos
  const buscar = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const filtrosLimpos = Object.fromEntries(
        Object.entries(filtros).filter(([_, v]) => v !== '')
      );
      
      const response = await buscarProdutos({
        ...filtrosLimpos,
        limit: itemsPerPage,
      });
      
      setProdutos(response.produtos || []);
      setTotal(response.total || 0);
    } catch (err) {
      setError(err.message || 'Erro ao buscar produtos');
    } finally {
      setLoading(false);
    }
  }, [filtros]);

  useEffect(() => {
    buscar();
  }, [buscar, page]);

  // Handlers
  const handleFiltroChange = (campo, valor) => {
    setFiltros(prev => ({ ...prev, [campo]: valor }));
    setPage(1);
  };

  const handleLimparFiltros = () => {
    setFiltros({
      nome: '',
      marca: '',
      categoria: '',
      cbd_min: '',
      cbd_max: '',
      thc_min: '',
      thc_max: '',
      quimiotipo: '',
      via_administracao: '',
      indicacao: '',
    });
    setPage(1);
  };

  const handleValidar = async (produtoId) => {
    setValidando(produtoId);
    try {
      const resultado = await validarProduto(produtoId);
      alert(`Validação: ${resultado.validacao?.validacao?.status || 'Concluída'}`);
    } catch (err) {
      alert('Erro na validação: ' + err.message);
    } finally {
      setValidando(null);
    }
  };

  const handleSelecionar = (produto) => {
    if (modoSelecao && onSelectProduct) {
      onSelectProduct(produto);
      return;
    }

    const jaSelecionado = produtosSelecionados.find(p => p.id === produto.id);
    if (jaSelecionado) {
      setProdutosSelecionados(prev => prev.filter(p => p.id !== produto.id));
    } else {
      if (produtosSelecionados.length < 3) {
        setProdutosSelecionados(prev => [...prev, produto]);
      } else {
        alert('Máximo de 3 produtos para comparação');
      }
    }
  };

  const handleComparar = async () => {
    if (produtosSelecionados.length < 2) {
      alert('Selecione pelo menos 2 produtos para comparar');
      return;
    }

    try {
      const resultado = await compararProdutos(produtosSelecionados.map(p => p.id));
      setDialogComparacao(resultado);
    } catch (err) {
      alert('Erro na comparação: ' + err.message);
    }
  };

  const getQuimiotipoColor = (tipo) => {
    if (!tipo) return 'default';
    if (tipo.includes('I (THC)')) return 'error';
    if (tipo.includes('II (THC+CBD)')) return 'warning';
    if (tipo.includes('III (CBD)')) return 'success';
    if (tipo.includes('IV')) return 'info';
    return 'default';
  };

  return (
    <Box>
      {/* Filtros */}
      <Accordion defaultExpanded sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FilterIcon />
            <Typography variant="h6">Filtros de Busca</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Nome/Marca"
                value={filtros.nome}
                onChange={(e) => handleFiltroChange('nome', e.target.value)}
                placeholder="Buscar produto..."
              />
            </Grid>
            
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Marca</InputLabel>
                <Select
                  value={filtros.marca}
                  onChange={(e) => handleFiltroChange('marca', e.target.value)}
                  label="Marca"
                >
                  <MenuItem value="">Todas</MenuItem>
                  {marcas.map(marca => (
                    <MenuItem key={marca} value={marca}>{marca}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Categoria</InputLabel>
                <Select
                  value={filtros.categoria}
                  onChange={(e) => handleFiltroChange('categoria', e.target.value)}
                  label="Categoria"
                >
                  <MenuItem value="">Todas</MenuItem>
                  {categorias.map(cat => (
                    <MenuItem key={cat} value={cat}>{cat}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="CBD Mínimo (mg)"
                type="number"
                value={filtros.cbd_min}
                onChange={(e) => handleFiltroChange('cbd_min', e.target.value)}
              />
            </Grid>
            
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="CBD Máximo (mg)"
                type="number"
                value={filtros.cbd_max}
                onChange={(e) => handleFiltroChange('cbd_max', e.target.value)}
              />
            </Grid>
            
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="THC Mínimo (mg)"
                type="number"
                value={filtros.thc_min}
                onChange={(e) => handleFiltroChange('thc_min', e.target.value)}
              />
            </Grid>
            
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="THC Máximo (mg)"
                type="number"
                value={filtros.thc_max}
                onChange={(e) => handleFiltroChange('thc_max', e.target.value)}
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Quimiotipo</InputLabel>
                <Select
                  value={filtros.quimiotipo}
                  onChange={(e) => handleFiltroChange('quimiotipo', e.target.value)}
                  label="Quimiotipo"
                >
                  <MenuItem value="">Todos</MenuItem>
                  <MenuItem value="Tipo I">Tipo I (THC)</MenuItem>
n                  <MenuItem value="Tipo II">Tipo II (THC+CBD)</MenuItem>
                  <MenuItem value="Tipo III">Tipo III (CBD)</MenuItem>
                  <MenuItem value="Tipo IV">Tipo IV (CBG)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Via de Administração</InputLabel>
                <Select
                  value={filtros.via_administracao}
                  onChange={(e) => handleFiltroChange('via_administracao', e.target.value)}
                  label="Via de Administração"
                >
                  <MenuItem value="">Todas</MenuItem>
                  <MenuItem value="Sublingual">Sublingual</MenuItem>
                  <MenuItem value="Oral">Oral</MenuItem>
                  <MenuItem value="Tópica">Tópica</MenuItem>
                  <MenuItem value="Inalatória">Inalatória</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Indicação"
                value={filtros.indicacao}
                onChange={(e) => handleFiltroChange('indicacao', e.target.value)}
                placeholder="Ex: dor, ansiedade, insônia..."
              />
            </Grid>
          </Grid>

          <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              startIcon={<SearchIcon />}
              onClick={buscar}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Buscar'}
            </Button>
            <Button variant="outlined" onClick={handleLimparFiltros}>
              Limpar Filtros
            </Button>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Produtos Selecionados para Comparação */}
      {produtosSelecionados.length > 0 && !modoSelecao && (
        <Box sx={{ mb: 2, p: 2, bgcolor: 'primary.light', borderRadius: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="subtitle1">
              {produtosSelecionados.length} produto(s) selecionado(s) para comparação
            </Typography>
            <Box>
              <Button
                variant="contained"
                size="small"
                startIcon={<CompareIcon />}
                onClick={handleComparar}
                sx={{ mr: 1 }}
              >
                Comparar
              </Button>
              <Button
                variant="outlined"
                size="small"
                onClick={() => setProdutosSelecionados([])}
              >
                Limpar
              </Button>
            </Box>
          </Box>
          <Box sx={{ mt: 1 }}>
            {produtosSelecionados.map(p => (
              <Chip
                key={p.id}
                label={p.nome}
                onDelete={() => handleSelecionar(p)}
                sx={{ mr: 1, mb: 1 }}
              />
            ))}
n          </Box>
        </Box>
      )}

      {/* Lista de Produtos */}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Grid container spacing={2}>
        {produtos.map((produto) => {
          const selecionado = produtosSelecionados.find(p => p.id === produto.id);
          
          return (
            <Grid item xs={12} md={6} lg={4} key={produto.id}>
              <Card 
                variant={selecionado ? 'elevation' : 'outlined'}
                sx={{ 
                  cursor: 'pointer',
                  borderColor: selecionado ? 'primary.main' : undefined,
                  borderWidth: selecionado ? 2 : 1,
                }}
                onClick={() => handleSelecionar(produto)}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Typography variant="h6" component="div" noWrap sx={{ flex: 1 }}>
                      {produto.nome}
                    </Typography>
                    {produto.verificado && (
                      <Tooltip title="Produto verificado">
                        <CheckCircleIcon color="success" />
                      </Tooltip>
                    )}
                  </Box>

                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    {produto.marca}
                  </Typography>

                  <Box sx={{ mb: 1 }}>
n                    <Chip
                      size="small"
                      label={produto.quimiotipo || 'N/A'}
                      color={getQuimiotipoColor(produto.quimiotipo)}
                      sx={{ mr: 1 }}
                    />
                    <Chip
                      size="small"
                      label={produto.categoria || 'N/A'}
                      variant="outlined"
                    />
                  </Box>

                  <Box sx={{ display: 'flex', gap: 2, mb: 1 }}>
                    {produto.cbd_total_mg > 0 && (
                      <Typography variant="body2">
                        <strong>CBD:</strong> {produto.cbd_total_mg} mg
                      </Typography>
                    )}
                    {produto.thc_total_mg > 0 && (
                      <Typography variant="body2">
                        <strong>THC:</strong> {produto.thc_total_mg} mg
                      </Typography>
                    )}
                  </Box>

                  {produto.razao_cbd_thc && (
                    <Typography variant="body2" color="text.secondary">
                      <strong>Razão CBD:THC:</strong> {produto.razao_cbd_thc}
                    </Typography>
                  )}

                  {produto.via_administracao && (
                    <Typography variant="body2" color="text.secondary">
                      <strong>Via:</strong> {produto.via_administracao}
                    </Typography>
                  )}

                  {produto.preco_referencia && (
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      <strong>Preço:</strong> R$ {parseFloat(produto.preco_referencia).toFixed(2)}
                    </Typography>
                  )}

                  {produto.indicacoes && (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      <strong>Indicações:</strong> {produto.indicacoes.substring(0, 100)}...
                    </Typography>
                  )}

                  {!modoSelecao && (
                    <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<ScienceIcon />}
n                        onClick={(e) => {
                          e.stopPropagation();
                          handleValidar(produto.id);
                        }}
                        disabled={validando === produto.id}
                      >
                        {validando === produto.id ? 'Validando...' : 'Validar'}
                      </Button>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Paginação */}
      {total > itemsPerPage && (
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
          <Pagination
            count={Math.ceil(total / itemsPerPage)}
n            page={page}
            onChange={(_, value) => setPage(value)}
            color="primary"
          />
        </Box>
      )}

      {/* Dialog de Comparação */}
      <Dialog
        open={!!dialogComparacao}
        onClose={() => setDialogComparacao(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Comparação de Produtos</DialogTitle>
        <DialogContent>
          {dialogComparacao && (
            <Box>
              <Typography variant="h6" gutterBottom>Análise Técnica</Typography>
              <pre>{JSON.stringify(dialogComparacao.comparacao_tecnica, null, 2)}</pre>
              
              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>Análise do Farmacêutico</Typography>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {dialogComparacao.analise_ia}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogComparacao(null)}>Fechar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ProdutoList;