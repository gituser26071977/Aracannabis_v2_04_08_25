/**
 * PageHeader — cabeçalho padronizado para todas as páginas internas.
 *
 * Resolve:
 *   - 7 variações diferentes de header (algumas com emoji, outras não)
 *   - Mistura de h3, h4, h5, h6 com cores e fontSizes conflitantes
 *   - Falta de hierarquia entre título, subtítulo e ações
 *
 * Uso:
 *   <PageHeader
 *     title="Pacientes"
 *     subtitle="Gerencie seus pacientes e prontuários"
 *     actions={<Button variant="contained">Novo</Button>}
 *   />
 */
import React from 'react';
import { Box, Typography, Stack } from '@mui/material';
import { tokens } from '../theme/tokens';

const PageHeader = ({
  title,
  subtitle,
  actions,
  icon,           // opcional — IconButton ou Avatar à esquerda do título
  breadcrumbs,    // opcional — array de strings
  compact = false,
}) => {
  return (
    <Box
      component="header"
      sx={{
        display: 'flex',
        flexDirection: { xs: 'column', sm: 'row' },
        alignItems: { xs: 'flex-start', sm: 'center' },
        justifyContent: 'space-between',
        gap: 2,
        mb: compact ? 2 : 4,
        pb: compact ? 1 : 2,
        borderBottom: 1,
        borderColor: 'divider',
      }}
    >
      <Stack direction="row" spacing={2} alignItems="center" sx={{ minWidth: 0, flexGrow: 1 }}>
        {icon && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: tokens.hitTarget.lg,
              height: tokens.hitTarget.lg,
              borderRadius: tokens.radius.md,
              bgcolor: (t) => `${t.palette.primary.main}14`,
              color: 'primary.main',
              flexShrink: 0,
            }}
          >
            {icon}
          </Box>
        )}
        <Box sx={{ minWidth: 0 }}>
          {breadcrumbs && (
            <Typography
              variant="overline"
              color="text.secondary"
              sx={{ display: 'block', mb: 0.5, lineHeight: 1.2 }}
            >
              {breadcrumbs.join(' / ')}
            </Typography>
          )}
          <Typography
            variant={compact ? 'h5' : 'h4'}
            component="h1"
            sx={{
              fontWeight: 700,
              letterSpacing: '-0.01em',
              lineHeight: 1.2,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {title}
          </Typography>
          {subtitle && (
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mt: 0.5, maxWidth: 720 }}
            >
              {subtitle}
            </Typography>
          )}
        </Box>
      </Stack>

      {actions && (
        <Stack
          direction="row"
          spacing={1.5}
          sx={{
            flexShrink: 0,
            width: { xs: '100%', sm: 'auto' },
            '& > *': { flexGrow: { xs: 1, sm: 0 } },
          }}
        >
          {actions}
        </Stack>
      )}
    </Box>
  );
};

export default PageHeader;
