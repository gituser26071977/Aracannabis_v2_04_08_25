/**
 * QuickChipSelect — seletor de 1-click para valores recorrentes.
 *
 * Resolve:
 *   - Médico digita "ABRACE" / "Santa Cannabis" toda vez
 *   - Free-text em campos como "Associação", "Tipo de consulta", "Via de administração"
 *
 * Mostra até 6 chips clicáveis + opção de digitar valor novo (outros).
 *
 * Uso:
 *   <QuickChipSelect
 *     label="Associação"
 *     value={form.associacao}
 *     onChange={(v) => setForm({ ...form, associacao: v })}
 *     options={['ABRACE', 'Santa Cannabis', 'Cannabis Sem Fronteiras', 'Cultive']}
 *     rememberKey="associacao"
 *   />
 */
import React, { useState } from 'react';
import { Box, Chip, TextField, Stack, Typography } from '@mui/material';
import useRemember from '../hooks/useRemember';

const QuickChipSelect = ({
  label,
  value,
  onChange,
  options = [],
  rememberKey,        // opcional: se passado, persiste último valor
  maxChips = 6,
  allowCustom = true,
  customPlaceholder = 'Outro (digite)',
}) => {
  const [remembered, setRemembered] = useRemember(rememberKey || '_unused', value);
  const [customMode, setCustomMode] = useState(
    () => value !== undefined && value !== null && value !== '' && !options.includes(value)
  );
  const [customValue, setCustomValue] = useState(() => customMode ? value : '');

  const handleSelect = (selected) => {
    onChange(selected);
    if (rememberKey) setRemembered(selected);
    setCustomMode(false);
  };

  const handleCustom = (e) => {
    setCustomValue(e.target.value);
    onChange(e.target.value);
  };

  const handleCustomBlur = () => {
    if (customValue && rememberKey) setRemembered(customValue);
  };

  return (
    <Box>
      {label && (
        <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
          {label}
        </Typography>
      )}
      <Stack direction="row" spacing={0.75} sx={{ flexWrap: 'wrap', gap: 0.75 }}>
        {options.slice(0, maxChips).map((opt) => (
          <Chip
            key={opt}
            label={opt}
            size="small"
            onClick={() => handleSelect(opt)}
            color={value === opt ? 'primary' : 'default'}
            variant={value === opt ? 'filled' : 'outlined'}
            sx={{ cursor: 'pointer' }}
          />
        ))}
        {allowCustom && !customMode && (
          <Chip
            label="+ Outro"
            size="small"
            onClick={() => setCustomMode(true)}
            variant="outlined"
            sx={{ cursor: 'pointer', borderStyle: 'dashed' }}
          />
        )}
        {allowCustom && customMode && (
          <TextField
            size="small"
            autoFocus
            value={customValue}
            onChange={handleCustom}
            onBlur={handleCustomBlur}
            placeholder={customPlaceholder}
            sx={{ minWidth: 180, '& .MuiOutlinedInput-root': { borderRadius: 20 } }}
          />
        )}
      </Stack>
    </Box>
  );
};

export default QuickChipSelect;
