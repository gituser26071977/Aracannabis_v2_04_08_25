-- Esquema do Banco de Dados para o Sistema de Prontuário Eletrônico de Cannabis Medicinal

-- Tabela de profissionais (médicos)
CREATE TABLE IF NOT EXISTS profissionais (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    crm TEXT UNIQUE NOT NULL,
    usuario TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    email TEXT NOT NULL,  -- Adicionado campo email
    telefone TEXT,
    especialidade TEXT,
    instituicao TEXT,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    tipo_conta TEXT,
    data_expiracao TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de senhas temporárias
CREATE TABLE IF NOT EXISTS senhas_temporarias (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    senha_hash TEXT NOT NULL,
    data_expiracao TIMESTAMP NOT NULL,
    usado BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (usuario_id) REFERENCES profissionais(id) ON DELETE CASCADE
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

-- Tabela de exames
CREATE TABLE IF NOT EXISTS exames (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL,
    profissional_id INTEGER,
    data_exame TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tipo_exame TEXT NOT NULL,  -- 'imaging' ou 'lab'
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE,
    FOREIGN KEY (profissional_id) REFERENCES profissionais(id) ON DELETE SET NULL
);

-- Tabela para exames de imagem (ultrassons, tomografias, etc.)
CREATE TABLE IF NOT EXISTS exame_imagens (
    id SERIAL PRIMARY KEY,
    exame_id INTEGER NOT NULL,
    arquivo_nome TEXT NOT NULL,
    arquivo_caminho TEXT NOT NULL,
    laudo TEXT NOT NULL,
    FOREIGN KEY (exame_id) REFERENCES exames(id) ON DELETE CASCADE
);

-- Tabela para exames laboratoriais (hemograma, etc.)
CREATE TABLE IF NOT EXISTS exame_lab_resultados (
    id SERIAL PRIMARY KEY,
    exame_id INTEGER NOT NULL,
    teste_nome TEXT NOT NULL,
    valor NUMERIC NOT NULL,
    unidade TEXT NOT NULL,
    valor_referencia TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exame_id) REFERENCES exames(id) ON DELETE CASCADE
);

-- Tabela de solicitações de cadastro de profissionais
CREATE TABLE IF NOT EXISTS solicitacoes_cadastro (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    email TEXT NOT NULL,
    crm TEXT NOT NULL,
    uf_crm TEXT NOT NULL,
    telefone TEXT,
    especialidade TEXT,
    instituicao TEXT,
    status TEXT NOT NULL DEFAULT 'pendente',
    data_solicitacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_aprovacao TIMESTAMP,
    observacoes TEXT,
    aprovado_por INTEGER REFERENCES profissionais(id) ON DELETE SET NULL
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

-- Tabela de sintomas personalizados
CREATE TABLE IF NOT EXISTS sintomas_personalizados (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    nome TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(paciente_id, nome)
);

-- Índices para melhorar a performance
CREATE INDEX IF NOT EXISTS idx_sintomas_paciente_id ON sintomas(paciente_id);
CREATE INDEX IF NOT EXISTS idx_sintomas_data ON sintomas(data);
CREATE INDEX IF NOT EXISTS idx_dosagens_paciente_id ON dosagens(paciente_id);
CREATE INDEX IF NOT EXISTS idx_dosagens_data ON dosagens(data);
CREATE INDEX IF NOT EXISTS idx_evolucoes_paciente_id ON evolucoes(paciente_id);
CREATE INDEX IF NOT EXISTS idx_evolucoes_data ON evolucoes(data_evolucao);
CREATE INDEX IF NOT EXISTS idx_exames_paciente_id ON exames(paciente_id);
CREATE INDEX IF NOT EXISTS idx_exames_data ON exames(data_exame);
CREATE INDEX IF NOT EXISTS idx_exame_imagens_exame_id ON exame_imagens(exame_id);
CREATE INDEX IF NOT EXISTS idx_exame_lab_resultados_exame_id ON exame_lab_resultados(exame_id);
CREATE INDEX IF NOT EXISTS idx_logs_profissional_id ON logs_atividades(profissional_id);
CREATE INDEX IF NOT EXISTS idx_logs_data ON logs_atividades(data_hora);
CREATE INDEX IF NOT EXISTS idx_solicitacoes_email ON solicitacoes_cadastro(email);
CREATE INDEX IF NOT EXISTS idx_solicitacoes_crm_uf ON solicitacoes_cadastro(crm, uf_crm);
