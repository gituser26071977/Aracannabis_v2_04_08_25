"""
Modelos de dados para catálogo de produtos de cannabis medicinal
"""
from datetime import datetime
from models import db


class ProdutoCannabis(db.Model):
    """Modelo para produtos de cannabis medicinal"""
    __tablename__ = 'produtos_cannabis'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informações básicas
    nome = db.Column(db.String(255), nullable=False)
    nome_comercial = db.Column(db.String(255))
    marca = db.Column(db.String(100), nullable=False)
    laboratorio = db.Column(db.String(100))
    cnpj_fabricante = db.Column(db.String(20))
    
    # Categoria e tipo
    categoria = db.Column(db.String(50))  # Óleo, Cápsula, Floral, Tópico, etc
    tipo_extracao = db.Column(db.String(50))  # CO2, Etanol, Hidrossolúvel, etc
    origem_cannabis = db.Column(db.String(50))  # Nacional, Importada, etc
    
    # Composição - Canabinoides (em mg/ml ou mg/cápsula)
    cbd_total_mg = db.Column(db.Numeric(10, 2))
    thc_total_mg = db.Column(db.Numeric(10, 2))
    cbg_mg = db.Column(db.Numeric(10, 2))
    cbn_mg = db.Column(db.Numeric(10, 2))
    cbc_mg = db.Column(db.Numeric(10, 2))
    thcv_mg = db.Column(db.Numeric(10, 2))
    cbdv_mg = db.Column(db.Numeric(10, 2))
    
    # Composição - Porcentagem
    cbd_percent = db.Column(db.Numeric(5, 2))
    thc_percent = db.Column(db.Numeric(5, 2))
    
    # Quimiotipo
    quimiotipo = db.Column(db.String(20))  # Tipo I (THC), Tipo II (THC+CBD), Tipo III (CBD), Tipo IV (CBG), etc
    
    # Razão CBD:THC
    razao_cbd_thc = db.Column(db.String(20))
    
    # Perfil de terpenos (em porcentagem)
    mirceno = db.Column(db.Numeric(5, 2))
    limoneno = db.Column(db.Numeric(5, 2))
    linalol = db.Column(db.Numeric(5, 2))
    beta_cariofileno = db.Column(db.Numeric(5, 2))
    alfa_pineno = db.Column(db.Numeric(5, 2))
    beta_pineno = db.Column(db.Numeric(5, 2))
    humuleno = db.Column(db.Numeric(5, 2))
    terpinoleno = db.Column(db.Numeric(5, 2))
    
    # Informações do produto
    apresentacao = db.Column(db.String(100))  # Frasco 30ml, Caixa 30 cápsulas, etc
    volume_ml = db.Column(db.Numeric(8, 2))
    quantidade_cps = db.Column(db.Integer)
    via_administracao = db.Column(db.String(50))  # Sublingual, Oral, Tópica, etc
    
    # Características
    espectro = db.Column(db.String(30))  # Full spectrum, Broad spectrum, Isolate
    veiculo = db.Column(db.String(50))  # Óleo MCT, Azeite, etc
    composicao_veiculo = db.Column(db.Text)
    
    # Indicações e contraindicações
    indicacoes = db.Column(db.Text)  # Lista de indicações separadas por vírgula
    contraindicacoes = db.Column(db.Text)
    interacoes = db.Column(db.Text)
    
    # Posologia sugerida
    posologia_inicial = db.Column(db.Text)
    posologia_manutencao = db.Column(db.Text)
    posologia_maxima = db.Column(db.Text)
    
    # Regulatório
    registro_anvisa = db.Column(db.String(50))
    tipo_registro = db.Column(db.String(30))  # Saneantes, Cosméticos, Importação, etc
    rdc_327_2019 = db.Column(db.Boolean, default=False)
    
    # Disponibilidade
    disponivel_brasil = db.Column(db.Boolean, default=True)
    necessita_receita = db.Column(db.Boolean, default=True)
    controle_especial = db.Column(db.String(10))  # A1, A2, A3, B1, B2, C1, C2, C5
    
    # Preço e distribuição
    preco_referencia = db.Column(db.Numeric(10, 2))
    codigo_barras = db.Column(db.String(50))
    distribuidores = db.Column(db.Text)
    
    # Dados de importação
    pais_origem = db.Column(db.String(50))
    importador = db.Column(db.String(100))
    
    # Metadados
    associacao_id = db.Column(db.Integer, db.ForeignKey('associacoes.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('profissionais.id'))
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    verificado = db.Column(db.Boolean, default=False)  # Verificado por profissional
    
    # Fonte dos dados
    fonte_dados = db.Column(db.String(100))  # Catálogo, PDF, Web, Manual
    url_origem = db.Column(db.Text)
    arquivo_origem = db.Column(db.String(255))
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'nome_comercial': self.nome_comercial,
            'marca': self.marca,
            'laboratorio': self.laboratorio,
            'categoria': self.categoria,
            'tipo_extracao': self.tipo_extracao,
            'quimiotipo': self.quimiotipo,
            'cbd_total_mg': float(self.cbd_total_mg) if self.cbd_total_mg else None,
            'thc_total_mg': float(self.thc_total_mg) if self.thc_total_mg else None,
            'cbg_mg': float(self.cbg_mg) if self.cbg_mg else None,
            'cbn_mg': float(self.cbn_mg) if self.cbn_mg else None,
            'cbc_mg': float(self.cbc_mg) if self.cbc_mg else None,
            'thcv_mg': float(self.thcv_mg) if self.thcv_mg else None,
            'cbdv_mg': float(self.cbdv_mg) if self.cbdv_mg else None,
            'cbd_percent': float(self.cbd_percent) if self.cbd_percent else None,
            'thc_percent': float(self.thc_percent) if self.thc_percent else None,
            'razao_cbd_thc': self.razao_cbd_thc,
            'espectro': self.espectro,
            'via_administracao': self.via_administracao,
            'apresentacao': self.apresentacao,
            'volume_ml': float(self.volume_ml) if self.volume_ml else None,
            'quantidade_cps': self.quantidade_cps,
            'indicacoes': self.indicacoes,
            'contraindicacoes': self.contraindicacoes,
            'posologia_inicial': self.posologia_inicial,
            'posologia_manutencao': self.posologia_manutencao,
            'preco_referencia': float(self.preco_referencia) if self.preco_referencia else None,
            'disponivel_brasil': self.disponivel_brasil,
            'necessita_receita': self.necessita_receita,
            'ativo': self.ativo,
            'verificado': self.verificado,
            'fonte_dados': self.fonte_dados,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CatalogoImportacao(db.Model):
    """Registro de importações de catálogos"""
    __tablename__ = 'catalogo_importacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informações do arquivo
    nome_arquivo = db.Column(db.String(255), nullable=False)
    tipo_arquivo = db.Column(db.String(10))  # pdf, xlsx, csv, docx, txt
    tamanho_arquivo = db.Column(db.Integer)
    
    # Dados da importação
    empresa_origem = db.Column(db.String(100))
    total_produtos = db.Column(db.Integer, default=0)
    produtos_importados = db.Column(db.Integer, default=0)
    produtos_atualizados = db.Column(db.Integer, default=0)
    erros = db.Column(db.Text)
    
    # Status
    status = db.Column(db.String(20), default='processando')  # processando, concluido, erro, parcial
    
    # Metadados
    associacao_id = db.Column(db.Integer, db.ForeignKey('associacoes.id'), nullable=True)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Caminho do arquivo
    arquivo_path = db.Column(db.String(500))
    
    # Processamento por IA
    processado_ia = db.Column(db.Boolean, default=False)
    extracao_dados = db.Column(db.JSON)  # Dados brutos extraídos pelo agente
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome_arquivo': self.nome_arquivo,
            'tipo_arquivo': self.tipo_arquivo,
            'empresa_origem': self.empresa_origem,
            'total_produtos': self.total_produtos,
            'produtos_importados': self.produtos_importados,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processado_ia': self.processado_ia
        }


class SugestaoPrescricao(db.Model):
    """Registro de sugestões de produtos para prescrições"""
    __tablename__ = 'sugestoes_prescricao'
    
    id = db.Column(db.Integer, primary_key=True)
    
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id'), nullable=False)
    
    # Critérios da busca
    condicao_medica = db.Column(db.String(100))
    sintomas_alvo = db.Column(db.Text)
    evitar_thc = db.Column(db.Boolean, default=False)
    preferencia_cbd = db.Column(db.Boolean, default=False)
    via_preferida = db.Column(db.String(50))
    
    # Sugestões geradas
    produtos_sugeridos = db.Column(db.JSON)  # Lista de IDs e justificativas
    justificativa_ia = db.Column(db.Text)
    
    # Feedback
    prescricao_gerada = db.Column(db.Boolean, default=False)
    produto_escolhido_id = db.Column(db.Integer, db.ForeignKey('produtos_cannabis.id'))
    feedback_eficacia = db.Column(db.Integer)  # 1-5 estrelas
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'paciente_id': self.paciente_id,
            'condicao_medica': self.condicao_medica,
            'sintomas_alvo': self.sintomas_alvo,
            'produtos_sugeridos': self.produtos_sugeridos,
            'justificativa_ia': self.justificativa_ia,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }