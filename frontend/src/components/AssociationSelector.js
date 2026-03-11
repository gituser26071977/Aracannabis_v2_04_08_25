import React, { useState } from 'react';
import { useAssociation } from '../contexts/AssociationContext';
import { Select, MenuItem, FormControl, InputLabel, Box, Typography } from '@mui/material';
import BusinessIcon from '@mui/icons-material/Business';

const AssociationSelector = () => {
    const { currentAssociation, userAssociations, selectAssociation, loading } = useAssociation();

    if (loading) return null;

    if (userAssociations.length <= 1 && currentAssociation) {
        // If only one, just show the name maybe? Or nothing.
        // Let's show it as a static label for clarity that they are in a context.
        return (
            <Box sx={{ display: 'flex', alignItems: 'center', mr: 2, color: 'white' }}>
                <BusinessIcon sx={{ mr: 1, fontSize: 20 }} />
                <Typography variant="body2" fontWeight="bold">
                    {currentAssociation.nome}
                </Typography>
            </Box>
        );
    }

    if (!currentAssociation) return null;

    const handleChange = (event) => {
        const selectedId = event.target.value;
        const selected = userAssociations.find(a => a.id === selectedId);
        if (selected) {
            selectAssociation(selected);
        }
    };

    return (
        <FormControl variant="standard" sx={{ m: 1, minWidth: 120 }}>
            <Select
                id="association-select"
                value={currentAssociation.id}
                onChange={handleChange}
                label="Associação"
                disableUnderline
                sx={{
                    color: 'white',
                    '.MuiSelect-icon': { color: 'white' },
                    fontSize: '0.875rem',
                    fontWeight: 500
                }}
                renderValue={(selected) => {
                    const selectedAssoc = userAssociations.find(a => a.id === selected);
                    return (
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <BusinessIcon sx={{ mr: 1, fontSize: 18 }} />
                            {selectedAssoc ? selectedAssoc.nome : 'Selecione'}
                        </Box>
                    );
                }}
            >
                {userAssociations.map((assoc) => (
                    <MenuItem key={assoc.id} value={assoc.id}>
                        {assoc.nome}
                    </MenuItem>
                ))}
            </Select>
        </FormControl>
    );
};

export default AssociationSelector;
