import React from 'react';
import {
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Typography,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    TextField,
    Button,
    CircularProgress,
    FormControlLabel,
    Switch,
    Box
} from '@mui/material';
import { ExpandMore as ExpandMoreIcon } from '@mui/icons-material';

/**
 * Componente reutilizável para configuração de LLM por função
 */
export default function FunctionLLMConfig({
    title,
    icon,
    provider,
    model,
    apiKey,
    baseUrl,
    useCustomModel,
    providers,
    onProviderChange,
    onModelChange,
    onApiKeyChange,
    onBaseUrlChange,
    onCustomModelToggle,
    onSave,
    saving
}) {
    return (
        <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box display="flex" alignItems="center" gap={1}>
                    {icon}
                    <Typography>{title}</Typography>
                </Box>
            </AccordionSummary>
            <AccordionDetails>
                <Box sx={{ width: '100%' }}>
                    <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                        <InputLabel>Provedor</InputLabel>
                        <Select
                            value={provider}
                            onChange={(e) => onProviderChange(e.target.value)}
                            label="Provedor"
                        >
                            {Object.entries(providers).map(([key, prov]) => (
                                <MenuItem key={key} value={key}>{prov.name}</MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    {provider && (
                        <>
                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={useCustomModel}
                                        onChange={(e) => onCustomModelToggle(e.target.checked)}
                                    />
                                }
                                label="Usar modelo customizado"
                                sx={{ mb: 1 }}
                            />

                            {useCustomModel ? (
                                <TextField
                                    fullWidth
                                    size="small"
                                    label="Modelo Customizado"
                                    value={model}
                                    onChange={(e) => onModelChange(e.target.value)}
                                    placeholder="Digite o nome do modelo"
                                    sx={{ mb: 2 }}
                                />
                            ) : (
                                <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                                    <InputLabel>Modelo</InputLabel>
                                    <Select
                                        value={model}
                                        onChange={(e) => onModelChange(e.target.value)}
                                        label="Modelo"
                                    >
                                        {providers[provider]?.models?.map(m => (
                                            <MenuItem key={m} value={m}>{m}</MenuItem>
                                        ))}
                                    </Select>
                                </FormControl>
                            )}

                            <TextField
                                fullWidth
                                size="small"
                                label="API Key (opcional)"
                                type="password"
                                value={apiKey}
                                onChange={(e) => onApiKeyChange(e.target.value)}
                                placeholder="Deixe em branco para usar a chave salva"
                                sx={{ mb: 2 }}
                            />

                            <TextField
                                fullWidth
                                size="small"
                                label="Base URL (opcional)"
                                value={baseUrl}
                                onChange={(e) => onBaseUrlChange(e.target.value)}
                                placeholder="URL personalizada"
                                sx={{ mb: 2 }}
                            />

                            <Button
                                variant="contained"
                                onClick={onSave}
                                disabled={saving || !provider}
                                fullWidth
                            >
                                {saving ? <CircularProgress size={20} /> : 'Salvar Configuração'}
                            </Button>
                        </>
                    )}
                </Box>
            </AccordionDetails>
        </Accordion>
    );
}
