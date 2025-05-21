-- Esquema do Banco de Dados para o Sistema de Prontuário Eletrônico de Cannabis Medicinal

-- Tabela de profissionais (médicos)
CREATE TABLE IF NOT EXISTS profissionais (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    crm TEXT UNIQUE NOT NULL,
    usuario TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de pacientes
CREATE TABLE IF NOT EXISTS pacientes (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    data_nascimento DATE NOT NULL,
    telefone TEXT,
    email TEXT,
    em_tratamento BOOLEAN NOT NULL DEFAULT FALSE,
    composicao TEXT,
    dosagem TEXT,
    horarios TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de sintomas
CREATE TABLE IF NOT EXISTS sintomas (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL,
    data DATE NOT NULL,
    sintoma TEXT NOT NULL,
    intensidade INTEGER NOT NULL CHECK (intensidade BETWEEN 0 AND 10),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE,
    UNIQUE(paciente_id, data, sintoma)
);

-- Tabela de dosagens
CREATE TABLE IF NOT EXISTS dosagens (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL,
    data DATE NOT NULL,
    dosagem TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
);

-- Tabela de evolução médica
CREATE TABLE IF NOT EXISTS evolucoes (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL,
    profissional_id INTEGER,
    data_evolucao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    nota_evolucao TEXT NOT NULL,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE,
    FOREIGN KEY (profissional_id) REFERENCES profissionais(id) ON DELETE SET NULL
);

-- Tabela de logs de atividades (para auditoria)
CREATE TABLE IF NOT EXISTS logs_atividades (
    id SERIAL PRIMARY KEY,
    profissional_id INTEGER,
    acao TEXT NOT NULL,
    detalhes TEXT,
    data_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profissional_id) REFERENCES profissionais(id) ON DELETE SET NULL
);

-- Índices para melhorar a performance
CREATE INDEX IF NOT EXISTS idx_sintomas_paciente_id ON sintomas(paciente_id);
CREATE INDEX IF NOT EXISTS idx_sintomas_data ON sintomas(data);
CREATE INDEX IF NOT EXISTS idx_dosagens_paciente_id ON dosagens(paciente_id);
CREATE INDEX IF NOT EXISTS idx_dosagens_data ON dosagens(data);
CREATE INDEX IF NOT EXISTS idx_evolucoes_paciente_id ON evolucoes(paciente_id);
CREATE INDEX IF NOT EXISTS idx_evolucoes_data ON evolucoes(data_evolucao);
CREATE INDEX IF NOT EXISTS idx_logs_profissional_id ON logs_atividades(profissional_id);
CREATE INDEX IF NOT EXISTS idx_logs_data ON logs_atividades(data_hora);
