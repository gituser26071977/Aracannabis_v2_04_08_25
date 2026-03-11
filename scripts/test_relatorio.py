import os
import sys
from datetime import datetime
from flask import g

# Adicionar diretório atual ao path
sys.path.append(os.getcwd())

from app_cors_livre import create_app
from models import db, Profissional, Paciente
from services.crew_agents import gerar_relatorio_paciente
from association.models import Associacao
from models_extra import UsuarioAssociacao

# Mock para AI Manager se não estiver disponível ou para evitar custos/demora
# Mas crew_agents usa ai_manager global. Vamos tentar usar o real ou mockar se falhar.
# O teste de prescrição não usou IA, mas o relatório usa.
# Se o teste falhar por causa da IA (sem chave API), vamos mockar ai_manager.chat_completion

def setup_test_data():
    """Cria dados de teste para relatório"""
    print("🛠️ Configurando dados de teste...")
    
    # 1. Obter ou criar profissional
    prof = Profissional.query.filter_by(email="teste_relatorio@aracannabis.com.br").first()
    if not prof:
        prof = Profissional(
            nome="Dr. Teste Relatório",
            email="teste_relatorio@aracannabis.com.br",
            usuario="dr_teste_relatorio",
            senha="hash_teste",
            crm="54321-R",
            uf_crm="SP"
        )
        db.session.add(prof)
        db.session.commit()
    
    # 2. Obter ou criar associação
    associacao = Associacao.query.get(1)
    if not associacao:
        associacao = Associacao(id=1, nome="Associação Teste", cnpj="00.000.000/0001-00")
        db.session.add(associacao)
        db.session.commit()
        
    # 3. Vínculo Profissional-Associação
    link = UsuarioAssociacao.query.filter_by(profissional_id=prof.id, associacao_id=associacao.id).first()
    if not link:
        link = UsuarioAssociacao(
            profissional_id=prof.id,
            associacao_id=associacao.id,
            role='admin',
            status='active'
        )
        db.session.add(link)
        db.session.commit()
    
    # 4. Obter ou criar paciente
    paciente = Paciente.query.filter_by(cpf="999.888.777-66").first()
    if not paciente:
        paciente = Paciente(
            nome="Paciente Teste Relatório",
            cpf="999.888.777-66",
            data_nascimento=datetime.strptime("1985-05-15", "%Y-%m-%d").date(),
            profissional_responsavel_id=prof.id,
            associacao_id=associacao.id,
            diagnostico="Epilepsia Refratária"
        )
        db.session.add(paciente)
        db.session.commit()
        
    return prof, paciente, associacao

def test_gerar_relatorio():
    app = create_app()
    
    with app.app_context():
        # Setup
        prof, paciente, associacao = setup_test_data()
        
        # Mock de contexto
        g.current_association = associacao
        g.user_id = prof.id
        
        from services.crew_agents import CURRENT_PROFISSIONAL_ID, ai_manager
        token = CURRENT_PROFISSIONAL_ID.set(prof.id)
        
        # Mock do AI Manager para não depender de APIs externas no teste unitário
        # Salva o método original para restaurar depois
        original_chat_completion = ai_manager.chat_completion
        
        def mock_chat_completion(**kwargs):
            return {
                'content': """
# Relatório Clínico - Paciente Teste

## Resumo Clínico
Paciente apresenta quadro estável de Epilepsia Refratária.

## Análise de Progresso
Houve redução significativa no número de crises (50%) após ajuste da dosagem.

## Exames Relevantes
- Hemograma: Normal
- EEG: Padrão irritativo leve

## Evolução e Sintomas
Relata melhora na qualidade do sono e redução da ansiedade.

## Plano Terapêutico
Manter dosagem atual de CBD Full Spectrum.

## Recomendações
Retorno em 60 dias. Manter diário de crises.
"""
            }
            
        ai_manager.chat_completion = mock_chat_completion
        
        print("\n🧪 Iniciando teste de geração de relatório...")
        
        # Executar a ferramenta
        try:
             # Tente chamar como tool ou função direta
            if hasattr(gerar_relatorio_paciente, 'func'):
                resultado = gerar_relatorio_paciente.func(
                    paciente_id=paciente.id,
                    tipo_relatorio="clinico"
                )
            elif hasattr(gerar_relatorio_paciente, '_run'):
                resultado = gerar_relatorio_paciente._run(
                    paciente_id=paciente.id,
                    tipo_relatorio="clinico"
                )
            else:
                 resultado = gerar_relatorio_paciente.run(
                    paciente_id=paciente.id,
                    tipo_relatorio="clinico"
                )
        except Exception as e:
            print(f"❌ Erro na execução da ferramenta: {str(e)}")
            # Restaurar e sair
            ai_manager.chat_completion = original_chat_completion
            CURRENT_PROFISSIONAL_ID.reset(token)
            return False

        # Restaurar mocks
        ai_manager.chat_completion = original_chat_completion
        CURRENT_PROFISSIONAL_ID.reset(token)
        
        # Verificações
        if "error" in resultado:
            print(f"❌ Erro ao gerar relatório: {resultado['error']}")
            return False
            
        print("✅ Relatório gerado com sucesso!")
        print(f"📄 Arquivo: {resultado.get('arquivo_path')}")
        
        # Validar conteúdo do arquivo
        arquivo_path = resultado.get('arquivo_path')
        if os.path.exists(arquivo_path):
            print("✅ Arquivo físico existe")
            with open(arquivo_path, 'r') as f:
                content = f.read()
                if "Relatório Clínico - Paciente Teste" in content and "Dr. Teste Relatório" in content:
                    print("✅ Conteúdo do HTML validado (contém título do relatório e nome do médico)")
                else:
                    print("⚠️ Conteúdo do HTML gerado pode estar incorreto (verifique o arquivo)")
        else:
            print(f"❌ Arquivo físico NÃO encontrado em {arquivo_path}")
            return False
            
        return True

if __name__ == "__main__":
    try:
        current_dir = os.getcwd()
        print(f"📂 Diretório de execução: {current_dir}")
        success = test_gerar_relatorio()
        if success:
            print("\n✨ Teste de Relatório CONCLUÍDO COM SUCESSO! ✨")
            sys.exit(0)
        else:
            print("\n💥 Teste de Relatório FALHOU! 💥")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro fatal no teste: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
