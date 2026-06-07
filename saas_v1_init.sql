-- Migration Phase 1: SaaS Initialization (Minimal Scope)

-- 1. Enable UUID extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Create 'associacoes' table
CREATE TABLE IF NOT EXISTS associacoes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    cnpj VARCHAR(18),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Insert Default Associations
-- Using fixed UUIDs for predictability in scripts
INSERT INTO associacoes (id, nome, slug, cnpj) 
VALUES 
    ('REDACTED', 'Aracannabis Legacy', 'legacy', NULL),
    ('REDACTED', 'HC Agrobuds', 'agrobuds', NULL)
ON CONFLICT (slug) DO NOTHING;

-- 4. Alter 'pacientes' table
-- Add column nullable first
ALTER TABLE pacientes 
ADD COLUMN IF NOT EXISTS associacao_id UUID REFERENCES associacoes(id);

-- 5. Backfill existing data
-- All existing patients go to Legacy (default)
UPDATE pacientes 
SET associacao_id = 'REDACTED' 
WHERE associacao_id IS NULL;

-- 6. Create Index for performance
CREATE INDEX IF NOT EXISTS idx_pacientes_associacao ON pacientes(associacao_id);

-- 7. Verification Query (Run manually to check)
-- SELECT count(*) FROM pacientes WHERE associacao_id IS NULL;
