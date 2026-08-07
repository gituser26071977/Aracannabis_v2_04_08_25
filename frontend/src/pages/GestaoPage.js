import React from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardActionArea,
  CardContent,
  Stack,
  Chip,
} from '@mui/material';
import {
  VerifiedUser,
  PersonAdd,
  ReceiptLong,
  LocalHospital,
  Category,
  Extension,
  Settings,
  Security,
  SmartToy,
  Storefront,
  Inventory2,
  Groups,
  AdminPanelSettings,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function RoutineCard({ icon, title, description, onClick, emBreve }) {
  return (
    <Card
      elevation={0}
      sx={{ height: '100%', border: '1px solid', borderColor: 'divider', borderRadius: 3 }}
    >
      <CardActionArea
        onClick={onClick}
        disabled={emBreve}
        sx={{ p: 2, height: '100%', opacity: emBreve ? 0.55 : 1 }}
      >
        <CardContent sx={{ p: 0 }}>
          <Stack direction="row" spacing={1.5} alignItems="center" mb={1}>
            <Box
              sx={{
                width: 44,
                height: 44,
                borderRadius: 2,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: emBreve ? 'text.disabled' : 'primary.main',
                bgcolor: emBreve ? 'action.hover' : 'primary.light',
              }}
            >
              {icon}
            </Box>
            {emBreve && <Chip size="small" label="Em breve" color="default" variant="outlined" />}
          </Stack>
          <Typography variant="subtitle1" fontWeight={700}>
            {title}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {description}
          </Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}

function RoutineGroup({ title, children }) {
  return (
    <Box mb={3}>
      <Typography
        variant="overline"
        sx={{ fontWeight: 700, letterSpacing: '0.1em', color: 'text.secondary', opacity: 0.7 }}
      >
        {title}
      </Typography>
      <Grid container spacing={2} mt={0.5}>
        {children}
      </Grid>
    </Box>
  );
}

function GestaoPage() {
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const ehAdmin = currentUser?.role === 'admin' || currentUser?.role === 'superadmin';
  const ehAssistencial =
    currentUser?.perfil_efetivo === 'assistencial' ||
    (!currentUser?.perfil_efetivo && !ehAdmin && currentUser?.role !== 'profissional'
      ? false
      : (currentUser?.perfil_efetivo || 'assistencial') === 'assistencial');

  return (
    <Box p={3}>
      <Typography variant="h4" fontWeight={800} gutterBottom>
        🏢 Gestão
      </Typography>
      <Typography color="text.secondary" gutterBottom>
        Rotinas administrativas da clínica, organizadas por área.
      </Typography>

      {!ehAssistencial && (
        <RoutineGroup title="PACIENTES">
          <Grid item xs={12} sm={6} md={4}>
            <RoutineCard
              icon={<PersonAdd fontSize="large" />}
              title="Cadastro de pacientes"
              description="Cadastro com assistência de IA e upload de documentos (imagem/PDF)."
              onClick={() => navigate('/onboarding-pacientes')}
            />
          </Grid>
        </RoutineGroup>
      )}

      {!ehAssistencial && (
        <RoutineGroup title="FINANCEIRO">
          <Grid item xs={12} sm={6} md={4}>
            <RoutineCard
              icon={<ReceiptLong fontSize="large" />}
              title="Financeiro"
              description="Contas a receber, recebimentos, repasse dos profissionais e agente de consulta."
              onClick={() => navigate('/faturamento')}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <RoutineCard
              icon={<LocalHospital fontSize="large" />}
              title="Convênios & Tabela"
              description="Convênios, serviços e tabela de preços (particular e por convênio)."
              onClick={() => navigate('/faturamento')}
            />
          </Grid>
        </RoutineGroup>
      )}

      {!ehAssistencial && (
        <RoutineGroup title="OPERAÇÕES">
          <Grid item xs={12} sm={6} md={4}>
            <RoutineCard
              icon={<Inventory2 fontSize="large" />}
              title="Estoque"
              description="Controle de produtos, medicamentos e dispensação."
              onClick={() => navigate('/association/stock')}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <RoutineCard
              icon={<Storefront fontSize="large" />}
              title="Marketplace"
              description="Venda de produtos e serviços da clínica."
              emBreve
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <RoutineCard
              icon={<Groups fontSize="large" />}
              title="Gestão da Clínica"
              description="Cadastro da clínica, convites e membros da equipe."
              onClick={() => navigate('/association')}
            />
          </Grid>
        </RoutineGroup>
      )}

      <RoutineGroup title="CONFIGURAÇÕES">
        <Grid item xs={12} sm={6} md={4}>
          <RoutineCard
            icon={<LocalHospital fontSize="large" />}
            title="Configurar Receituário"
            description="Modelo do receituário e assinatura."
            onClick={() => navigate('/configuracao-prescricao')}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <RoutineCard
            icon={<Category fontSize="large" />}
            title="Catálogo → Importar por IA"
            description="Importe produtos/procedimentos com IA."
            onClick={() => navigate('/catalogo')}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <RoutineCard
            icon={<Extension fontSize="large" />}
            title="Módulos de Especialidade"
            description="Escalas e módulos por especialidade."
            onClick={() => navigate('/modulos')}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <RoutineCard
            icon={<Settings fontSize="large" />}
            title="Configurar IA SDR"
            description="Agente comercial / SDR."
            onClick={() => navigate('/configuracao-ia')}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <RoutineCard
            icon={<VerifiedUser fontSize="large" />}
            title="Certificação Digital"
            description="Assinatura digital de prescrições, laudos e relatórios (Bird ID e outros)."
            onClick={() => navigate('/certificacao-digital')}
          />
        </Grid>
      </RoutineGroup>

      {ehAdmin && !ehAssistencial && (
        <RoutineGroup title="ADMINISTRAÇÃO">
          <Grid item xs={12} sm={6} md={4}>
            <RoutineCard
              icon={<AdminPanelSettings fontSize="large" />}
              title="Admin Geral"
              description="Usuários, permissões e assinaturas."
              onClick={() => navigate('/admin')}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <RoutineCard
              icon={<Security fontSize="large" />}
              title="Config IA"
              description="Provedores e modelos de IA."
              onClick={() => navigate('/ai-config')}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <RoutineCard
              icon={<SmartToy fontSize="large" />}
              title="Dashboard IA"
              description="Métricas dos agentes de IA."
              onClick={() => navigate('/ai-dashboard')}
            />
          </Grid>
        </RoutineGroup>
      )}
    </Box>
  );
}

export default GestaoPage;
