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

// Provedor do Tema
export const ThemeContextProvider = ({ children }) => {
    // Ler modo inicial do localStorage ou padrão 'light'
    const [mode, setMode] = useState(() => {
        const savedMode = localStorage.getItem('colorMode');
        return savedMode ? savedMode : 'light';
    });

    // Função para alternar entre claro e escuro
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

    // Sincronizar classe no documentElement para CSS externo
    useEffect(() => {
        document.documentElement.classList.remove('light', 'dark');
        document.documentElement.classList.add(mode);
        // Também aplicar ao body por segurança
        document.body.classList.remove('light', 'dark');
        document.body.classList.add(mode);
    }, [mode]);

    // Definição dos temas
    const theme = useMemo(
        () =>
            createTheme({
                palette: {
                    mode,
                    ...(mode === 'light'
                        ? {
                            // Tema Claro (Premium & Textured)
                            primary: {
                                main: '#2e7d32', // Verde
                            },
                            secondary: {
                                main: '#f9a825', // Amarelo
                            },
                            background: {
                                default: '#fcfaf5', // Partitura/Papel levemente envelhecido
                                paper: '#ffffff',
                            },
                            text: {
                                primary: 'rgba(0, 0, 0, 0.87)',
                                secondary: 'rgba(0, 0, 0, 0.6)',
                            },
                        }
                        : {
                            // Tema Escuro (Premium)
                            primary: {
                                main: '#81c784', // Verde Claro
                            },
                            secondary: {
                                main: '#ffb74d', // Laranja Claro
                            },
                            background: {
                                default: '#121212',
                                paper: '#1e1e1e',
                            },
                            text: {
                                primary: '#ffffff',
                                secondary: 'rgba(255, 255, 255, 0.7)',
                            },
                        }),
                },
                components: {
                    MuiCssBaseline: {
                        styleOverrides: {
                            body: {
                                backgroundImage: mode === 'light'
                                    ? `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%232e7d32' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
                                    : 'none',
                                backgroundAttachment: 'fixed',
                            },
                        },
                    },
                    MuiAppBar: {
                        styleOverrides: {
                            root: {
                                backgroundColor: mode === 'dark' ? '#1e1e1e' : '#2e7d32', // Escuro ou Verde tradicional
                            },
                        },
                    },
                    MuiDrawer: {
                        styleOverrides: {
                            paper: {
                                backgroundColor: mode === 'dark' ? '#1e1e1e' : '#ffffff',
                            },
                        },
                    },
                },
            }),
        [mode]
    );

    return (
        <ColorModeContext.Provider value={colorMode}>
            <MuiThemeProvider theme={theme}>
                <CssBaseline />
                {children}
            </MuiThemeProvider>
        </ColorModeContext.Provider>
    );
};
