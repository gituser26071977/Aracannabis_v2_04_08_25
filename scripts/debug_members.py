import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_cors_livre import create_app, db
from association.models import Membro, Associacao
from models import Paciente
import sys
from datetime import datetime

app = create_app()

with app.app_context():
    print("Iniciando teste de membros...")
    try:
        # 1. Obter ou criar Associação
        assoc = Associacao.query.first()
        if not assoc:
            print("Criando associação dummy...")
            assoc = Associacao(nome="Assoc Teste", cnpj="00000000000100", email="teste@assoc.com")
            db.session.add(assoc)
            db.session.commit()
        print(f"Usando Associação ID: {assoc.id}")
        
        # 2. Obter ou criar Paciente
        paciente = Paciente.query.first()
        if not paciente:
            print("Criando paciente dummy...")
            paciente = Paciente(nome="Paciente Teste", cpf="11111111111", data_nascimento=datetime.now())
            db.session.add(paciente)
            db.session.commit()
        print(f"Usando Paciente ID: {paciente.id}")

        # 3. Criar Membro
        print("Criando membro dummy...")
        membro = Membro(
            associacao_id=assoc.id,
            nome="Membro Teste",
            cpf="11111111111",
            paciente_id=paciente.id
        )
        db.session.add(membro)
        # db.session.commit() # Não commitamos para não sujar, ou commitamos e deletamos?
        # Vamos tentar to_dict sem commitar session (objeto está na session)
        
        print("Testando to_dict no membro (sem commit)...")
        try:
            data = membro.to_dict()
            print(f"!! SUCESSO !! Dados: {data}")
        except Exception as e:
            print(f"!! ERRO em to_dict !!: {e}")
            import traceback
            traceback.print_exc()

        # Testar com membro sem paciente
        print("Criando membro SEM paciente...")
        membro_sem_paciente = Membro(
            associacao_id=assoc.id,
            nome="Membro Solitário",
            cpf="22222222222",
            paciente_id=None
        )
        db.session.add(membro_sem_paciente)
        try:
            data = membro_sem_paciente.to_dict()
            print(f"!! SUCESSO (Sem Paciente) !! Dados: {data}")
        except Exception as e:
            print(f"!! ERRO em to_dict (Sem Paciente) !!: {e}")
            import traceback
            traceback.print_exc()
            
        db.session.rollback()
        print("Rollback realizado.")

    except Exception as e:
        print(f"Erro geral: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
