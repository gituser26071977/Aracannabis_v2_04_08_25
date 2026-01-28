from app_cors_livre import create_app
from models import db, Profissional, SenhaTemporaria, Paciente, CompartilhamentoPaciente, ReminderSettings, Assinatura

app = create_app()

with app.app_context():
    print("--- Iniciando limpeza de usuários V2 ---")
    
    # Encontrar admin para backup de pacientes
    admin = Profissional.query.filter_by(usuario='admin').first()
    if not admin:
        # Tenta criar se não existir (fallback) ou busca outro
        print("Admin não encontrado. Buscando substituto...")
        # fallback logic could go here
    
    emails_to_keep = ['abholzwarth@gmail.com']
    usernames_to_keep = ['admin']

    users = Profissional.query.all()
    deleted_count = 0

    for user in users:
        keep = False
        if user.email and user.email.lower() in [e.lower() for e in emails_to_keep]:
            keep = True
        if user.usuario in usernames_to_keep:
            keep = True
            
        if not keep:
            print(f"Processando exclusão: {user.nome} ({user.usuario})")
            
            # 1. Reassign Patients (pois profissional_responsavel_id é nullable=False)
            pacientes = Paciente.query.filter_by(profissional_responsavel_id=user.id).all()
            if pacientes:
                print(f"  - Reatribuindo {len(pacientes)} pacientes para admin (ID {admin.id if admin else 'N/A'})...")
                if not admin:
                    print("ERRO CRÍTICO: Não há admin para assumir pacientes. Pulando exclusão deste usuário.")
                    continue
                for p in pacientes:
                    p.profissional_responsavel_id = admin.id
            
            # 2. Remover dependências estritas
            # Senhas temporárias
            st_count = SenhaTemporaria.query.filter_by(usuario_id=user.id).delete()
            if st_count: print(f"  - Removidos {st_count} senhas temporárias.")

            # Reminder Settings
            rs_count = ReminderSettings.query.filter_by(profissional_id=user.id).delete()
            if rs_count: print(f"  - Removidos {rs_count} configs de lembrete.")

            # Assinaturas
            as_count = Assinatura.query.filter_by(profissional_id=user.id).delete()
            if as_count: print(f"  - Removidas {as_count} assinaturas.")

            # Compartilhamentos (como receptor)
            cp_count = CompartilhamentoPaciente.query.filter_by(profissional_id=user.id).delete()
            if cp_count: print(f"  - Removidos {cp_count} compartilhamentos recebidos.")

            # Flush para garantir que deletes ocorreram
            db.session.flush()

            print(f"❌ Deletando usuário: {user.nome}")
            db.session.delete(user)
            deleted_count += 1
        else:
            print(f"✅ Mantendo: {user.nome}")

    if deleted_count > 0:
        try:
            db.session.commit()
            print(f"\nSucesso: {deleted_count} usuários removidos.")
        except Exception as e:
            db.session.rollback()
            print(f"\nErro ao commitar mudanças: {e}")
    else:
        print("\nNenhum usuário precisou ser removido.")
