import React, { useState, useEffect } from 'react';
import {
    Box,
    Typography,
    Paper,
    Grid,
    TextField,
    FormControlLabel,
    Switch,
    Button,
    Divider,
    Alert,
    CircularProgress
} from '@mui/material';
import { Save as SaveIcon, UploadFile as UploadFileIcon } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { prescricaoConfigService } from '../services/api';

const ConfiguracaoPrescricaoPage = () => {
    const { currentUser } = useAuth();
    const [config, setConfig] = useState({
        modo_consultor_ia: false,
        usar_assinatura_digital: false,
        cabecalho_personalizado: '',
        rodape_personalizado: ''
    });
    const [logoClinica, setLogoClinica] = useState(null);
    const [logoProfissional, setLogoProfissional] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [successMessage, setSuccessMessage] = useState('');
    const [errorMessage, setErrorMessage] = useState('');

    useEffect(() => {
        carregarConfiguracoes();
    }, []);

    const carregarConfiguracoes = async () => {
        try {
            setLoading(true);
            const data = await prescricaoConfigService.obter();
            if (data && data.config) {
                setConfig({
                    modo_consultor_ia: data.config.modo_consultor_ia || false,
                    usar_assinatura_digital: data.config.usar_assinatura_digital || false,
                    cabecalho_personalizado: data.config.cabecalho_personalizado || '',
                    rodape_personalizado: data.config.rodape_personalizado || ''
                });
            }
        } catch (error) {
            if(process.env.NODE_ENV!=='production')console.error('Erro ao carregar configurações de prescrição', error);
            setErrorMessage('Não foi possível carregar as configurações atuais.');
        } finally {
            setLoading(false);
        }
    };

    const handleToggleChange = (field) => (event) => {
        setConfig({ ...config, [field]: event.target.checked });
    };

    const handleTextChange = (field) => (event) => {
        setConfig({ ...config, [field]: event.target.value });
    };

    const handleFileChange = (field) => (event) => {
        if (event.target.files && event.target.files[0]) {
            if (field === 'logo_clinica') setLogoClinica(event.target.files[0]);
            if (field === 'logo_profissional') setLogoProfissional(event.target.files[0]);
        }
    };

    const handleSalvar = async () => {
        try {
            setSaving(true);
            setErrorMessage('');
            setSuccessMessage('');

            const formData = new FormData();
            formData.append('modo_consultor_ia', config.modo_consultor_ia);
            formData.append('usar_assinatura_digital', config.usar_assinatura_digital);
            formData.append('cabecalho_personalizado', config.cabecalho_personalizado);
            formData.append('rodape_personalizado', config.rodape_personalizado);

            if (logoClinica) formData.append('logo_clinica', logoClinica);
            if (logoProfissional) formData.append('logo_profissional', logoProfissional);

            await prescricaoConfigService.salvar(formData);
            setSuccessMessage('Configurações salvas com sucesso!');
        } catch (error) {
            if(process.env.NODE_ENV!=='production')console.error('Erro ao salvar configurações', error);
            setErrorMessage(error.error || 'Erro ao salvar. Verifique sua conexão e tente novamente.');
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3, maxWidth: 900, margin: '0 auto' }}>
            <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
                Configurações de Prescrição
            </Typography>

            {successMessage && <Alert severity="success" sx={{ mb: 3 }}>{successMessage}</Alert>}
            {errorMessage && <Alert severity="error" sx={{ mb: 3 }}>{errorMessage}</Alert>}

            <Paper sx={{ p: 4, mb: 4, borderRadius: 2 }}>
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>Logomarcas e Identidade Visual</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    A logomarca da clínica terá maior destaque (60%) e a do profissional terá tamanho secundário (40%).
                    Você pode cadastrar ambas ou apenas uma delas.
                </Typography>

                <Grid container spacing={4}>
                    <Grid item xs={12} md={6}>
                        <Box sx={{ border: '1px dashed grey', p: 3, borderRadius: 2, textAlign: 'center' }}>
                            <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>Selo / Logo da Clínica</Typography>
                            <Button variant="outlined" component="label" startIcon={<UploadFileIcon />}>
                                Escolher Arquivo
                                <input type="file" hidden accept="image/png, image/jpeg" onChange={handleFileChange('logo_clinica')} />
                            </Button>
                            {logoClinica && <Typography variant="caption" display="block" sx={{ mt: 1 }}>{logoClinica.name}</Typography>}
                        </Box>
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <Box sx={{ border: '1px dashed grey', p: 3, borderRadius: 2, textAlign: 'center' }}>
                            <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>Selo / Logo do Profissional</Typography>
                            <Button variant="outlined" component="label" startIcon={<UploadFileIcon />}>
                                Escolher Arquivo
                                <input type="file" hidden accept="image/png, image/jpeg" onChange={handleFileChange('logo_profissional')} />
                            </Button>
                            {logoProfissional && <Typography variant="caption" display="block" sx={{ mt: 1 }}>{logoProfissional.name}</Typography>}
                        </Box>
                    </Grid>
                </Grid>
            </Paper>

            <Paper sx={{ p: 4, mb: 4, borderRadius: 2 }}>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 'bold' }}>Automação e IA</Typography>

                <Box sx={{ mb: 3 }}>
                    <FormControlLabel
                        control={<Switch checked={config.modo_consultor_ia} onChange={handleToggleChange('modo_consultor_ia')} color="primary" />}
                        label={<Typography fontWeight="bold">Consultor IA de Dosagem Ativado</Typography>}
                    />
                    <Typography variant="body2" color="text.secondary" sx={{ ml: 4, mt: 0.5 }}>
                        A Inteligência Artificial atua como um assistente sugerindo esquemas posológicos baseados em sintomas. Se desativado, o sistema apenas ajuda na formatação livre.
                    </Typography>
                </Box>

                <Box>
                    <FormControlLabel
                        control={<Switch checked={config.usar_assinatura_digital} onChange={handleToggleChange('usar_assinatura_digital')} color="primary" />}
                        label={<Typography fontWeight="bold">Assinatura Eletrônica Third-party</Typography>}
                    />
                    <Typography variant="body2" color="text.secondary" sx={{ ml: 4, mt: 0.5 }}>
                        Deixe no modo padrão (Off) para assinar receitas utilizando seu e-CPF ICP-Brasil via Gov.br ou certificado próprio direto no PDF final. Ative apenas caso a clínica for usar integradora validável.
                    </Typography>
                </Box>
            </Paper>

            <Paper sx={{ p: 4, mb: 4, borderRadius: 2 }}>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 'bold' }}>Textos Fixos</Typography>
                <Grid container spacing={3}>
                    <Grid item xs={12}>
                        <TextField
                            fullWidth
                            label="Cabeçalho Personalizado (Opcional)"
                            multiline
                            rows={2}
                            value={config.cabecalho_personalizado}
                            onChange={handleTextChange('cabecalho_personalizado')}
                            placeholder="Ex: Clínica Holística São Paulo - Atendimento Integrado"
                        />
                    </Grid>
                    <Grid item xs={12}>
                        <TextField
                            fullWidth
                            label="Rodapé Personalizado (Opcional)"
                            multiline
                            rows={2}
                            value={config.rodape_personalizado}
                            onChange={handleTextChange('rodape_personalizado')}
                            placeholder="Ex: Endereço completo, Telefone, e-mail de contato..."
                        />
                    </Grid>
                </Grid>
            </Paper>

            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 5 }}>
                <Button
                    variant="contained"
                    color="primary"
                    size="large"
                    startIcon={saving ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />}
                    onClick={handleSalvar}
                    disabled={saving}
                    sx={{ px: 4, py: 1.5 }}
                >
                    {saving ? 'Salvando...' : 'Salvar Configurações'}
                </Button>
            </Box>
        </Box>
    );
};

export default ConfiguracaoPrescricaoPage;
