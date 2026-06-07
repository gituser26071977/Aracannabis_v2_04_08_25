import React, { createContext, useState, useMemo, useContext, useEffect } from 'react';
import { createTheme, ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Contexto para controlar o modo de cor
const ColorModeContext = createContext({
    mode: 'light',
    toggleColorMode: () => { },
});

// Hook personalizado para usar o contexto
export const useColorMode = () => useContext(ColorModeContext);

// ============================================
// PALETA "EMERALD CANNABIS" — DESIGN SYSTEM
// ============================================

const paletteLight = {
    primary: {
        main: '#0d7377',
        light: '#14a085',
        dark: '#085e61',
        contrastText: '#ffffff',
    },
    secondary: {
        main: '#f5a623',
        light: '#f8d56b',
        dark: '#d4891a',
        contrastText: '#1a1a1a',
    },
    background: {
        default: '#f0f4f1',
        paper: 'rgba(255, 255, 255, 0.72)',
    },
    text: {
        primary: '#1a1f1d',
        secondary: 'rgba(26, 31, 29, 0.65)',
        disabled: 'rgba(26, 31, 29, 0.38)',
    },
    error: {
        main: '#e94560',
        light: '#ff6b6b',
        dark: '#c5304c',
    },
    warning: {
        main: '#f5a623',
        light: '#f8d56b',
        dark: '#d4891a',
    },
    info: {
        main: '#0d7377',
        light: '#14a085',
        dark: '#085e61',
    },
    success: {
        main: '#2ecc71',
        light: '#58d68d',
        dark: '#27ae60',
    },
    divider: 'rgba(13, 115, 119, 0.12)',
};

const paletteDark = {
    primary: {
        main: '#00d4aa',
        light: '#33ddbf',
        dark: '#00a885',
        contrastText: '#0a0f0d',
    },
    secondary: {
        main: '#ffd166',
        light: '#ffe08a',
        dark: '#e6b84d',
        contrastText: '#0a0f0d',
    },
    background: {
        default: '#0a0f0d',
        paper: 'rgba(26, 31, 29, 0.80)',
    },
    text: {
        primary: '#f0f4f1',
        secondary: 'rgba(240, 244, 241, 0.65)',
        disabled: 'rgba(240, 244, 241, 0.38)',
    },
    error: {
        main: '#ff6b6b',
        light: '#ff8e8e',
        dark: '#e94560',
    },
    warning: {
        main: '#ffd166',
        light: '#ffe08a',
        dark: '#e6b84d',
    },
    info: {
        main: '#00d4aa',
        light: '#33ddbf',
        dark: '#00a885',
    },
    success: {
        main: '#27ae60',
        light: '#2ecc71',
        dark: '#1e8c4e',
    },
    divider: 'rgba(0, 212, 170, 0.12)',
};

// ============================================
// SISTEMA DE SOMBRAS EM CAMADAS
// ============================================

const shadowsLight = [
    'none',
    '0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06)',
    '0 4px 6px rgba(0,0,0,0.04), 0 2px 4px rgba(0,0,0,0.06)',
    '0 10px 15px rgba(0,0,0,0.05), 0 4px 6px rgba(0,0,0,0.04)',
    '0 20px 25px rgba(0,0,0,0.06), 0 10px 10px rgba(0,0,0,0.04)',
    '0 25px 50px rgba(0,0,0,0.12), 0 10px 20px rgba(0,0,0,0.08)',
    '0 8px 32px rgba(0,0,0,0.08)',
    '0 8px 32px rgba(0,0,0,0.10)',
    '0 8px 32px rgba(0,0,0,0.12)',
    '0 8px 32px rgba(0,0,0,0.14)',
    '0 8px 32px rgba(0,0,0,0.16)',
    '0 8px 32px rgba(0,0,0,0.18)',
    '0 8px 32px rgba(0,0,0,0.20)',
    '0 8px 32px rgba(0,0,0,0.22)',
    '0 8px 32px rgba(0,0,0,0.24)',
    '0 8px 32px rgba(0,0,0,0.26)',
    '0 8px 32px rgba(0,0,0,0.28)',
    '0 8px 32px rgba(0,0,0,0.30)',
    '0 8px 32px rgba(0,0,0,0.32)',
    '0 8px 32px rgba(0,0,0,0.34)',
    '0 8px 32px rgba(0,0,0,0.36)',
    '0 8px 32px rgba(0,0,0,0.38)',
    '0 8px 32px rgba(0,0,0,0.40)',
    '0 8px 32px rgba(0,0,0,0.42)',
    '0 8px 32px rgba(0,0,0,0.44)',
];

const shadowsDark = [
    'none',
    '0 1px 3px rgba(0,0,0,0.20), 0 1px 2px rgba(0,0,0,0.24)',
    '0 4px 6px rgba(0,0,0,0.20), 0 2px 4px rgba(0,0,0,0.24)',
    '0 10px 15px rgba(0,0,0,0.20), 0 4px 6px rgba(0,0,0,0.24)',
    '0 20px 25px rgba(0,0,0,0.24), 0 10px 10px rgba(0,0,0,0.20)',
    '0 25px 50px rgba(0,0,0,0.40), 0 10px 20px rgba(0,0,0,0.32)',
    '0 8px 32px rgba(0,0,0,0.30)',
    '0 8px 32px rgba(0,0,0,0.32)',
    '0 8px 32px rgba(0,0,0,0.34)',
    '0 8px 32px rgba(0,0,0,0.36)',
    '0 8px 32px rgba(0,0,0,0.38)',
    '0 8px 32px rgba(0,0,0,0.40)',
    '0 8px 32px rgba(0,0,0,0.42)',
    '0 8px 32px rgba(0,0,0,0.44)',
    '0 8px 32px rgba(0,0,0,0.46)',
    '0 8px 32px rgba(0,0,0,0.48)',
    '0 8px 32px rgba(0,0,0,0.50)',
    '0 8px 32px rgba(0,0,0,0.52)',
    '0 8px 32px rgba(0,0,0,0.54)',
    '0 8px 32px rgba(0,0,0,0.56)',
    '0 8px 32px rgba(0,0,0,0.58)',
    '0 8px 32px rgba(0,0,0,0.60)',
    '0 8px 32px rgba(0,0,0,0.62)',
    '0 8px 32px rgba(0,0,0,0.64)',
    '0 8px 32px rgba(0,0,0,0.66)',
];

// ============================================
// KEYFRAMES CSS — ANIMAÇÕES GLOBAIS
// ============================================

const globalKeyframes = `
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
@keyframes slideInRight {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}
@keyframes slideInLeft {
    from { opacity: 0; transform: translateX(20px); }
    to { opacity: 1; transform: translateX(0); }
}
@keyframes scaleIn {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
}
@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 5px rgba(13,115,119,0.3); }
    50% { box-shadow: 0 0 20px rgba(13,115,119,0.6); }
}
@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-6px); }
}
@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
@keyframes bounceIn {
    0% { opacity: 0; transform: scale(0.3); }
    50% { opacity: 1; transform: scale(1.05); }
    70% { transform: scale(0.9); }
    100% { transform: scale(1); }
}
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
@keyframes shake {
    0%, 100% { transform: translateX(0); }
    10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
    20%, 40%, 60%, 80% { transform: translateX(4px); }
}
`;

// ============================================
// ESTILOS GLOBAIS CSS
// ============================================

const globalStylesLight = {
    body: {
        background: 'radial-gradient(ellipse at 20% 0%, #e8f5e9 0%, #f0f4f1 40%, #e0e7e4 100%)',
        backgroundAttachment: 'fixed',
        minHeight: '100vh',
        '&::before': {
            content: '""',
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
            opacity: 0.025,
            pointerEvents: 'none',
            zIndex: 0,
        },
    },
    '*': {
        scrollbarWidth: 'thin',
        scrollbarColor: 'rgba(13,115,119,0.3) transparent',
    },
    '*::-webkit-scrollbar': {
        width: '6px',
    },
    '*::-webkit-scrollbar-track': {
        background: 'transparent',
    },
    '*::-webkit-scrollbar-thumb': {
        backgroundColor: 'rgba(13,115,119,0.3)',
        borderRadius: '10px',
    },
};

const globalStylesDark = {
    body: {
        background: 'radial-gradient(ellipse at 20% 0%, #0d1f1a 0%, #0a0f0d 40%, #050a08 100%)',
        backgroundAttachment: 'fixed',
        minHeight: '100vh',
        '&::before': {
            content: '""',
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
            opacity: 0.04,
            pointerEvents: 'none',
            zIndex: 0,
        },
    },
    '*': {
        scrollbarWidth: 'thin',
        scrollbarColor: 'rgba(0,212,170,0.3) transparent',
    },
    '*::-webkit-scrollbar': {
        width: '6px',
    },
    '*::-webkit-scrollbar-track': {
        background: 'transparent',
    },
    '*::-webkit-scrollbar-thumb': {
        backgroundColor: 'rgba(0,212,170,0.3)',
        borderRadius: '10px',
    },
};

// ============================================
// THEME CREATOR
// ============================================

const createAppTheme = (mode) => {
    const isLight = mode === 'light';
    const palette = isLight ? paletteLight : paletteDark;
    const shadows = isLight ? shadowsLight : shadowsDark;

    return createTheme({
        palette: {
            mode,
            ...palette,
        },
        shape: {
            borderRadius: 12,
        },
        shadows,
        typography: {
            fontFamily: '"Roboto", "Segoe UI", "Helvetica Neue", sans-serif',
            h1: {
                fontWeight: 700,
                letterSpacing: '-0.02em',
                lineHeight: 1.2,
            },
            h2: {
                fontWeight: 700,
                letterSpacing: '-0.02em',
                lineHeight: 1.25,
            },
            h3: {
                fontWeight: 700,
                letterSpacing: '-0.015em',
                lineHeight: 1.3,
            },
            h4: {
                fontWeight: 600,
                letterSpacing: '-0.01em',
                lineHeight: 1.35,
            },
            h5: {
                fontWeight: 600,
                letterSpacing: '-0.005em',
                lineHeight: 1.4,
            },
            h6: {
                fontWeight: 600,
                letterSpacing: '0',
                lineHeight: 1.45,
            },
            subtitle1: {
                fontWeight: 500,
                letterSpacing: '-0.01em',
                lineHeight: 1.5,
            },
            subtitle2: {
                fontWeight: 500,
                letterSpacing: '0.01em',
                lineHeight: 1.5,
                textTransform: 'uppercase',
                fontSize: '0.75rem',
            },
            body1: {
                fontWeight: 400,
                lineHeight: 1.6,
                letterSpacing: '0',
            },
            body2: {
                fontWeight: 400,
                lineHeight: 1.6,
                letterSpacing: '0',
                fontSize: '0.875rem',
            },
            button: {
                fontWeight: 600,
                letterSpacing: '0.02em',
                textTransform: 'none',
            },
            caption: {
                fontWeight: 500,
                letterSpacing: '0.02em',
                fontSize: '0.75rem',
            },
            overline: {
                fontWeight: 600,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                fontSize: '0.7rem',
            },
        },
        components: {
            MuiCssBaseline: {
                styleOverrides: {
                    ...(isLight ? globalStylesLight : globalStylesDark),
                    '@global': globalKeyframes,
                },
            },
            MuiAppBar: {
                styleOverrides: {
                    root: {
                        background: isLight
                            ? 'rgba(255, 255, 255, 0.72)'
                            : 'rgba(10, 15, 13, 0.72)',
                        backdropFilter: 'blur(20px) saturate(180%)',
                        WebkitBackdropFilter: 'blur(20px) saturate(180%)',
                        borderBottom: `1px solid ${isLight ? 'rgba(13,115,119,0.08)' : 'rgba(0,212,170,0.08)'}`,
                        boxShadow: 'none',
                        color: isLight ? '#1a1f1d' : '#f0f4f1',
                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    },
                },
            },
            MuiDrawer: {
                styleOverrides: {
                    paper: {
                        background: isLight
                            ? 'rgba(255, 255, 255, 0.85)'
                            : 'rgba(26, 31, 29, 0.90)',
                        backdropFilter: 'blur(24px) saturate(180%)',
                        WebkitBackdropFilter: 'blur(24px) saturate(180%)',
                        borderRight: `1px solid ${isLight ? 'rgba(13,115,119,0.08)' : 'rgba(0,212,170,0.08)'}`,
                        boxShadow: isLight
                            ? '8px 0 32px rgba(0,0,0,0.08)'
                            : '8px 0 32px rgba(0,0,0,0.30)',
                        borderRadius: '0 20px 20px 0',
                        overflow: 'hidden',
                    },
                },
            },
            MuiCard: {
                styleOverrides: {
                    root: {
                        background: isLight
                            ? 'rgba(255, 255, 255, 0.72)'
                            : 'rgba(26, 31, 29, 0.72)',
                        backdropFilter: 'blur(12px)',
                        WebkitBackdropFilter: 'blur(12px)',
                        borderRadius: '16px',
                        border: `1px solid ${isLight ? 'rgba(13,115,119,0.08)' : 'rgba(0,212,170,0.08)'}`,
                        boxShadow: isLight
                            ? '0 8px 32px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.04)'
                            : '0 8px 32px rgba(0,0,0,0.20), 0 2px 8px rgba(0,0,0,0.15)',
                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                        '&:hover': {
                            transform: 'translateY(-4px)',
                            boxShadow: isLight
                                ? '0 20px 40px rgba(0,0,0,0.10), 0 8px 16px rgba(0,0,0,0.06)'
                                : '0 20px 40px rgba(0,0,0,0.30), 0 8px 16px rgba(0,0,0,0.20)',
                        },
                    },
                },
            },
            MuiPaper: {
                styleOverrides: {
                    root: {
                        backgroundImage: 'none',
                        background: isLight
                            ? 'rgba(255, 255, 255, 0.72)'
                            : 'rgba(26, 31, 29, 0.72)',
                        backdropFilter: 'blur(12px)',
                        WebkitBackdropFilter: 'blur(12px)',
                        borderRadius: '16px',
                        border: `1px solid ${isLight ? 'rgba(13,115,119,0.08)' : 'rgba(0,212,170,0.08)'}`,
                    },
                },
            },
            MuiButton: {
                styleOverrides: {
                    root: {
                        borderRadius: '12px',
                        textTransform: 'none',
                        fontWeight: 600,
                        letterSpacing: '0.02em',
                        padding: '10px 24px',
                        transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                        '&:hover': {
                            transform: 'scale(1.02)',
                            boxShadow: isLight
                                ? '0 4px 16px rgba(13,115,119,0.25)'
                                : '0 4px 16px rgba(0,212,170,0.25)',
                        },
                        '&:active': {
                            transform: 'scale(0.98)',
                        },
                    },
                    containedPrimary: {
                        background: isLight
                            ? 'linear-gradient(135deg, #0d7377 0%, #14a085 100%)'
                            : 'linear-gradient(135deg, #00d4aa 0%, #33ddbf 100%)',
                        boxShadow: isLight
                            ? '0 4px 16px rgba(13,115,119,0.30)'
                            : '0 4px 16px rgba(0,212,170,0.30)',
                        '&:hover': {
                            boxShadow: isLight
                                ? '0 8px 24px rgba(13,115,119,0.40)'
                                : '0 8px 24px rgba(0,212,170,0.40)',
                        },
                    },
                    containedSecondary: {
                        background: isLight
                            ? 'linear-gradient(135deg, #f5a623 0%, #f8d56b 100%)'
                            : 'linear-gradient(135deg, #ffd166 0%, #ffe08a 100%)',
                        boxShadow: isLight
                            ? '0 4px 16px rgba(245,166,35,0.30)'
                            : '0 4px 16px rgba(255,209,102,0.30)',
                    },
                    outlined: {
                        borderWidth: '1.5px',
                        '&:hover': {
                            borderWidth: '1.5px',
                        },
                    },
                },
            },
            MuiTextField: {
                styleOverrides: {
                    root: {
                        '& .MuiOutlinedInput-root': {
                            borderRadius: '12px',
                            background: isLight
                                ? 'rgba(255,255,255,0.5)'
                                : 'rgba(26,31,29,0.5)',
                            backdropFilter: 'blur(8px)',
                            transition: 'all 0.2s ease',
                            '& fieldset': {
                                borderColor: isLight
                                    ? 'rgba(13,115,119,0.15)'
                                    : 'rgba(0,212,170,0.15)',
                                borderWidth: '1.5px',
                            },
                            '&:hover fieldset': {
                                borderColor: isLight
                                    ? 'rgba(13,115,119,0.35)'
                                    : 'rgba(0,212,170,0.35)',
                            },
                            '&.Mui-focused fieldset': {
                                borderColor: isLight ? '#0d7377' : '#00d4aa',
                                borderWidth: '2px',
                                boxShadow: isLight
                                    ? '0 0 0 3px rgba(13,115,119,0.15)'
                                    : '0 0 0 3px rgba(0,212,170,0.15)',
                            },
                        },
                    },
                },
            },
            MuiOutlinedInput: {
                styleOverrides: {
                    root: {
                        borderRadius: '12px',
                    },
                },
            },
            MuiListItem: {
                styleOverrides: {
                    root: {
                        borderRadius: '12px',
                        margin: '4px 12px',
                        padding: '10px 16px',
                        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                        '&:hover': {
                            background: isLight
                                ? 'rgba(13,115,119,0.06)'
                                : 'rgba(0,212,170,0.06)',
                            transform: 'translateX(4px)',
                            '& .MuiListItemIcon-root': {
                                transform: 'scale(1.1)',
                                color: isLight ? '#0d7377' : '#00d4aa',
                            },
                        },
                        '&.Mui-selected': {
                            background: isLight
                                ? 'linear-gradient(90deg, rgba(13,115,119,0.12) 0%, rgba(20,160,133,0.08) 100%)'
                                : 'linear-gradient(90deg, rgba(0,212,170,0.15) 0%, rgba(51,221,191,0.10) 100%)',
                            borderLeft: `3px solid ${isLight ? '#0d7377' : '#00d4aa'}`,
                            '& .MuiListItemIcon-root': {
                                color: isLight ? '#0d7377' : '#00d4aa',
                            },
                            '& .MuiListItemText-primary': {
                                fontWeight: 600,
                                color: isLight ? '#0d7377' : '#00d4aa',
                            },
                        },
                    },
                },
            },
            MuiListItemIcon: {
                styleOverrides: {
                    root: {
                        transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                        minWidth: '40px',
                    },
                },
            },
            MuiDivider: {
                styleOverrides: {
                    root: {
                        background: isLight
                            ? 'linear-gradient(90deg, transparent 0%, rgba(13,115,119,0.15) 50%, transparent 100%)'
                            : 'linear-gradient(90deg, transparent 0%, rgba(0,212,170,0.15) 50%, transparent 100%)',
                        border: 'none',
                        height: '1px',
                        margin: '12px 0',
                    },
                },
            },
            MuiChip: {
                styleOverrides: {
                    root: {
                        borderRadius: '20px',
                        fontWeight: 600,
                        fontSize: '0.8rem',
                        padding: '4px 8px',
                        background: isLight
                            ? 'rgba(13,115,119,0.08)'
                            : 'rgba(0,212,170,0.08)',
                        border: `1px solid ${isLight ? 'rgba(13,115,119,0.12)' : 'rgba(0,212,170,0.12)'}`,
                        transition: 'all 0.2s ease',
                        '&:hover': {
                            transform: 'scale(1.05)',
                            boxShadow: isLight
                                ? '0 2px 8px rgba(13,115,119,0.15)'
                                : '0 2px 8px rgba(0,212,170,0.15)',
                        },
                    },
                },
            },
            MuiAvatar: {
                styleOverrides: {
                    root: {
                        border: `2px solid ${isLight ? 'rgba(13,115,119,0.2)' : 'rgba(0,212,170,0.2)'}`,
                        boxShadow: isLight
                            ? '0 2px 8px rgba(13,115,119,0.15)'
                            : '0 2px 8px rgba(0,212,170,0.15)',
                    },
                },
            },
            MuiAlert: {
                styleOverrides: {
                    root: {
                        borderRadius: '16px',
                        background: isLight
                            ? 'rgba(255,255,255,0.72)'
                            : 'rgba(26,31,29,0.72)',
                        backdropFilter: 'blur(12px)',
                        border: '1px solid',
                        borderLeftWidth: '4px',
                        boxShadow: isLight
                            ? '0 4px 16px rgba(0,0,0,0.06)'
                            : '0 4px 16px rgba(0,0,0,0.15)',
                    },
                    standardError: {
                        borderLeftColor: '#e94560',
                    },
                    standardWarning: {
                        borderLeftColor: '#f5a623',
                    },
                    standardInfo: {
                        borderLeftColor: '#0d7377',
                    },
                    standardSuccess: {
                        borderLeftColor: '#2ecc71',
                    },
                },
            },
            MuiDialog: {
                styleOverrides: {
                    paper: {
                        borderRadius: '20px',
                        background: isLight
                            ? 'rgba(255,255,255,0.90)'
                            : 'rgba(26,31,29,0.90)',
                        backdropFilter: 'blur(24px)',
                        boxShadow: isLight
                            ? '0 25px 50px rgba(0,0,0,0.15)'
                            : '0 25px 50px rgba(0,0,0,0.40)',
                    },
                },
            },
            MuiTableContainer: {
                styleOverrides: {
                    root: {
                        borderRadius: '16px',
                        background: isLight
                            ? 'rgba(255,255,255,0.72)'
                            : 'rgba(26,31,29,0.72)',
                        backdropFilter: 'blur(12px)',
                        border: `1px solid ${isLight ? 'rgba(13,115,119,0.08)' : 'rgba(0,212,170,0.08)'}`,
                        boxShadow: isLight
                            ? '0 8px 32px rgba(0,0,0,0.06)'
                            : '0 8px 32px rgba(0,0,0,0.20)',
                    },
                },
            },
            MuiTab: {
                styleOverrides: {
                    root: {
                        textTransform: 'none',
                        fontWeight: 600,
                        fontSize: '0.9rem',
                        borderRadius: '12px',
                        transition: 'all 0.2s ease',
                        '&:hover': {
                            background: isLight
                                ? 'rgba(13,115,119,0.06)'
                                : 'rgba(0,212,170,0.06)',
                        },
                    },
                },
            },
            MuiTooltip: {
                styleOverrides: {
                    tooltip: {
                        background: isLight
                            ? 'rgba(26,31,29,0.90)'
                            : 'rgba(255,255,255,0.90)',
                        backdropFilter: 'blur(12px)',
                        borderRadius: '10px',
                        padding: '8px 14px',
                        fontSize: '0.8rem',
                        fontWeight: 500,
                        boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
                    },
                },
            },
            MuiSnackbar: {
                styleOverrides: {
                    root: {
                        '& .MuiPaper-root': {
                            borderRadius: '16px',
                            background: isLight
                                ? 'rgba(255,255,255,0.90)'
                                : 'rgba(26,31,29,0.90)',
                            backdropFilter: 'blur(16px)',
                            boxShadow: isLight
                                ? '0 8px 32px rgba(0,0,0,0.12)'
                                : '0 8px 32px rgba(0,0,0,0.30)',
                        },
                    },
                },
            },
            MuiFab: {
                styleOverrides: {
                    root: {
                        background: isLight
                            ? 'linear-gradient(135deg, #0d7377 0%, #14a085 100%)'
                            : 'linear-gradient(135deg, #00d4aa 0%, #33ddbf 100%)',
                        boxShadow: isLight
                            ? '0 4px 16px rgba(13,115,119,0.35)'
                            : '0 4px 16px rgba(0,212,170,0.35)',
                        '&:hover': {
                            transform: 'scale(1.08)',
                            boxShadow: isLight
                                ? '0 8px 24px rgba(13,115,119,0.45)'
                                : '0 8px 24px rgba(0,212,170,0.45)',
                        },
                    },
                },
            },
            MuiIconButton: {
                styleOverrides: {
                    root: {
                        transition: 'all 0.2s ease',
                        '&:hover': {
                            transform: 'scale(1.1)',
                            background: isLight
                                ? 'rgba(13,115,119,0.08)'
                                : 'rgba(0,212,170,0.08)',
                        },
                    },
                },
            },
            MuiBadge: {
                styleOverrides: {
                    badge: {
                        fontWeight: 700,
                        fontSize: '0.7rem',
                        boxShadow: isLight
                            ? '0 2px 6px rgba(0,0,0,0.15)'
                            : '0 2px 6px rgba(0,0,0,0.30)',
                    },
                },
            },
            MuiAccordion: {
                styleOverrides: {
                    root: {
                        borderRadius: '12px !important',
                        background: isLight
                            ? 'rgba(255,255,255,0.60)'
                            : 'rgba(26,31,29,0.60)',
                        backdropFilter: 'blur(8px)',
                        marginBottom: '8px',
                        '&:before': {
                            display: 'none',
                        },
                    },
                },
            },
            MuiStepper: {
                styleOverrides: {
                    root: {
                        background: 'transparent',
                    },
                },
            },
            MuiStepLabel: {
                styleOverrides: {
                    label: {
                        fontWeight: 500,
                        '&.Mui-active': {
                            fontWeight: 700,
                            color: isLight ? '#0d7377' : '#00d4aa',
                        },
                    },
                },
            },
            MuiLinearProgress: {
                styleOverrides: {
                    root: {
                        borderRadius: '10px',
                        background: isLight
                            ? 'rgba(13,115,119,0.12)'
                            : 'rgba(0,212,170,0.12)',
                    },
                    bar: {
                        borderRadius: '10px',
                        background: isLight
                            ? 'linear-gradient(90deg, #0d7377, #14a085)'
                            : 'linear-gradient(90deg, #00d4aa, #33ddbf)',
                    },
                },
            },
            MuiCircularProgress: {
                styleOverrides: {
                    root: {
                        '& .MuiCircularProgress-circle': {
                            strokeLinecap: 'round',
                        },
                    },
                },
            },
            MuiSkeleton: {
                styleOverrides: {
                    root: {
                        borderRadius: '12px',
                        background: isLight
                            ? 'linear-gradient(90deg, rgba(13,115,119,0.06) 25%, rgba(13,115,119,0.12) 50%, rgba(13,115,119,0.06) 75%)'
                            : 'linear-gradient(90deg, rgba(0,212,170,0.06) 25%, rgba(0,212,170,0.12) 50%, rgba(0,212,170,0.06) 75%)',
                        backgroundSize: '200% 100%',
                        animation: 'shimmer 1.5s infinite',
                    },
                },
            },
            MuiMenu: {
                styleOverrides: {
                    paper: {
                        borderRadius: '16px',
                        background: isLight
                            ? 'rgba(255,255,255,0.90)'
                            : 'rgba(26,31,29,0.90)',
                        backdropFilter: 'blur(16px)',
                        boxShadow: isLight
                            ? '0 8px 32px rgba(0,0,0,0.10)'
                            : '0 8px 32px rgba(0,0,0,0.30)',
                    },
                },
            },
            MuiMenuItem: {
                styleOverrides: {
                    root: {
                        borderRadius: '10px',
                        margin: '2px 8px',
                        transition: 'all 0.15s ease',
                        '&:hover': {
                            background: isLight
                                ? 'rgba(13,115,119,0.08)'
                                : 'rgba(0,212,170,0.08)',
                        },
                    },
                },
            },
            MuiPaginationItem: {
                styleOverrides: {
                    root: {
                        borderRadius: '12px',
                        fontWeight: 600,
                        '&.Mui-selected': {
                            background: isLight
                                ? 'linear-gradient(135deg, #0d7377, #14a085)'
                                : 'linear-gradient(135deg, #00d4aa, #33ddbf)',
                            color: isLight ? '#fff' : '#0a0f0d',
                            boxShadow: isLight
                                ? '0 2px 8px rgba(13,115,119,0.30)'
                                : '0 2px 8px rgba(0,212,170,0.30)',
                        },
                    },
                },
            },
        },
    });
};

// ============================================
// PROVIDER
// ============================================

export const ThemeContextProvider = ({ children }) => {
    const [mode, setMode] = useState(() => {
        const savedMode = localStorage.getItem('colorMode');
        return savedMode ? savedMode : 'light';
    });

    const colorMode = useMemo(
        () => ({
            mode,
            toggleColorMode: () => {
                setMode((prevMode) => {
                    const newMode = prevMode === 'light' ? 'dark' : 'light';
                    localStorage.setItem('colorMode', newMode);
                    return newMode;
                });
            },
        }),
        [mode]
    );

    useEffect(() => {
        document.documentElement.classList.remove('light', 'dark');
        document.documentElement.classList.add(mode);
        document.body.classList.remove('light', 'dark');
        document.body.classList.add(mode);
    }, [mode]);

    const theme = useMemo(() => createAppTheme(mode), [mode]);

    return (
        <ColorModeContext.Provider value={colorMode}>
            <MuiThemeProvider theme={theme}>
                <CssBaseline />
                {children}
            </MuiThemeProvider>
        </ColorModeContext.Provider>
    );
};
