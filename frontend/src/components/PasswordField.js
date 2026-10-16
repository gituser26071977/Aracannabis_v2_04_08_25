import React, { useState } from 'react';
import { TextField, InputAdornment, IconButton } from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';

/**
 * PasswordField — TextField de senha com botão de exibir/ocultar caracteres.
 *
 * Aceita as mesmas props de `TextField` (label, value, onChange, sx, ...).
 * O tipo alterna entre `password` e `text` ao clicar no ícone de olho.
 */
const PasswordField = ({ InputProps, ...props }) => {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <TextField
      {...props}
      type={showPassword ? 'text' : 'password'}
      InputProps={{
        ...InputProps,
        endAdornment: (
          <InputAdornment position="end">
            <IconButton
              edge="end"
              aria-label={showPassword ? 'Ocultar senha' : 'Exibir senha'}
              title={showPassword ? 'Ocultar senha' : 'Exibir senha'}
              onClick={() => setShowPassword((prev) => !prev)}
              onMouseDown={(event) => event.preventDefault()}
            >
              {showPassword ? <VisibilityOff /> : <Visibility />}
            </IconButton>
          </InputAdornment>
        ),
      }}
    />
  );
};

export default PasswordField;
