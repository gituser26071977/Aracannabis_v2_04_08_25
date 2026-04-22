import React from 'react';
import { Button, useTheme } from '@mui/material';

/**
 * GradientButton — Botão com gradiente primário e glow no hover
 * Props: todas as do MUI Button + glowColor (opcional)
 */
const GradientButton = ({ children, sx = {}, glowColor, ...props }) => {
    const theme = useTheme();
    const isLight = theme.palette.mode === 'light';
    const primary = theme.palette.primary.main;
    const primaryLight = theme.palette.primary.light;

    const defaultGlow = isLight
        ? `0 8px 24px ${primary}40`
        : `0 8px 24px ${primary}50`;

    return (
        <Button
            {...props}
            sx={{
                borderRadius: '14px',
                fontWeight: 700,
                letterSpacing: '0.02em',
                textTransform: 'none',
                padding: '12px 28px',
                background: `linear-gradient(135deg, ${primary} 0%, ${primaryLight} 100%)`,
                boxShadow: glowColor
                    ? `0 4px 16px ${glowColor}40`
                    : `0 4px 16px ${primary}30`,
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                '&:hover': {
                    transform: 'scale(1.02) translateY(-2px)',
                    boxShadow: glowColor
                        ? `0 8px 28px ${glowColor}55`
                        : defaultGlow,
                },
                '&:active': {
                    transform: 'scale(0.98)',
                },
                ...sx,
            }}
        >
            {children}
        </Button>
    );
};

export default GradientButton;
