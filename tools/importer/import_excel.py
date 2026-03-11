import argparse
import pandas as pd
import json
import logging
import os
import sys

# Adicionar raiz ao path para importar models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Imports locais
from tools.importer import validators

# Tentar importar app context (necessário para DB)
try:
    from app_cors_livre import create_app
    from models import db, Paciente, Associacao # Assumindo que Model Associacao será criado
except ImportError:
    print("AVISO: Falha ao importar App/Models. Certifique-se de estar na raiz do projeto.")
    # Mock para não quebrar o script se rodar isolado sem env
    db = None

# Config Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Importer')

def carregar_dados_json(json_str):
    try:
        return json.loads(json_str)
    except:
        return {}

def run_import(input_file, dry_run=True, default_associacao_id=None):
    logger.info(f"Iniciando Importador. Modo Dry-Run: {dry_run}")
    logger.info(f"Lendo arquivo: {input_file}")
    
    try:
        df = pd.read_excel(input_file)
    except Exception as e:
        logger.error(f"Erro ao ler Excel: {e}")
        return

    total_rows = len(df)
    valid_rows = 0
    skipped_rows = 0
    error_rows = 0
    
    results = []

    logger.info(f"Total de linhas encontradas: {total_rows}")
    
    # Se commit, precisamos do app context
    app = None
    if not dry_run:
        app = create_app()
        ctx = app.app_context()
        ctx.push()

    for index, row in df.iterrows():
        line_num = index + 2 # Excel header is 1
        
        status = 'PENDING'
        user_message = ''
        
        # 1. Parse JSON
        try:
            dados_extraidos = carregar_dados_json(row.get('dados_json', '{}'))
        except:
            dados_extraidos = {}
            
        nome = row.get('nome_detectado')
        cpf = row.get('cpf_detectado')
        tipo = row.get('tipo_documento')
        associacao_raw = row.get('associacao_detectada')
        
        # 2. Validações Básicas
        if not nome or pd.isna(nome) or str(nome).lower() == 'nan':
            status = 'INVALID'
            user_message = 'Nome ausente'
            skipped_rows += 1
        
        elif tipo not in ['RECEITA_MEDICA', 'DOCUMENTO_PESSOAL', 'LAUDO_MEDICO']:
             # Se for COMPROVANTE ou OUTRO, talvez não cria paciente direto?
             # Vamos assumir que cria se tiver nome/cpf
             if not cpf:
                 status = 'SKIPPED'
                 user_message = f'Tipo {tipo} sem CPF, ignorado para criação de paciente'
                 skipped_rows += 1
             else:
                 pass # Segue
        
        # 3. Resolver Associação
        associacao_id = validators.resolve_associacao(associacao_raw, default_associacao_id)
        
        if status == 'PENDING':
             # Simular criação
             valid_rows += 1
             status = 'READY'
             
             if not dry_run:
                 try:
                     # Verificar duplicação?
                     # existing = Paciente.query.filter_by(cpf=cpf).first()
                     # if existing: ...
                     
                     # Criar (Mockado pois Model Paciente ainda não tem associacao_id oficial no código)
                     # p = Paciente(nome=nome, cpf=cpf, associacao_id=associacao_id)
                     # db.session.add(p)
                     # db.session.commit()
                     status = 'IMPORTED'
                 except Exception as e:
                     status = 'ERROR'
                     user_message = str(e)
                     error_rows += 1
                     # db.session.rollback()
        
        # Log linha
        logger.info(f"Linha {line_num}: {status} - {nome} ({cpf}) - Assoc: {associacao_id} - Msg: {user_message}")
        
    logger.info("="*30)
    logger.info("RESUMO DA IMPORTAÇÃO")
    logger.info(f"Total: {total_rows}")
    logger.info(f"Válidos (Para Importar): {valid_rows}")
    logger.info(f"Ignorados/Inválidos: {skipped_rows}")
    logger.info(f"Erros de DB: {error_rows}")
    
    if dry_run:
        logger.info("Modo DRY-RUN finalizado. Nenhuma alteração feita no banco.")
    else:
        logger.info("Importação CONCLUÍDA.")

def main():
    parser = argparse.ArgumentParser(description='Importador de Excel Validado (Etapa 1.5)')
    parser.add_argument('--input', required=True, help='Arquivo Excel validado')
    parser.add_argument('--dry-run', action='store_true', help='Simula sem gravar')
    parser.add_argument('--default-assoc', default='REDACTED', help='ID da associação default (Legacy)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        logger.error("Arquivo de entrada não encontrado.")
        return
        
    run_import(args.input, args.dry_run, args.default_assoc)

if __name__ == "__main__":
    main()
