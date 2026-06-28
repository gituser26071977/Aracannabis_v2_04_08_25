import React from 'react';
import { Box, Card, CardActionArea, CardContent, Typography, Stack } from '@mui/material';

/**
 * QuickActionsBar — Barra de ações rápidas contextuais
 *
 * Mostra 3-6 ações em grid de cards compactos para tornar as funções
 * mais importantes de uma tela imediatamente descobriveis.
 *
 * Props:
 *  - title:    string (opcional, default null) — "Ações Rápidas" por ex.
 *  - actions:  array de { label, description?, icon, onClick, color?, badge? }
 *  - columns:  number (auto-fit default = 3 em desktop, 1 em mobile)
 *  - compact:  boolean (default false) — cards menores
 *  - sx:       object
 *
 * Uso típico:
 *   <QuickActionsBar
 *     title="Ações Rápidas"
 *     actions={[
 *       { label: 'Nova Consulta', icon: <CalendarIcon />, onClick: () => ... },
 *       { label: 'Nova Prescrição', icon: <EditIcon />, onClick: () => ... },
 *     ]}
 *   />
 */
const QuickActionsBar = ({
    title = 'Ações Rápidas',
    actions = [],
    columns,
    compact = false,
    sx = {},
}) => {
    if (!actions || actions.length === 0) return null;

    const gridCols = columns || { xs: 1, sm: 2, md: Math.min(actions.length, 4) };

    return (
        <Box sx={{ mb: 3, ...sx }}>
            {title && (
                <Typography
                    variant="overline"
                    sx={{
                        color: 'text.secondary',
                        fontWeight: 600,
                        letterSpacing: '0.08em',
                        pl: 0.5,
                    }}
                >
                    {title}
                </Typography>
            )}
            <Box
                sx={{
                    display: 'grid',
                    gridTemplateColumns: gridCols,
                    gap: 2,
                    mt: 1,
                }}
            >
                {actions.map((action, idx) => (
                    <Card
                        key={idx}
                        elevation={0}
                        sx={{
                            borderRadius: 2,
                            border: '1px solid',
                            borderColor: 'divider',
                            transition: 'all 0.2s ease',
                            position: 'relative',
                            '&:hover': {
                                borderColor: action.color || 'primary.main',
                                transform: 'translateY(-2px)',
                                boxShadow: 3,
                            },
                        }}
                    >
                        <CardActionArea
                            onClick={action.onClick}
                            disabled={action.disabled}
                            sx={{
                                p: compact ? 1.5 : 2,
                                minHeight: compact ? 64 : 88,
                            }}
                        >
                            <Stack
                                direction="row"
                                spacing={1.5}
                                alignItems="center"
                            >
                                {action.icon && (
                                    <Box
                                        sx={{
                                            color: action.color || 'primary.main',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            width: 40,
                                            height: 40,
                                            borderRadius: 1.5,
                                            bgcolor: action.disabled
                                                ? 'action.disabledBackground'
                                                : (action.bgcolor || 'action.hover'),
                                            flexShrink: 0,
                                        }}
                                    >
                                        {action.icon}
                                    </Box>
                                )}
                                <CardContent
                                    sx={{
                                        p: 0,
                                        '&:last-child': { pb: 0 },
                                        flex: 1,
                                        minWidth: 0,
                                    }}
                                >
                                    <Typography
                                        variant={compact ? 'body2' : 'subtitle2'}
                                        sx={{
                                            fontWeight: 600,
                                            lineHeight: 1.2,
                                            whiteSpace: 'nowrap',
                                            overflow: 'hidden',
                                            textOverflow: 'ellipsis',
                                        }}
                                    >
                                        {action.label}
                                        {action.badge && (
                                            <Box
                                                component="span"
                                                sx={{
                                                    ml: 1,
                                                    px: 0.75,
                                                    py: 0.25,
                                                    borderRadius: 1,
                                                    bgcolor: 'error.main',
                                                    color: 'error.contrastText',
                                                    fontSize: '0.65rem',
                                                    fontWeight: 700,
                                                    verticalAlign: 'middle',
                                                }}
                                            >
                                                {action.badge}
                                            </Box>
                                        )}
                                    </Typography>
                                    {action.description && !compact && (
                                        <Typography
                                            variant="caption"
                                            sx={{
                                                color: 'text.secondary',
                                                display: 'block',
                                                mt: 0.25,
                                                lineHeight: 1.3,
                                            }}
                                        >
                                            {action.description}
                                        </Typography>
                                    )}
                                </CardContent>
                            </Stack>
                        </CardActionArea>
                    </Card>
                ))}
            </Box>
        </Box>
    );
};

export default QuickActionsBar;
