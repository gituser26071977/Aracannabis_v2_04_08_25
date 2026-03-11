from app_cors_livre import create_app
from models import db, Profissional
from association.models import Associacao
from models_extra import UsuarioAssociacao
from sqlalchemy import text

def migrate_saas():
    app = create_app()
    with app.app_context():
        print("🔄 Iniciando migração SaaS...")

        # 1. Garantir que as tabelas existem (incluindo a nova UsuarioAssociacao)
        db.create_all()
        print("✅ Tabelas sincronizadas.")

        # 2. Adicionar colunas (RAW SQL para garantir)
        with db.engine.connect() as conn:
            # Associacao: slug
            try:
                # Check if exists
                res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='associacoes' AND column_name='slug'"))
                if not res.fetchone():
                    conn.execute(text("ALTER TABLE associacoes ADD COLUMN slug VARCHAR(255)"))
                    conn.commit()
                    print("✅ Coluna 'slug' adicionada.")
                else:
                    print("ℹ️ Coluna 'slug' já existe.")
            except Exception as e:
                print(f"⚠️ Erro ao verificar/criar slug: {e}")
                try:
                    conn.rollback()
                except: pass

            try:
                # Paciente: associacao_id
                res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='pacientes' AND column_name='associacao_id'"))
                if not res.fetchone():
                    conn.execute(text("ALTER TABLE pacientes ADD COLUMN associacao_id INTEGER REFERENCES associacoes(id)"))
                    conn.commit()
                    print("✅ Coluna 'associacao_id' adicionada.")
                else:
                    print("ℹ️ Coluna 'associacao_id' já existe.")
            except Exception as e:
                print(f"⚠️ Erro ao verificar/criar associacao_id: {e}")
                try:
                    conn.rollback()
                except: pass
                
            # Profissional: associacao_id (just in case model has it, though we use N:N now, model might have backref expectation)
            # Not adding column to Profissional table based on plan (using N:N table), skipping.

        # 3. Criar Associação Default
        default_assoc = Associacao.query.filter_by(cnpj='00.000.000/0001-00').first()
        if not default_assoc:
            default_assoc = Associacao(
                nome="Associação Padrão (Legacy)",
                slug="default",
                cnpj="00.000.000/0001-00",
                endereco="Sistema",
                ativo=True
            )
            db.session.add(default_assoc)
            db.session.commit()
            print(f"✅ Associação Default criada: ID {default_assoc.id}")
        else:
            print(f"ℹ️ Associação Default já existe: ID {default_assoc.id}")
            if not default_assoc.slug:
                default_assoc.slug = "default"
                db.session.commit()

        # 4. Backfill: Vincular Pacientes órfãos à Associação Default
        # Using raw SQL for backfill to avoid model mapping errors if column not detected by ORM yet
        with db.engine.connect() as conn:
            conn.execute(text(f"UPDATE pacientes SET associacao_id = {default_assoc.id} WHERE associacao_id IS NULL"))
            conn.commit()
        print("✅ Pacientes migrados (SQL direto).")

        # 5. Backfill: Vincular Profissionais existentes
        profs = Profissional.query.all()
        for p in profs:
            # Check existing link
            link = UsuarioAssociacao.query.filter_by(
                profissional_id=p.id, 
                associacao_id=default_assoc.id
            ).first()
            
            if not link:
                role = 'admin' if p.role == 'admin' else 'member'
                new_link = UsuarioAssociacao(
                    profissional_id=p.id,
                    associacao_id=default_assoc.id,
                    role=role,
                    status='active'
                )
                db.session.add(new_link)
                # print(f"➕ Profissional {p.nome} vinculado à associação default como {role}.")
        
        db.session.commit()
        print("✅ Profissionais vinculados.")
        print("🏁 Migração SaaS concluída com sucesso!")

if __name__ == '__main__':
    migrate_saas()
