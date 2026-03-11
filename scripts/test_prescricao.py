import os
import sys
from datetime import datetime
from flask import g

# Adicionar diretório atual ao path
sys.path.append(os.getcwd())

from app_cors_livre import create_app
from models import db, Profissional, Paciente, Prescricao
from association.models import Associacao
from models_extra import UsuarioAssociacao
from services.crew_agents import gerar_prescricao_chat

def setup_test_data():
    """Cria dados de teste para prescrição"""
    print("🛠️ Configurando dados de teste...")
    
    # 1. Obter ou criar profissional
    prof = Profissional.query.filter_by(email="teste_prescricao@aracannabis.com.br").first()
    if not prof:
        prof = Profissional(
            nome="Dr. Teste Prescrição",
            email="teste_prescricao@aracannabis.com.br",
            usuario="dr_teste_prescricao",
            senha="hash_teste",
            crm="12345-P",
            uf_crm="SP"
        )
        db.session.add(prof)
        db.session.commit()
    
    # 2. Obter ou criar paciente
    paciente = Paciente.query.filter_by(cpf="111.222.333-99").first()
    if not paciente:
        paciente = Paciente(
            nome="Paciente Teste Prescrição",
            cpf="111.222.333-99",
            data_nascimento=datetime.strptime("1990-01-01", "%Y-%m-%d").date(),
            profissional_responsavel_id=prof.id,
            associacao_id=1
        )
        db.session.add(paciente)
        db.session.commit()
        # 3. Garantir Associação e Vínculo
    
    associacao = Associacao.query.get(1)
    if not associacao:
        associacao = Associacao(id=1, nome="Associação Teste", cnpj="00.000.000/0001-00")
        db.session.add(associacao)
        db.session.commit()
    
    # Criar vínculo
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
        
    return prof, paciente

def test_gerar_prescricao():
    app = create_app()
    
    with app.app_context():
        # Setup
        prof, paciente = setup_test_data()
        
        # Simular contexto de request (necessário para 'g' e '_get_current_profissional_id')
        # Como _get_current_profissional_id usa contextvars ou g, vamos mockar ou configurar g
        
        # Mockar g.current_user e g.current_association
        from collections import namedtuple
        Association = namedtuple('Association', ['id', 'nome'])
        g.current_association = Association(id=1, nome="Associação Teste")
        g.user_id = prof.id # Se _get_current_profissional_id usar g.user_id
        
        # Mockar a função _get_current_profissional_id no módulo crew_agents se necessário
        # Mas vamos tentar usar contextvar se for o caso. 
        # No código original, _get_current_profissional_id pode pegar de contextvar.
        # Vamos definir a contextvar
        from services.crew_agents import CURRENT_PROFISSIONAL_ID
        token = CURRENT_PROFISSIONAL_ID.set(prof.id)
        
        print("\n🧪 Iniciando teste de geração de prescrição...")
        
        medicamentos = [
            {
                "nome": "Óleo de CBD Full Spectrum",
                "composicao": "CBD 200mg/ml",
                "posologia": "Inciar com 3 gotas, 2x ao dia (manhã e noite). Aumentar 1 gota a cada 3 dias até atingir efeito desejado.",
                "quantidade": "1 frasco de 30ml"
            },
            {
                "nome": "Óleo de THC Isolado",
                "composicao": "THC 10mg/ml",
                "posologia": "Uso SOS em caso de crise álgica intensa. Máximo 5 gotas.",
                "quantidade": "1 frasco de 10ml"
            }
        ]
        
        observacoes = "Paciente deve retornar em 30 dias para reavaliação. Manter diário de sintomas."
        
        # Executar a ferramenta (tratando objeto Tool do CrewAI/LangChain)
        print(f"DEBUG: Tipo da ferramenta: {type(gerar_prescricao_chat)}")
        try:
            # Tenta chamar diretamente (se não for Tool object)
            resultado = gerar_prescricao_chat(
                paciente_id=paciente.id,
                medicamentos=medicamentos,
                observacoes=observacoes
            )
        except TypeError:
            # Se for Tool object, tenta .run() ou .func()
            if hasattr(gerar_prescricao_chat, 'func'):
                print("DEBUG: Chamando via .func()")
                resultado = gerar_prescricao_chat.func(
                    paciente_id=paciente.id,
                    medicamentos=medicamentos,
                    observacoes=observacoes
                )
            elif hasattr(gerar_prescricao_chat, '_run'):
                 print("DEBUG: Chamando via ._run()")
                 resultado = gerar_prescricao_chat._run(
                    paciente_id=paciente.id,
                    medicamentos=medicamentos,
                    observacoes=observacoes
                )
            else:
                 print("DEBUG: Chamando via .run()")
                 try:
                     resultado = gerar_prescricao_chat.run(
                        paciente_id=paciente.id,
                        medicamentos=medicamentos,
                        observacoes=observacoes
                    )
                 except:
                     # Tenta passar como string json se for o caso (menos provável aqui)
                     raise Exception("Não foi possível invocar a ferramenta")
        
        # Resetar contextvar
        CURRENT_PROFISSIONAL_ID.reset(token)
        
        # Verificações
        if "error" in resultado:
            print(f"❌ Erro ao gerar prescrição: {resultado['error']}")
            return False
            
        print("✅ Prescrição gerada com sucesso!")
        print(f"📄 Arquivo: {resultado.get('arquivo_path')}")
        
        # Validar no banco
        prescricao_db = Prescricao.query.filter_by(paciente_id=paciente.id).order_by(Prescricao.id.desc()).first()
        if not prescricao_db:
            print("❌ Registro não encontrado no banco de dados!")
            return False
            
        print(f"💾 Registro no banco ID: {prescricao_db.id}")
        
        # Validar conteúdo do arquivo
        arquivo_path = resultado.get('arquivo_path')
        if os.path.exists(arquivo_path):
            print("✅ Arquivo físico existe")
            with open(arquivo_path, 'r') as f:
                content = f.read()
                if "Óleo de CBD Full Spectrum" in content and "Dr. Teste Prescrição" in content:
                    print("✅ Conteúdo do HTML validado (contém medicamentos e nome do médico)")
                else:
                    print("❌ Conteúdo do HTML inválido ou incompleto")
        else:
            print(f"❌ Arquivo físico NÃO encontrado em {arquivo_path}")
            
        return True

if __name__ == "__main__":
    try:
        current_dir = os.getcwd()
        print(f"📂 Diretório de execução: {current_dir}")
        success = test_gerar_prescricao()
        if success:
            print("\n✨ Teste de Prescrição CONCLUÍDO COM SUCESSO! ✨")
            sys.exit(0)
        else:
            print("\n💥 Teste de Prescrição FALHOU! 💥")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro fatal no teste: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
