import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  Stack,
  Alert,
  Chip,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  ReceiptLong,
  TrendingUp,
  Payments,
  WarningAmber,
  Percent,
  Paid,
} from '@mui/icons-material';
import api from '../services/api';

const money = (v) =>
  v == null ? '—' : v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

function KPI({ icon, label, value, color }) {
  return (
    <Card elevation={0} sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 3 }}>
      <CardContent>
        <Stack direction="row" spacing={1} alignItems="center">
          <Box sx={{ color: color || 'primary.main' }}>{icon}</Box>
          <Box>
            <Typography variant="caption" color="text.secondary" display="block">
              {label}
            </Typography>
            <Typography variant="h6" fontWeight={800}>
              {value}
            </Typography>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}

function RelatoriosFinanceirosPage() {
  const [filtros, setFiltros] = useState({ de: '', ate: '', agrupar_por: 'profissional' });
  const [resumo, setResumo] = useState(null);
  const [receita, setReceita] = useState([]);
  const [repasse, setRepasse] = useState([]);
  const [inadimplentes, setInadimplentes] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const carregar = async () => {
    setLoading(true);
    setError('');
    const q = new URLSearchParams();
    if (filtros.de) q.append('de', filtros.de);
    if (filtros.ate) q.append('ate', filtros.ate);
    if (filtros.agrupar_por) q.append('agrupar_por', filtros.agrupar_por);
    try {
      const [rs, rc, rp, ina] = await Promise.all([
        api.get(`/faturamento/relatorios/resumo?${q}`),
        api.get(`/faturamento/relatorios/receita?${q}`),
        api.get(
          `/faturamento/relatorios/repasse?${new URLSearchParams({ de: filtros.de, ate: filtros.ate })}`,
        ),
        api.get(
          `/faturamento/relatorios/inadimplencia?${new URLSearchParams({ de: filtros.de, ate: filtros.ate })}`,
        ),
      ]);
      setResumo(rs.data);
      setReceita(rc.data.itens || []);
      setRepasse(rp.data.itens || []);
      setInadimplentes(ina.data);
    } catch (e) {
      setError(e.response?.data?.error || 'Erro ao carregar relatórios');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Box p={3}>
      <Typography variant="h4" fontWeight={800} gutterBottom>
        <ReceiptLong sx={{ verticalAlign: 'middle', mr: 1 }} />
        Relatórios Financeiros
      </Typography>

      <Stack direction="row" spacing={1} alignItems="center" mb={2} flexWrap="wrap">
        <TextField
          size="small"
          type="date"
          label="De"
          value={filtros.de}
          onChange={(e) => setFiltros({ ...filtros, de: e.target.value })}
          InputLabelProps={{ shrink: true }}
        />
        <TextField
          size="small"
          type="date"
          label="Até"
          value={filtros.ate}
          onChange={(e) => setFiltros({ ...filtros, ate: e.target.value })}
          InputLabelProps={{ shrink: true }}
        />
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel>Agrupar receita por</InputLabel>
          <Select
            value={filtros.agrupar_por}
            label="Agrupar receita por"
            onChange={(e) => setFiltros({ ...filtros, agrupar_por: e.target.value })}
          >
            <MenuItem value="profissional">Profissional</MenuItem>
            <MenuItem value="convenio">Convênio / Particular</MenuItem>
            <MenuItem value="mes">Mês</MenuItem>
          </Select>
        </FormControl>
        <Button variant="contained" onClick={carregar} disabled={loading}>
          Gerar
        </Button>
      </Stack>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {loading && <CircularProgress />}

      {resumo && (
        <Grid container spacing={2} mb={3}>
          <Grid item xs={6} sm={4} md={2}>
            <KPI
              icon={<TrendingUp />}
              label="Receita (lançada)"
              value={money(resumo.lancado)}
              color="primary.main"
            />
          </Grid>
          <Grid item xs={6} sm={4} md={2}>
            <KPI
              icon={<Payments />}
              label="Recebido"
              value={money(resumo.recebido)}
              color="success.main"
            />
          </Grid>
          <Grid item xs={6} sm={4} md={2}>
            <KPI
              icon={<WarningAmber />}
              label="A receber"
              value={money(resumo.a_receber)}
              color="warning.main"
            />
          </Grid>
          <Grid item xs={6} sm={4} md={2}>
            <KPI
              icon={<Paid />}
              label="Repasse devido"
              value={money(resumo.repasse_due)}
              color="info.main"
            />
          </Grid>
          <Grid item xs={6} sm={4} md={2}>
            <KPI
              icon={<Percent />}
              label="Repasse pago"
              value={money(resumo.repasse_pago)}
              color="text.secondary"
            />
          </Grid>
          <Grid item xs={6} sm={4} md={2}>
            <KPI
              icon={<ReceiptLong />}
              label="Lançamentos"
              value={resumo.quantidade}
              color="text.primary"
            />
          </Grid>
        </Grid>
      )}

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Card elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
            <CardContent>
              <Typography variant="h6" mb={1}>
                Receita por {filtros.agrupar_por}
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Grupo</TableCell>
                      <TableCell align="right">Lançado</TableCell>
                      <TableCell align="right">Recebido</TableCell>
                      <TableCell align="right">Qtde</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {receita.map((i) => (
                      <TableRow key={i.grupo}>
                        <TableCell>
                          <b>{i.grupo}</b>
                        </TableCell>
                        <TableCell align="right">{money(i.lancado)}</TableCell>
                        <TableCell align="right">{money(i.recebido)}</TableCell>
                        <TableCell align="right">{i.quantidade}</TableCell>
                      </TableRow>
                    ))}
                    {receita.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={4}>
                          <Typography variant="body2" color="text.secondary">
                            Sem dados no período.
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
            <CardContent>
              <Typography variant="h6" mb={1}>
                Repasse por profissional
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Profissional</TableCell>
                      <TableCell align="right">Devido</TableCell>
                      <TableCell align="right">Pago</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {repasse.map((i) => (
                      <TableRow key={i.profissional_id}>
                        <TableCell>
                          <b>{i.profissional}</b>
                        </TableCell>
                        <TableCell align="right">{money(i.repasse_due)}</TableCell>
                        <TableCell align="right">{money(i.repasse_pago)}</TableCell>
                      </TableRow>
                    ))}
                    {repasse.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={3}>
                          <Typography variant="body2" color="text.secondary">
                            Sem dados.
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
            <CardContent>
              <Typography variant="h6" mb={1}>
                Inadimplência{' '}
                {inadimplentes ? (
                  <Chip
                    size="small"
                    color="warning"
                    label={`${money(inadimplentes.total_pendente)} · ${inadimplentes.quantidade} item(ns)`}
                  />
                ) : null}
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Paciente</TableCell>
                      <TableCell>Serviço</TableCell>
                      <TableCell>Profissional</TableCell>
                      <TableCell>Modalidade</TableCell>
                      <TableCell align="right">Em aberto</TableCell>
                      <TableCell align="right">Atraso</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(inadimplentes?.itens || []).map((i, idx) => (
                      <TableRow key={idx}>
                        <TableCell>{i.paciente}</TableCell>
                        <TableCell>{i.servico}</TableCell>
                        <TableCell>{i.profissional}</TableCell>
                        <TableCell>
                          <Chip size="small" label={i.modalidade} />
                        </TableCell>
                        <TableCell align="right">{money(i.valor_aberto)}</TableCell>
                        <TableCell align="right">{i.dias_atraso}d</TableCell>
                      </TableRow>
                    ))}
                    {(!inadimplentes || inadimplentes.itens.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={6}>
                          <Typography variant="body2" color="text.secondary">
                            Nenhuma inadimplência.
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default RelatoriosFinanceirosPage;
