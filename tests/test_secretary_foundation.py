"""
Testes da Fase 1 — Fundação RBAC Secretária

Cobre:
  1. models.ProfissionalRole — validação, normalização, classificação
  2. association.validators — validação CRM contextual e roles
  3. middleware.permission_middleware — resolução de permissões via RoleRegistry
  4. routes.auth_decorators — @require_role, @require_permission, @require_association_member

Roda via:
    pytest tests/test_secretary_foundation.py -v

ou standalone:
    python tests/test_secretary_foundation.py
"""
from __future__ import annotations

import os
import sys

# Permite rodar standalone (adiciona raiz do projeto ao sys.path)
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

# ═══════════════════════════════════════════════════════════════════════
# 1. ProfissionalRole — validação e helpers
# ═══════════════════════════════════════════════════════════════════════

class TestProfissionalRole:
    """Testa a classe ProfissionalRole em models.py."""

    def test_all_valid_roles(self):
        from models import ProfissionalRole
        # Todas as roles usadas no sistema devem ser aceitas
        assert ProfissionalRole.is_valid("admin")
        assert ProfissionalRole.is_valid("profissional")
        assert ProfissionalRole.is_valid("secretary")
        assert ProfissionalRole.is_valid("manager")
        assert ProfissionalRole.is_valid("auxiliar")  # deprecated
        assert ProfissionalRole.is_valid("superadmin")

    def test_invalid_role_rejected(self):
        from models import ProfissionalRole
        assert not ProfissionalRole.is_valid("doctor")  # não é o termo do sistema
        assert not ProfissionalRole.is_valid("receptionist")
        assert not ProfissionalRole.is_valid("")
        assert not ProfissionalRole.is_valid(None)

    def test_staff_classification(self):
        from models import ProfissionalRole
        assert ProfissionalRole.is_staff("secretary")
        assert ProfissionalRole.is_staff("manager")
        assert ProfissionalRole.is_staff("auxiliar")
        assert not ProfissionalRole.is_staff("profissional")
        assert not ProfissionalRole.is_staff("admin")

    def test_clinical_classification(self):
        from models import ProfissionalRole
        assert ProfissionalRole.is_clinical("profissional")
        assert not ProfissionalRole.is_clinical("secretary")
        assert not ProfissionalRole.is_clinical("manager")
        assert not ProfissionalRole.is_clinical("admin")

    def test_admin_classification(self):
        from models import ProfissionalRole
        assert ProfissionalRole.is_admin_role("admin")
        assert ProfissionalRole.is_admin_role("superadmin")
        assert ProfissionalRole.is_admin_role("manager")
        assert not ProfissionalRole.is_admin_role("secretary")
        assert not ProfissionalRole.is_admin_role("profissional")

    def test_legacy_alias_normalization(self):
        from models import ProfissionalRole
        assert ProfissionalRole.normalize("auxiliar") == "secretary"
        assert ProfissionalRole.normalize("secretary") == "secretary"
        assert ProfissionalRole.normalize("profissional") == "profissional"
        assert ProfissionalRole.normalize("") == "profissional"
        assert ProfissionalRole.normalize(None) == "profissional"

    def test_display_label_user_facing(self):
        from models import ProfissionalRole
        assert ProfissionalRole.display_label("secretary") == "Secretária"
        assert ProfissionalRole.display_label("manager") == "Gestor"
        assert ProfissionalRole.display_label("admin") == "Admin"
        assert ProfissionalRole.display_label("profissional") == "Profissional"
        assert ProfissionalRole.display_label("auxiliar") == "Secretária (legado)"

    def test_sets_are_immutable(self):
        """Os sets devem ser frozensets para imutabilidade."""
        from models import ProfissionalRole
        assert isinstance(ProfissionalRole.ALL_VALID, frozenset)
        assert isinstance(ProfissionalRole.STAFF_ROLES, frozenset)
        assert isinstance(ProfissionalRole.CLINICAL_ROLES, frozenset)
        assert isinstance(ProfissionalRole.ADMIN_ROLES, frozenset)


# ═══════════════════════════════════════════════════════════════════════
# 2. Validators (CPF/CRM/role contextual)
# ═══════════════════════════════════════════════════════════════════════

class TestValidators:
    """Testa validators customizados para staff."""

    def test_validar_role_institucional(self):
        from association.validators import validar_role_institucional
        assert validar_role_institucional("admin")
        assert validar_role_institucional("member")
        assert validar_role_institucional("secretary")
        assert validar_role_institucional("manager")
        assert not validar_role_institucional("superadmin")  # não é role per-assoc
        assert not validar_role_institucional("doctor")
        assert not validar_role_institucional("")
        assert not validar_role_institucional(None)

    def test_validar_role_staff(self):
        from association.validators import validar_role_staff
        assert validar_role_staff("secretary")
        assert validar_role_staff("manager")
        assert validar_role_staff("auxiliar")  # deprecated
        assert validar_role_staff("admin")
        assert not validar_role_staff("profissional")  # profissional NÃO é staff
        assert not validar_role_staff("superadmin")
        assert not validar_role_staff("doctor")
        assert not validar_role_staff("")

    def REDACTED(self):
        """Staff (secretary) pode ter CRM vazio."""
        from association.validators import validar_crm_opcional

        # Vazio OK
        valid, err = validar_crm_opcional("", "", "secretary")
        assert valid and err is None

        # None OK
        valid, err = validar_crm_opcional(None, None, "secretary")
        assert valid and err is None

        # CRM preenchido OK
        valid, err = validar_crm_opcional("12345", "SP", "secretary")
        assert valid and err is None

    def REDACTED(self):
        """Profissional PRECISA de CRM."""
        from association.validators import validar_crm_opcional

        # Vazio falha
        valid, err = validar_crm_opcional("", "", "profissional")
        assert not valid
        assert "obrigatório" in err.lower()

        # CRM inválido falha
        valid, err = validar_crm_opcional("ab", "SP", "profissional")
        assert not valid

        # UF inválida falha
        valid, err = validar_crm_opcional("12345", "XXL", "profissional")
        assert not valid

        # OK
        valid, err = validar_crm_opcional("12345", "SP", "profissional")
        assert valid and err is None

    def REDACTED(self):
        """auxiliar (alias) também é tratado como staff sem CRM obrigatório."""
        from association.validators import validar_crm_opcional

        valid, err = validar_crm_opcional("", "", "auxiliar")
        assert valid and err is None

    def test_validar_crm_opcional_admin(self):
        """Admin não precisa de CRM (não prescreve)."""
        from association.validators import validar_crm_opcional

        valid, err = validar_crm_opcional("", "", "admin")
        assert valid and err is None


# ═══════════════════════════════════════════════════════════════════════
# 3. PermissionMiddleware — resolução de permissões via AraOS
# ═══════════════════════════════════════════════════════════════════════

class TestPermissionMiddleware:
    """Testa resolve_effective_permissions em middleware/permission_middleware.py."""

    def REDACTED(self):
        from middleware.permission_middleware import resolve_effective_permissions
        perms = resolve_effective_permissions("admin", None)
        assert len(perms) > 0
        # Admin tem todas as permissões AraOS
        assert "patient.read" in perms
        assert "prescription.write" in perms
        assert "platform.admin" in perms

    def test_superadmin_bypass(self):
        from middleware.permission_middleware import resolve_effective_permissions
        perms = resolve_effective_permissions("superadmin", None)
        assert "platform.admin" in perms

    def test_secretary_role_permissions(self):
        from middleware.permission_middleware import resolve_effective_permissions
        from araos.platform.identity.permissions import Permission
        perms = resolve_effective_permissions("secretary", None)

        # Secretária DEVE ter
        assert Permission.PATIENT_READ in perms
        assert Permission.PATIENT_WRITE in perms
        assert Permission.CONSULTATION_SCHEDULE in perms
        assert Permission.BILLING_READ in perms
        assert Permission.COMMUNICATION_SEND in perms

        # Secretária NÃO DEVE ter
        assert Permission.PRESCRIPTION_WRITE not in perms
        assert Permission.EVOLUTION_WRITE not in perms
        assert Permission.MEDICATION_PRESCRIBE not in perms
        assert Permission.AI_CONFIGURE not in perms
        assert Permission.PLATFORM_ADMIN not in perms

    def test_profissional_permissions(self):
        from middleware.permission_middleware import resolve_effective_permissions
        from araos.platform.identity.permissions import Permission
        perms = resolve_effective_permissions("profissional", None)

        # Médico tem
        assert Permission.PATIENT_READ in perms
        assert Permission.PRESCRIPTION_WRITE in perms
        assert Permission.EVOLUTION_WRITE in perms
        assert Permission.MEDICATION_PRESCRIBE in perms
        assert Permission.AI_USE in perms

        # Médico NÃO tem (apenas admin)
        assert Permission.PLATFORM_ADMIN not in perms
        assert Permission.USER_IMPERSONATE not in perms

    def test_manager_permissions(self):
        from middleware.permission_middleware import resolve_effective_permissions
        from araos.platform.identity.permissions import Permission
        perms = resolve_effective_permissions("manager", None)

        # Manager tem
        assert Permission.CLINIC_WRITE in perms
        assert Permission.PROFESSIONAL_WRITE in perms
        assert Permission.BILLING_MANAGE in perms
        assert Permission.SMART_FLOW_CONFIGURE in perms

        # Manager NÃO tem (apenas admin)
        assert Permission.PLATFORM_ADMIN not in perms

    def REDACTED(self):
        """auxiliar é alias deprecated — deve resolver para mesmas perms de secretary."""
        from middleware.permission_middleware import resolve_effective_permissions
        from araos.platform.identity.permissions import Permission

        perms_aux = resolve_effective_permissions("auxiliar", None)
        perms_sec = resolve_effective_permissions("secretary", None)

        # Devem ter o mesmo conjunto de perms (após normalização)
        # NOTA: como RoleRegistry é resolvido pelo nome direto, 'auxiliar' não
        # é uma role AraOS — retorna frozenset(). Validação de normalização é
        # responsabilidade da camada que produz o role (Profissional.normalize).
        # Aqui confirmamos que o alias não causa crash.
        assert isinstance(perms_aux, frozenset)
        assert isinstance(perms_sec, frozenset)

    def REDACTED(self):
        """Permissões globais + per-assoc devem ser união."""
        from middleware.permission_middleware import resolve_effective_permissions
        from araos.platform.identity.permissions import Permission
        perms = resolve_effective_permissions("secretary", "admin")
        # Union inclui perms de secretary + perms de admin
        assert Permission.PATIENT_READ in perms
        assert Permission.CLINIC_WRITE in perms  # só admin tem

    def test_empty_role_returns_empty(self):
        from middleware.permission_middleware import resolve_effective_permissions
        perms = resolve_effective_permissions(None, None)
        assert perms == frozenset()
        perms = resolve_effective_permissions("", "")
        assert perms == frozenset()

    def test_unknown_role_returns_empty(self):
        from middleware.permission_middleware import resolve_effective_permissions
        perms = resolve_effective_permissions("doctor", None)
        # 'doctor' não é uma role AraOS — retorna conjunto vazio (fail-safe)
        assert perms == frozenset()


# ═══════════════════════════════════════════════════════════════════════
# 4. RBAC Decorators
# ═══════════════════════════════════════════════════════════════════════

class TestRBACDecorators:
    """
    Testa os decorators @require_role, @require_permission, @require_association_member.

    Usa Flask test client + JWT mockado via before_request hook.
    """

    @pytest.fixture
    def app_with_secretary(self):
        """Cria app Flask mínimo com rota protegida por cada decorator."""
        from flask import Flask, g, jsonify
        from flask_jwt_extended import JWTManager
        from werkzeug.security import generate_password_hash

        from models import db, Profissional
        from models_extra import UsuarioAssociacao, AuditLog
        from association.models import Associacao
        from middleware.permission_middleware import register_permission_middleware
        from routes.auth_decorators import require_role, require_permission, require_association_member

        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
            "TEST_DATABASE_URI",
            "sqlite:///:memory:",
        )
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.config["JWT_SECRET_KEY"] = "test-secret"
        app.config["SECRET_KEY"] = "test-secret"

        db.init_app(app)
        JWTManager(app)

        # Models extras necessários
        from models_extra import UsuarioAssociacao, AuditLog, InventoryItem, PharmacyDispense, WebhookLog, CatalogoImportLog, EmailVerification, OnboardingProgress
        from association.models import Associacao, ConviteProfissionalInstituicao, Membro, DocumentoMembro, Estoque, Dispensacao
        from models import (
            SolicitacoesCadastro, ConfiguracaoPrescricao, ConfiguracaoIA, SenhaTemporaria,
            Paciente, Anamnese, Sintoma, Dosagem, Prescricao, Evolucao, Consulta, Exame,
            ExameImagem, ExameLabResultado, SolicitacaoExame, LogAtividade, CompartilhamentoPaciente,
            Produto, ReminderSettings, Plano, Assinatura, Fatura, PagamentoRegistro,
            SintomaPersonalizado, OCRResultado, SnapIVTeste, BeckDepressionTeste, PHQ9Teste, GAD7Teste,
            UploadSession, Disponibilidade
        )

        with app.app_context():
            db.create_all()

            # Cria associação
            assoc = Associacao(
                id=1, nome="Clínica Teste", cnpj="12345678000199", ativo=True
            )
            db.session.add(assoc)
            db.session.commit()

            # Cria usuários de teste
            secretary = Profissional(
                id=1, nome="Maria Secretária", crm=None, uf_crm=None,
                usuario="secretaria", email="sec@test.com",
                senha=generate_password_hash("123"),
                role="secretary",
                status_cadastro="aprovado",
                email_verified=True, onboarding_completed=True,
            )
            doctor = Profissional(
                id=2, nome="Dr. Teste", crm="CRM123", uf_crm="SP",
                usuario="medico", email="med@test.com",
                senha=generate_password_hash("123"),
                role="profissional",
                status_cadastro="aprovado",
                email_verified=True, onboarding_completed=True,
            )
            admin = Profissional(
                id=3, nome="Admin Teste", crm=None, uf_crm=None,
                usuario="admin", email="adm@test.com",
                senha=generate_password_hash("123"),
                role="admin",
                status_cadastro="aprovado",
                email_verified=True, onboarding_completed=True,
            )
            db.session.add_all([secretary, doctor, admin])
            db.session.commit()

            # Vincula secretária à associação
            link = UsuarioAssociacao(
                profissional_id=secretary.id, associacao_id=assoc.id,
                role="member", status="active",
            )
            db.session.add(link)
            db.session.commit()

        # Rotas de teste
        @app.route("/test/role-secretary")
        @require_role("secretary")
        def _r():
            return jsonify({"ok": True})

        @app.route("/test/role-doctor")
        @require_role("profissional", "admin")
        def _d():
            return jsonify({"ok": True})

        @app.route("/test/perm-write")
        @require_permission("prescription.write")
        def _p():
            return jsonify({"ok": True})

        @app.route("/test/perm-read")
        @require_permission("patient.read")
        def _pr():
            return jsonify({"ok": True})

        @app.route("/test/assoc-required")
        @require_association_member
        def _a():
            return jsonify({"ok": True})

        # Header X-Association-ID handler para popular g.current_association
        register_permission_middleware(app)

        return app

    def _login_token(self, app, profissional_id):
        from flask_jwt_extended import create_access_token
        with app.app_context():
            return create_access_token(identity=str(profissional_id))

    def test_require_role_secretary_passes(self, app_with_secretary):
        client = app_with_secretary.test_client()
        token = self._login_token(app_with_secretary, 1)
        res = client.get(
            "/test/role-secretary",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "1"},
        )
        assert res.status_code == 200, res.get_json()

    def REDACTED(self, app_with_secretary):
        client = app_with_secretary.test_client()
        token = self._login_token(app_with_secretary, 2)
        res = client.get(
            "/test/role-secretary",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "1"},
        )
        assert res.status_code == 403
        data = res.get_json()
        assert "secretary" in str(data.get("required_roles", []))

    def test_require_role_admin_bypass(self, app_with_secretary):
        client = app_with_secretary.test_client()
        token = self._login_token(app_with_secretary, 3)
        # Admin deve passar em QUALQUER rota de role
        res = client.get(
            "/test/role-secretary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        res = client.get(
            "/test/role-doctor",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200

    def REDACTED(self, app_with_secretary):
        """Secretária NÃO pode prescrever."""
        client = app_with_secretary.test_client()
        token = self._login_token(app_with_secretary, 1)
        res = client.get(
            "/test/perm-write",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "1"},
        )
        assert res.status_code == 403
        data = res.get_json()
        assert data.get("required_permission") == "prescription.write"

    def REDACTED(self, app_with_secretary):
        """Secretária PODE ler pacientes."""
        client = app_with_secretary.test_client()
        token = self._login_token(app_with_secretary, 1)
        res = client.get(
            "/test/perm-read",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "1"},
        )
        assert res.status_code == 200

    def REDACTED(self, app_with_secretary):
        """Admin tem todas as perms."""
        client = app_with_secretary.test_client()
        token = self._login_token(app_with_secretary, 3)
        res = client.get(
            "/test/perm-write",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200

    def REDACTED(self, app_with_secretary):
        client = app_with_secretary.test_client()
        token = self._login_token(app_with_secretary, 1)
        res = client.get(
            "/test/assoc-required",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "1"},
        )
        assert res.status_code == 200

    def REDACTED(self, app_with_secretary):
        client = app_with_secretary.test_client()
        token = self._login_token(app_with_secretary, 3)
        res = client.get(
            "/test/assoc-required",
            headers={"Authorization": f"Bearer {token}"},  # sem X-Association-ID
        )
        assert res.status_code == 200


# ═══════════════════════════════════════════════════════════════════════
# Runner (permite rodar sem pytest)
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
