import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  CloudUpload,
  CloudDownload,
  FileUpload,
  Description,
  TableChart,
  Chat,
  Send,
  CheckCircle,
  Error,
  Info
} from '@mui/icons-material';
import api from '../services/api';

import useNotifier from '../hooks/useNotifier';
const ImportExportManager = ({ patientId, patientName }) => {
  const { notify, NotifierElement } = useNotifier();
  const [exportDialog, setExportDialog] = useState(false);
  const [importDialog, setImportDialog] = useState(false);
  const [chatDialog, setChatDialog] = useState(false);
  const [loading, setLoading] = useState(false);
  const [exportType, setExportType] = useState('json');
  const [csvType, setCsvType] = useState('evolucoes');
  const [selectedFile, setSelectedFile] = useState(null);
  const [importResult, setImportResult] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  const handleExport = async () => {
    setLoading(true);
    try {
      let url = '';
      let filename = '';
      
      if (exportType === 'json') {
        url = `/import-export/export/patient/${patientId}`;
        filename = `${patientName}_dados_completos.json`;
      } else {
        url = `/import-export/export/csv/patient/${patientId}?type=${csvType}`;
        filename = `${patientName}_${csvType}.csv`;
      }

      const response = await api.get(url, {
        responseType: 'blob'
      });

      // Criar link para download
      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

      setExportDialog(false);
    } catch (error) {
      if(process.env.NODE_ENV!=='production')console.error('Erro ao exportar:', error);
      notify('Erro ao exportar dados', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    setSelectedFile(file);
  };

  const handleImport = async () => {
    if (!selectedFile) {
      notify('Selecione um arquivo para importar', 'warning');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await api.post(`/import-export/import/patient/${patientId}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setImportResult(response.data);
    } catch (error) {
      if(process.env.NODE_ENV!=='production')console.error('Erro ao importar:', error);
      setImportResult({
        error: 'Erro ao importar arquivo',
        details: error.response?.data?.error || error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!currentQuestion.trim()) return;

    setChatLoading(true);
    const userMessage = { type: 'user', content: currentQuestion };
    setChatMessages(prev => [...prev, userMessage]);

    try {
      const response = await api.post(`/import-export/chat/patient/${patientId}`, {
        question: currentQuestion
      });

      const aiMessage = {
        type: 'ai',
        content: response.data.response.resposta || response.data.response,
        insights: response.data.response.insights || [],
        suggestions: response.data.response.sugestoes || [],
        context: response.data.context_summary
      };

      setChatMessages(prev => [...prev, aiMessage]);
      setCurrentQuestion('');
    } catch (error) {
      if(process.env.NODE_ENV!=='production')console.error('Erro no chat:', error);
      const errorMessage = {
        type: 'error',
        content: 'Erro ao processar pergunta: ' + (error.response?.data?.error || error.message)
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setChatLoading(false);
    }
  };

  const predefinedQuestions = [
    "Como está a evolução do tratamento?",
    "Qual a eficácia das dosagens atuais?",
    "Há algum padrão nos sintomas?",
    "Quais são as tendências recentes?",
    "Preciso ajustar alguma dosagem?"
  ];

  return (
    <Box>

        <NotifierElement />      <Typography variant="h6" gutterBottom>
        Importação, Exportação e Chat com IA
      </Typography>

      <Grid container spacing={2}>
        {/* Exportação */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <CloudDownload sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Exportar Dados</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" mb={2}>
                Exporte todos os dados do paciente em diferentes formatos
              </Typography>
              <Button
                variant="contained"
                fullWidth
                onClick={() => setExportDialog(true)}
                startIcon={<CloudDownload />}
              >
                Exportar
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Importação */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <CloudUpload sx={{ mr: 1, color: 'secondary.main' }} />
                <Typography variant="h6">Importar Dados</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" mb={2}>
                Importe dados com análise automática de IA
              </Typography>
              <Button
                variant="contained"
                color="secondary"
                fullWidth
                onClick={() => setImportDialog(true)}
                startIcon={<CloudUpload />}
              >
                Importar
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Chat com IA */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Chat sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6">Chat com IA</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" mb={2}>
                Converse com os dados do paciente usando IA
              </Typography>
              <Button
                variant="contained"
                color="success"
                fullWidth
                onClick={() => setChatDialog(true)}
                startIcon={<Chat />}
              >
                Iniciar Chat
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Dialog de Exportação */}
      <Dialog open={exportDialog} onClose={() => setExportDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Exportar Dados do Paciente</DialogTitle>
        <DialogContent>
          <Box mt={2}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Formato de Exportação</InputLabel>
              <Select
                value={exportType}
                onChange={(e) => setExportType(e.target.value)}
                label="Formato de Exportação"
              >
                <MenuItem value="json">JSON Completo</MenuItem>
                <MenuItem value="csv">CSV Específico</MenuItem>
              </Select>
            </FormControl>

            {exportType === 'csv' && (
              <FormControl fullWidth margin="normal">
                <InputLabel>Tipo de Dados CSV</InputLabel>
                <Select
                  value={csvType}
                  onChange={(e) => setCsvType(e.target.value)}
                  label="Tipo de Dados CSV"
                >
                  <MenuItem value="evolucoes">Evoluções</MenuItem>
                  <MenuItem value="dosagens">Dosagens</MenuItem>
                  <MenuItem value="sintomas">Sintomas</MenuItem>
                </Select>
              </FormControl>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialog(false)}>Cancelar</Button>
          <Button
            onClick={handleExport}
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : <CloudDownload />}
          >
            {loading ? 'Exportando...' : 'Exportar'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog de Importação */}
      <Dialog open={importDialog} onClose={() => setImportDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Importar Dados com Análise de IA</DialogTitle>
        <DialogContent>
          <Box mt={2}>
            <Alert severity="info" sx={{ mb: 2 }}>
              Formatos suportados: JSON, CSV, TXT, MD, PDF, DOC, DOCX, MP3, WAV, MP4, AVI. A IA analisará automaticamente o conteúdo.
            </Alert>

            <Button
              variant="outlined"
              component="label"
              fullWidth
              sx={{ mb: 2, p: 2 }}
              startIcon={<FileUpload />}
            >
              {selectedFile ? selectedFile.name : 'Selecionar Arquivo'}
              <input
                type="file"
                hidden
                accept=".json,.csv,.txt,.md,.pdf,.doc,.docx,.mp3,.wav,.mp4,.avi,.mov,.m4a,.ogg"
                onChange={handleFileSelect}
              />
            </Button>

            {importResult && (
              <Box mt={2}>
                {importResult.error ? (
                  <Alert severity="error">
                    <Typography variant="subtitle2">Erro na Importação</Typography>
                    <Typography variant="body2">{importResult.error}</Typography>
                    {importResult.details && (
                      <Typography variant="caption">{importResult.details}</Typography>
                    )}
                  </Alert>
                ) : (
                  <Alert severity="success">
                    <Typography variant="subtitle2">Importação Concluída</Typography>
                    <List dense>
                      <ListItem>
                        <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
                        <ListItemText primary={`${importResult.evolucoes_criadas} evoluções criadas`} />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
                        <ListItemText primary={`${importResult.dosagens_criadas} dosagens criadas`} />
                      </ListItem>
                      {importResult.sintomas_criados > 0 && (
                        <ListItem>
                          <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
                          <ListItemText primary={`${importResult.sintomas_criados} sintomas criados`} />
                        </ListItem>
                      )}
                    </List>
                    {importResult.erros && importResult.erros.length > 0 && (
                      <Box mt={1}>
                        <Typography variant="caption" color="error">
                          Erros: {importResult.erros.join(', ')}
                        </Typography>
                      </Box>
                    )}
                  </Alert>
                )}
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setImportDialog(false);
            setSelectedFile(null);
            setImportResult(null);
          }}>
            Fechar
          </Button>
          <Button
            onClick={handleImport}
            variant="contained"
            disabled={!selectedFile || loading}
            startIcon={loading ? <CircularProgress size={20} /> : <CloudUpload />}
          >
            {loading ? 'Importando...' : 'Importar'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog de Chat com IA */}
      <Dialog open={chatDialog} onClose={() => setChatDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Chat com IA - Análise dos Dados</DialogTitle>
        <DialogContent>
          <Box sx={{ height: 400, overflow: 'auto', mb: 2, p: 1, border: '1px solid #ddd', borderRadius: 1 }}>
            {chatMessages.length === 0 ? (
              <Box textAlign="center" py={4}>
                <Chat sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                <Typography variant="body2" color="text.secondary">
                  Faça uma pergunta sobre os dados do paciente
                </Typography>
              </Box>
            ) : (
              chatMessages.map((message, index) => (
                <Box key={index} mb={2}>
                  {message.type === 'user' && (
                    <Box display="flex" justifyContent="flex-end">
                      <Chip
                        label={message.content}
                        color="primary"
                        sx={{ maxWidth: '80%', height: 'auto', '& .MuiChip-label': { whiteSpace: 'normal' } }}
                      />
                    </Box>
                  )}
                  {message.type === 'ai' && (
                    <Box>
                      <Alert severity="info" sx={{ mb: 1 }}>
                        <Typography variant="body2">{message.content}</Typography>
                        {message.insights && message.insights.length > 0 && (
                          <Box mt={1}>
                            <Typography variant="caption" fontWeight="bold">Insights:</Typography>
                            <List dense>
                              {message.insights.map((insight, i) => (
                                <ListItem key={i} sx={{ py: 0 }}>
                                  <ListItemText primary={insight} />
                                </ListItem>
                              ))}
                            </List>
                          </Box>
                        )}
                        {message.suggestions && message.suggestions.length > 0 && (
                          <Box mt={1}>
                            <Typography variant="caption" fontWeight="bold">Sugestões:</Typography>
                            <List dense>
                              {message.suggestions.map((suggestion, i) => (
                                <ListItem key={i} sx={{ py: 0 }}>
                                  <ListItemText primary={suggestion} />
                                </ListItem>
                              ))}
                            </List>
                          </Box>
                        )}
                      </Alert>
                    </Box>
                  )}
                  {message.type === 'error' && (
                    <Alert severity="error">
                      <Typography variant="body2">{message.content}</Typography>
                    </Alert>
                  )}
                </Box>
              ))
            )}
            {chatLoading && (
              <Box display="flex" alignItems="center" gap={1}>
                <CircularProgress size={20} />
                <Typography variant="body2">IA analisando...</Typography>
              </Box>
            )}
          </Box>

          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>Perguntas Sugeridas:</Typography>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {predefinedQuestions.map((question, index) => (
                <Chip
                  key={index}
                  label={question}
                  variant="outlined"
                  size="small"
                  onClick={() => setCurrentQuestion(question)}
                  sx={{ cursor: 'pointer' }}
                />
              ))}
            </Box>
          </Box>

          <Box display="flex" gap={1}>
            <TextField
              fullWidth
              placeholder="Digite sua pergunta..."
              value={currentQuestion}
              onChange={(e) => setCurrentQuestion(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              disabled={chatLoading}
            />
            <Button
              variant="contained"
              onClick={handleSendMessage}
              disabled={!currentQuestion.trim() || chatLoading}
              startIcon={chatLoading ? <CircularProgress size={20} /> : <Send />}
            >
              Enviar
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setChatDialog(false);
            setChatMessages([]);
            setCurrentQuestion('');
          }}>
            Fechar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ImportExportManager;
