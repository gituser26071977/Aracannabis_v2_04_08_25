import React, { useState } from 'react';
import { Alert, Box, IconButton, Collapse } from '@mui/material';
import { Close as CloseIcon, Lightbulb as LightbulbIcon } from '@mui/icons-material';

/**
 * ContextualTip — Dica discreta em formato de "tip" (não bloqueante, dispensável)
 *
 * Mostra um alerta amarelo/azul discreto no topo de uma seção para ensinar
 * o usuário sobre uma feature importante que ele poderia não descobrir.
 *
 * Props:
 *  - severity: 'info' | 'warning' | 'success' | 'tip' (default 'tip' = azul claro)
 *  - title:    string (opcional, ex: "💡 Dica:")
 *  - children: string | ReactNode
 *  - dismissible: boolean (default true) — usuário pode fechar
 *  - storageKey: string — se fornecido, lembra que foi dispensado (escopo por usuário)
 *  - icon:    ReactNode (opcional, default LightbulbIcon)
 *  - sx:      object (custom styles)
 *
 * Persistência: usa rememberKey em localStorage para não mostrar a mesma dica
 *   2x para o mesmo usuário.
 */
const ContextualTip = ({
    severity = 'info',
    title,
    children,
    dismissible = true,
    storageKey,
    icon,
    sx = {},
}) => {
    const STORAGE_PREFIX = 'tip_dismissed:';
    const fullKey = storageKey ? STORAGE_PREFIX + storageKey : null;

    const [dismissed, setDismissed] = useState(() => {
        if (!fullKey) return false;
        try {
            return localStorage.getItem(fullKey) === '1';
        } catch {
            return false;
        }
    });

    const handleDismiss = () => {
        setDismissed(true);
        if (fullKey) {
            try { localStorage.setItem(fullKey, '1'); } catch { /* noop */ }
        }
    };

    if (dismissed) return null;

    // Mapeia 'tip' para 'info' com styling diferenciado
    const effectiveSeverity = severity === 'tip' ? 'info' : severity;
    const defaultIcon = severity === 'tip' || severity === 'info'
        ? <LightbulbIcon fontSize="small" sx={{ color: 'warning.main' }} />
        : null;

    return (
        <Collapse in={!dismissed}>
            <Alert
                severity={effectiveSeverity}
                icon={icon || defaultIcon}
                action={
                    dismissible ? (
                        <IconButton
                            aria-label="Fechar dica"
                            color="inherit"
                            size="small"
                            onClick={handleDismiss}
                        >
                            <CloseIcon fontSize="inherit" />
                        </IconButton>
                    ) : null
                }
                sx={{
                    mb: 2,
                    borderRadius: 2,
                    alignItems: 'center',
                    '& .MuiAlert-message': { width: '100%' },
                    ...sx,
                }}
            >
                {title && (
                    <Box component="span" sx={{ fontWeight: 700, mr: 0.5 }}>
                        {title}
                    </Box>
                )}
                {children}
            </Alert>
        </Collapse>
    );
};

export default ContextualTip;
