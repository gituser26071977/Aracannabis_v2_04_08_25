import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  TextField,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Card,
  CardContent,
  CardActions,
  Chip,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  NoteAdd as NoteAddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Person as PersonIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  History as HistoryIcon,
  FilterList as FilterIcon
} from '@mui/icons-material';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';

const EvolutionHistory = ({ pacienteId, pacienteNome }) => {
  const [evolucoes, setEvolucoes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [openFilters, setOpenFilters] = useState(false);
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [profissionalFilter, setProfissionalFilter] = useState('');
  const [profissionais, setProfissionais] = useState([]);

  // Buscar evoluções do paciente
  useEffect(() => {
    const fetchEvolucoes = async () => {
      setLoading(true);
      setError('');
      
      try {
        // Aqui seria feita a chamada à API para buscar as evoluções
        // const response = await evolucaoService.listarEvolucoes(pacienteId);
        // setEvolucoes(response.data.evolucoes);
        
        // Dados simulados para demonstração
        const mockEvolucoes = [
          {
            id: 1,
            paciente_id: pacienteId,
            profissional_id: 1,
            profissional_nome: 'Dr. João Silva',
            data_evolucao: new Date(),
            nota_evolucao: 'Paciente relata melhora significativa na qualidade do sono após ajuste na dosagem. Mantém queixa de ansiedade leve durante o dia, mas com intensidade reduzida. Recomendado manter dosagem atual e reavaliar em 15 dias.'
          },
          {
            id: 2,
            paciente_id: pacienteId,
            profissional_id: 2,
            profissional_nome: 'Dra. Ana Ferreira',
            data_evolucao: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000), // 15 dias atrás
            nota_evolucao: 'Primeira consulta após início do tratamento. Paciente relata melhora parcial dos sintomas de ansiedade, mas ainda com dificuldades para dormir. Ajustada dosagem para 15 gotas 2x ao dia. Solicitados exames complementares para próxima consulta.'
          },
          {
            id: 3,
            paciente_id: pacienteId,
            profissional_id: 1,
            profissional_nome: 'Dr. João Silva',
            data_evolucao: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 dias atrás
            nota_evolucao: 'Consulta inicial. Paciente apresenta quadro de ansiedade generalizada e insônia. Iniciado tratamento com CBD 20mg/ml, 10 gotas 2x ao dia. Orientado sobre possíveis efeitos colaterais e necessidade de acompanhamento regular.'
          },
          {
            id: 4,
            paciente_id: pacienteId,
            profissional_id: 3,
            profissional_nome: 'Dr. Carlos Mendes',
            data_evolucao: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000), // 45 dias atrás
            nota_evolucao: 'Avaliação inicial. Paciente encaminhado por neurologista para tratamento de dores crônicas e distúrbios do sono. Histórico de tratamentos convencionais sem resposta satisfatória. Indicado início de tratamento com cannabis medicinal.'
          }
        ];
        
        setEvolucoes(mockEvolucoes);
        
        // Extrair lista de profissionais únicos
        const uniqueProfissionais = [...new Set(mockEvolucoes.map(ev => ev.profissional_nome))];
        setProfissionais(uniqueProfissionais);
      } catch (err) {
        console.error('Erro ao buscar evoluções:', err);
        setError('Não foi possível carregar o histórico de evoluções médicas.');
      } finally {
        setLoading(false);
      }
    };
    
    if (pacienteId) {
      fetchEvolucoes();
    }
  }, [pacienteId]);

  // Alternar exibição de filtros
  const handleToggleFilters = () => {
    setOpenFilters(!openFilters);
  };

  // Aplicar filtros
  const handleApplyFilters = () => {
    // Aqui seria feita a chamada à API com os filtros
    // Por enquanto, apenas simulamos o filtro no frontend
    setLoading(true);
    
    setTimeout(() => {
      setLoading(false);
    }, 500);
  };

  // Limpar filtros
  const handleClearFilters = () => {
    setStartDate(null);
    setEndDate(null);
    setProfissionalFilter('');
  };

  // Formatar data
  const formatDate = (date) => {
    return format(new Date(date), "dd 'de' MMMM 'de' yyyy 'às' HH:mm", { locale: ptBR });
  };

  // Filtrar evoluções
  const filteredEvolucoes = evolucoes.filter(evolucao => {
    let passesFilter = true;
    
    if (startDate) {
      passesFilter = passesFilter && new Date(evolucao.data_evolucao) >= startDate;
    }
    
    if (endDate) {
      passesFilter = passesFilter && new Date(evolucao.data_evolucao) <= endDate;
    }
    
    if (profissionalFilter) {
      passesFilter = passesFilter && evolucao.profissional_nome === profissionalFilter;
    }
    
    return passesFilter;
  });

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ptBR}>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Paper elevation={3} sx={{ p: 3, borderRadius: 2, mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h5" component="h1" color="primary" fontWeight="bold">
              Histórico de Evoluções - {pacienteNome || `Paciente #${pacienteId}`}
            </Typography>
            
            <Button 
              variant="outlined" 
              color="primary" 
              startIcon={<FilterIcon />}
              onClick={handleToggleFilters}
            >
              Filtros
            </Button>
          </Box>
          
          {openFilters && (
            <Box sx={{ mb: 3, p: 2, bgcolor: '#f5f5f5', borderRadius: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Filtrar Evoluções
              </Typography>
              
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={6} md={3}>
                  <DatePicker
                    label="Data Inicial"
                    value={startDate}
                    onChange={setStartDate}
                    slotProps={{
                      textField: {
                        size: "small",
                        fullWidth: true
                      }
                    }}
                  />
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <DatePicker
                    label="Data Final"
                    value={endDate}
                    onChange={setEndDate}
                    slotProps={{
                      textField: {
                        size: "small",
                        fullWidth: true
                      }
                    }}
                  />
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel id="profissional-select-label">Profissional</InputLabel>
                    <Select
                      labelId="profissional-select-label"
                      id="profissional-select"
                      value={profissionalFilter}
                      label="Profissional"
                      onChange={(e) => setProfissionalFilter(e.target.value)}
                    >
                      <MenuItem value="">Todos</MenuItem>
                      {profissionais.map((prof) => (
                        <MenuItem key={prof} value={prof}>{prof}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button 
                      variant="contained" 
                      color="primary"
                      onClick={handleApplyFilters}
                      fullWidth
                    >
                      Aplicar
                    </Button>
                    
                    <Button 
                      variant="outlined"
                      onClick={handleClearFilters}
                      fullWidth
                    >
                      Limpar
                    </Button>
                  </Box>
                </Grid>
              </Grid>
            </Box>
          )}
          
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}
          
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
              <CircularProgress />
            </Box>
          ) : filteredEvolucoes.length === 0 ? (
            <Card sx={{ bgcolor: '#f5f5f5', borderRadius: 2, mb: 3 }}>
              <CardContent>
                <Typography variant="h6" color="text.secondary" align="center">
                  Nenhuma evolução médica encontrada
                </Typography>
                <Typography variant="body2" color="text.secondary" align="center">
                  {evolucoes.length > 0 
                    ? 'Tente ajustar os filtros para ver mais resultados.' 
                    : 'Ainda não há evoluções médicas registradas para este paciente.'}
                </Typography>
              </CardContent>
            </Card>
          ) : (
            <>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Mostrando {filteredEvolucoes.length} evolução(ões) de um total de {evolucoes.length}
              </Typography>
              
              <List sx={{ width: '100%' }}>
                {filteredEvolucoes.map((evolucao, index) => (
                  <React.Fragment key={evolucao.id}>
                    {index > 0 && <Divider variant="inset" component="li" />}
                    <ListItem 
                      alignItems="flex-start"
                    >
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: 'primary.main' }}>
                          <PersonIcon />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Typography variant="subtitle1" color="primary" component="span">
                              {evolucao.profissional_nome}
                            </Typography>
                            <Chip 
                              icon={<HistoryIcon fontSize="small" />}
                              label={formatDate(evolucao.data_evolucao)}
                              size="small"
                              variant="outlined"
                              sx={{ ml: 2 }}
                            />
                          </Box>
                        }
                        secondary={
                          <Typography
                            sx={{ display: 'inline', whiteSpace: 'pre-line', mt: 1 }}
                            component="span"
                            variant="body2"
                            color="text.primary"
                          >
                            {evolucao.nota_evolucao}
                          </Typography>
                        }
                      />
                    </ListItem>
                  </React.Fragment>
                ))}
              </List>
            </>
          )}
        </Paper>
        
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Aracannabis © {new Date().getFullYear()} - Sistema de Controle de Pacientes
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Dados protegidos conforme LGPD (Lei 13.709/2018)
          </Typography>
        </Box>
      </Container>
    </LocalizationProvider>
  );
};

export default EvolutionHistory;
