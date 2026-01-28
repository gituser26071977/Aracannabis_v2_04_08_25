import React, { useState, useEffect } from 'react';
import {
  Grid,
  TextField,
  Button,
  Box,
  Typography
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';

const ProductForm = ({ onSubmit, onCancel, initialData = {} }) => {
  const [formData, setFormData] = useState({
    nome: '',
    tipo: 'oleo',
    concentracao_cbd: '',
    concentracao_thc: '',
    concentracao_cbg: '',
    concentracao_cbn: '',
    gotas_por_ml: 30,
    volume_ml: 30,
    fabricante: '',
    descricao: '',
    data_registro: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!formData.nome.trim()) {
      alert('Nome do produto é obrigatório');
      return;
    }

    // Converter valores numéricos
    const processedData = {
      ...formData,
      concentracao_cbd: parseFloat(formData.concentracao_cbd) || 0,
      concentracao_thc: parseFloat(formData.concentracao_thc) || 0,
      concentracao_cbg: parseFloat(formData.concentracao_cbg) || 0,
      concentracao_cbn: parseFloat(formData.concentracao_cbn) || 0,
      gotas_por_ml: parseInt(formData.gotas_por_ml) || 30,
      volume_ml: parseFloat(formData.volume_ml) || 30
      // data_registro already string, backend parses it
    };

    onSubmit(processedData);
  };

  useEffect(() => {
    setFormData({
      nome: initialData.nome || '',
      tipo: initialData.tipo || 'oleo',
      concentracao_cbd: initialData.concentracao_cbd ?? '',
      concentracao_thc: initialData.concentracao_thc ?? '',
      concentracao_cbg: initialData.concentracao_cbg ?? '',
      concentracao_cbn: initialData.concentracao_cbn ?? '',
      gotas_por_ml: initialData.gotas_por_ml ?? 30,
      volume_ml: initialData.volume_ml ?? 30,
      fabricante: initialData.fabricante || '',
      descricao: initialData.descricao || '',
      data_registro: initialData.data_registro || new Date().toISOString().split('T')[0] // Default to today if new
    });
  }, [initialData]);

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mb: 4 }}>
      <Typography variant="subtitle1" gutterBottom>
        Cadastrar Novo Produto
      </Typography>

      <Grid container spacing={2}>
        <Grid item xs={12} sm={6}>
          <TextField
            name="nome"
            label="Nome do Produto"
            value={formData.nome}
            onChange={handleChange}
            fullWidth
            required
            placeholder="Ex: Óleo CBD 10%"
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            name="fabricante"
            label="Fabricante"
            value={formData.fabricante}
            onChange={handleChange}
            fullWidth
            placeholder="Ex: Empresa XYZ"
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            name="data_registro"
            label="Data de Registro"
            type="date"
            value={formData.data_registro}
            onChange={handleChange}
            fullWidth
            InputLabelProps={{
              shrink: true,
            }}
          />
        </Grid>

        <Grid item xs={6} sm={3}>
          <TextField
            name="concentracao_cbd"
            label="CBD (mg/ml)"
            type="number"
            value={formData.concentracao_cbd}
            onChange={handleChange}
            fullWidth
            inputProps={{ min: 0, step: 0.1 }}
          />
        </Grid>

        <Grid item xs={6} sm={3}>
          <TextField
            name="concentracao_thc"
            label="THC (mg/ml)"
            type="number"
            value={formData.concentracao_thc}
            onChange={handleChange}
            fullWidth
            inputProps={{ min: 0, step: 0.1 }}
          />
        </Grid>

        <Grid item xs={6} sm={3}>
          <TextField
            name="concentracao_cbg"
            label="CBG (mg/ml)"
            type="number"
            value={formData.concentracao_cbg}
            onChange={handleChange}
            fullWidth
            inputProps={{ min: 0, step: 0.1 }}
          />
        </Grid>

        <Grid item xs={6} sm={3}>
          <TextField
            name="concentracao_cbn"
            label="CBN (mg/ml)"
            type="number"
            value={formData.concentracao_cbn}
            onChange={handleChange}
            fullWidth
            inputProps={{ min: 0, step: 0.1 }}
          />
        </Grid>

        <Grid item xs={6} sm={3}>
          <TextField
            name="gotas_por_ml"
            label="Gotas por ml"
            type="number"
            value={formData.gotas_por_ml}
            onChange={handleChange}
            fullWidth
            inputProps={{ min: 1, max: 50 }}
          />
        </Grid>

        <Grid item xs={6} sm={3}>
          <TextField
            name="volume_ml"
            label="Volume (ml)"
            type="number"
            value={formData.volume_ml}
            onChange={handleChange}
            fullWidth
            inputProps={{ min: 1 }}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
            name="descricao"
            label="Descrição"
            value={formData.descricao}
            onChange={handleChange}
            fullWidth
            multiline
            rows={2}
            placeholder="Descrição detalhada do produto"
          />
        </Grid>

        <Grid item xs={12}>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              startIcon={<AddIcon />}
            >
              Criar Produto
            </Button>
            <Button
              type="button"
              variant="outlined"
              onClick={onCancel}
            >
              Cancelar
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ProductForm;
