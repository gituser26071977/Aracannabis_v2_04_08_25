import React, { useState } from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  Paper, 
  Grid,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  Alert,
  Divider
} from '@mui/material';
import { 
  DeleteOutline as DeleteIcon,
  GetApp as DownloadIcon,
  Edit as EditIcon,
  History as HistoryIcon
} from '@mui/icons-material';

const DataSubjectRights = ({ pacienteId, pacienteData, onRequestAction }) => {
  const [openDialog, setOpenDialog] = useState(false);
  const [dialogType, setDialogType] = useState('');
  const [requestReason, setRequestReason] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const handleOpenDialog = (type) => {
    setDialogType(type);
    setRequestReason('');
    setSuccessMessage('');
    setErrorMessage('');
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
  };

  const handleReasonChange = (e) => {
    setRequestReason(e.target.value);
  };

  const handleSubmitRequest = () => {
    if (!requestReason.trim()) {
      setErrorMessage('Por favor, forneça um motivo para sua solicitação.');
      return;
    }

    try {
      // Aqui seria chamada a função para processar a solicitação
      if (onRequestAction) {
        onRequestAction(dialogType, requestReason, pacienteId);
      }

      // Mensagens de sucesso baseadas no tipo de solicitação
      const messages = {
        access: 'Solicitação de acesso aos dados enviada com sucesso. Você receberá os dados em até 15 dias.',
        correction: 'Solicitação de correção de dados enviada com sucesso. Processaremos sua solicitação em até 5 dias úteis.',
        deletion: 'Solicitação de exclusão de dados enviada com sucesso. Processaremos sua solicitação em até 5 dias úteis.',
        portability: 'Solicitação de portabilidade de dados enviada com sucesso. Você receberá seus dados em formato estruturado em até 15 dias.'
      };

      setSuccessMessage(messages[dialogType] || 'Solicitação enviada com sucesso.');
      setRequestReason('');
      
      // Fechar o diálogo após 3 segundos em caso de sucesso
      setTimeout(() => {
        setOpenDialog(false);
        setSuccessMessage('');
      }, 3000);
    } catch (error) {
      setErrorMessage('Erro ao processar sua solicitação. Por favor, tente novamente.');
    }
  };

  const getDialogTitle = () => {
    const titles = {
      access: 'Solicitar Acesso aos Dados',
      correction: 'Solicitar Correção de Dados',
      deletion: 'Solicitar Exclusão de Dados',
      portability: 'Solicitar Portabilidade de Dados'
    };
    return titles[dialogType] || 'Solicitação';
  };

  const getDialogDescription = () => {
    const descriptions = {
      access: 'Você está solicitando acesso a todos os seus dados pessoais que processamos. Por favor, explique o motivo da sua solicitação:',
      correction: 'Você está solicitando a correção de dados inexatos ou desatualizados. Por favor, explique quais dados precisam ser corrigidos e por quê:',
      deletion: 'Você está solicitando a exclusão dos seus dados pessoais. Por favor, explique o motivo da sua solicitação:',
      portability: 'Você está solicitando a portabilidade dos seus dados para outro fornecedor de serviço. Por favor, explique o motivo e indique o destinatário:'
    };
    return descriptions[dialogType] || 'Por favor, explique o motivo da sua solicitação:';
  };

  return (
    <Box sx={{ mt: 3 }}>
      <Paper elevation={2} sx={{ p: 3, borderRadius: 2, border: '1px solid #e0e0e0' }}>
        <Typography variant="h6" color="primary" gutterBottom>
          Seus Direitos como Titular de Dados
        </Typography>
        
        <Typography variant="body2" color="text.secondary" paragraph>
          De acordo com a Lei Geral de Proteção de Dados (LGPD - Lei 13.709/2018), você tem direitos específicos em relação aos seus dados pessoais:
        </Typography>
        
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} sm={6}>
            <Button 
              variant="outlined" 
              color="primary" 
              startIcon={<DownloadIcon />}
              fullWidth
              onClick={() => handleOpenDialog('access')}
              sx={{ justifyContent: 'flex-start', textAlign: 'left', py: 1 }}
            >
              Solicitar Acesso aos Dados
            </Button>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Button 
              variant="outlined" 
              color="primary" 
              startIcon={<EditIcon />}
              fullWidth
              onClick={() => handleOpenDialog('correction')}
              sx={{ justifyContent: 'flex-start', textAlign: 'left', py: 1 }}
            >
              Solicitar Correção de Dados
            </Button>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Button 
              variant="outlined" 
              color="error" 
              startIcon={<DeleteIcon />}
              fullWidth
              onClick={() => handleOpenDialog('deletion')}
              sx={{ justifyContent: 'flex-start', textAlign: 'left', py: 1 }}
            >
              Solicitar Exclusão de Dados
            </Button>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Button 
              variant="outlined" 
              color="primary" 
              startIcon={<HistoryIcon />}
              fullWidth
              onClick={() => handleOpenDialog('portability')}
              sx={{ justifyContent: 'flex-start', textAlign: 'left', py: 1 }}
            >
              Solicitar Portabilidade de Dados
            </Button>
          </Grid>
        </Grid>
        
        <Divider sx={{ my: 2 }} />
        
        <Typography variant="body2" color="text.secondary">
          Para mais informações sobre seus direitos, consulte nossa{' '}
          <Button 
            component="a" 
            href="/privacy-policy" 
            color="primary"
            sx={{ p: 0, minWidth: 'auto', fontWeight: 'bold', textTransform: 'none' }}
          >
            Política de Privacidade
          </Button>.
        </Typography>
      </Paper>
      
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{getDialogTitle()}</DialogTitle>
        <DialogContent>
          {successMessage && (
            <Alert severity="success" sx={{ mb: 2 }}>
              {successMessage}
            </Alert>
          )}
          
          {errorMessage && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {errorMessage}
            </Alert>
          )}
          
          <Typography variant="body2" color="text.secondary" paragraph sx={{ mt: 1 }}>
            {getDialogDescription()}
          </Typography>
          
          <TextField
            autoFocus
            margin="dense"
            id="reason"
            label="Motivo da solicitação"
            type="text"
            fullWidth
            multiline
            rows={4}
            variant="outlined"
            value={requestReason}
            onChange={handleReasonChange}
            disabled={!!successMessage}
          />
          
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
            Sua solicitação será processada de acordo com a LGPD e nossa política de privacidade.
            Entraremos em contato através do e-mail cadastrado para fornecer mais informações.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} color="inherit" disabled={!!successMessage}>
            Cancelar
          </Button>
          <Button 
            onClick={handleSubmitRequest} 
            color="primary" 
            variant="contained"
            disabled={!!successMessage}
          >
            Enviar Solicitação
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DataSubjectRights;
