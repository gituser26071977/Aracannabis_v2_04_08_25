import React from 'react';
import { Chip, useTheme } from '@mui/material';

/**
 * EmojiBadge — Chip com emoji e glassmorphism
 * Props: emoji, label, color (MUI color name), sx
 */
const EmojiBadge = ({ emoji, label, color = 'default', sx = {}, ...props }) => {
    const theme = useTheme();
    const isLight = theme.palette.mode === 'light';
    const colorValue = theme.palette[color]?.main || theme.palette.primary.main;

    return (
        <Chip
            {...props}
            label={
                <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    {emoji && <span>{emoji}</span>}
                    <span>{label}</span>
                </span>
            }
            sx={{
                borderRadius: '20px',
                fontWeight: 600,
                fontSize: '0.8rem',
                height: 32,
                bgcolor: `${colorValue}12`,
                color: colorValue,
                border: `1px solid ${colorValue}20`,
                backdropFilter: 'blur(8px)',
                transition: 'all 0.2s ease',
                '&:hover': {
                    transform: 'scale(1.05)',
                    bgcolor: `${colorValue}18`,
                    boxShadow: `0 2px 8px ${colorValue}20`,
                },
                '& .MuiChip-label': {
                    px: 1.5,
                    display: 'flex',
                    alignItems: 'center',
                },
                ...sx,
            }}
        />
    );
};

export default EmojiBadge;
