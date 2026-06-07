import React from 'react';
import { Card, useTheme } from '@mui/material';

/**
 * GlassCard — Card com glassmorphism e hover elevation
 * Props: children, sx, delay (animation delay in seconds)
 */
const GlassCard = ({ children, sx = {}, delay = 0, ...props }) => {
    const theme = useTheme();
    const isLight = theme.palette.mode === 'light';

    return (
        <Card
            {...props}
            sx={{
                background: isLight
                    ? 'rgba(255, 255, 255, 0.72)'
                    : 'rgba(26, 31, 29, 0.72)',
                backdropFilter: 'blur(12px)',
                WebkitBackdropFilter: 'blur(12px)',
                borderRadius: '20px',
                border: `1px solid ${isLight ? 'rgba(13,115,119,0.08)' : 'rgba(0,212,170,0.08)'}`,
                boxShadow: isLight
                    ? '0 8px 32px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.04)'
                    : '0 8px 32px rgba(0,0,0,0.20), 0 2px 8px rgba(0,0,0,0.15)',
                transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                animation: `fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) ${delay}s both`,
                '@keyframes fadeInUp': {
                    from: { opacity: 0, transform: 'translateY(20px)' },
                    to: { opacity: 1, transform: 'translateY(0)' },
                },
                '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: isLight
                        ? '0 20px 40px rgba(0,0,0,0.10), 0 8px 16px rgba(0,0,0,0.06)'
                        : '0 20px 40px rgba(0,0,0,0.30), 0 8px 16px rgba(0,0,0,0.20)',
                },
                ...sx,
            }}
        >
            {children}
        </Card>
    );
};

export default GlassCard;
