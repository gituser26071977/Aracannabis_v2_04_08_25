"""
MISSÃO 18 — P0 Remediation Tests

Testes automatizados para validar que os 12 P0 da auditoria foram
de fato corrigidos. Estes testes são read-only (não tocam em produção).

Cobrem:
  - P0-01: Path Traversal em hc_report (secure_filename + UUID)
  - P0-02: Servir exame com @jwt_required + tenant validation
  - P0-03: PII/senha NÃO aparece em logs de auth
  - P0-04: sanitize_input NUNCA toca em senhas
  - P0-05: CSP sem 'unsafe-inline' / 'unsafe-eval' em script-src
  - P0-06: CSRF token nunca None + compare_digest
  - P0-07: MAX_CONTENT_LENGTH vem só de config.py
  - P0-08: tenant_lib bloqueia INSERT/UPDATE sem tenant
  - P0-09: skip_tenant=True documentado ou validado
  - P0-10: detecção produção via ENVIRONMENT (não FLASK_ENV)
  - P0-11: webhook compare_digest em TODAS comparações
  - P0-12: tenant vem SÓ do JWT (X-Association-ID ignorado)

Execução:
    pytest tests/security/test_p0_remediation_m18.py -v
"""

import os
import re
import ast
import hmac as hmac_lib
import inspect

import pytest


# ════════════════════════════════════════════════════════════════
# P0-01: Path Traversal em hc_report
# ════════════════════════════════════════════════════════════════
class TestP01_PathTraversalHCReport:
    """Garante que hc_report.py NÃO aceita filenames arbitrários."""

    def REDACTED(self):
        from routes.hc_report import _validate_filename
        # Válido
        assert _validate_filename("a" * 32 + "_laudo.pdf")
        # Inválidos — vetores de ataque
        assert not _validate_filename("../../../etc/passwd")
        assert not _validate_filename("..\\..\\windows\\system32")
        assert not _validate_filename("/etc/passwd")
        assert not _validate_filename("C:\\Windows\\System32\\config\\SAM")
        assert not _validate_filename("foo.pdf")  # sem UUID
        assert not _validate_filename("")
        assert not _validate_filename(None)
        assert not _validate_filename("aaaaaa<script>alert(1)</script>_laudo.pdf")
        # Path traversal via filename '..' interno
        assert not _validate_filename("REDACTED..pdf")

    def test_hc_report_route_uses_realpath(self):
        """Garante que o download usa realpath + startswith para bloquear symlink."""
        with open("routes/hc_report.py", "r") as f:
            src = f.read()
        assert "realpath" in src
        assert "startswith" in src
        assert "send_file" in src

    def REDACTED(self):
        with open("routes/hc_report.py", "r") as f:
            src = f.read()
        assert "@jwt_required()" in src


# ════════════════════════════════════════════════════════════════
# P0-02: Servir exame com @jwt_required + tenant
# ════════════════════════════════════════════════════════════════
class TestP02_ExamFileServing:
    """Garante que /exames/arquivos/ exige auth + tenant."""

    def test_exames_filename_validation(self):
        from routes.exames import _validate_exame_filename
        assert _validate_exame_filename("a" * 32 + "_exame.pdf")
        assert not _validate_exame_filename("../etc/passwd")
        assert not _validate_exame_filename("")
        assert not _validate_exame_filename(None)

    def test_exames_servir_requires_jwt(self):
        with open("routes/exames.py", "r") as f:
            src = f.read()
        # Bloco servir_arquivo_exame tem @jwt_required
        assert "@jwt_required()\ndef servir_arquivo_exame" in src or \
               "@jwt_required()\n    def servir_arquivo_exame" in src, \
               "servir_arquivo_exame sem @jwt_required"
        # Bloco antigo (sem @jwt_required) removido
        # O bloco original era: 'def servir_arquivo_exame(filename):' sem decorator
        # Verificamos que a definição está sempre precedida por @jwt_required()
        match = re.search(r"def\s+servir_arquivo_exame", src)
        if match:
            pre = src[max(0, match.start() - 200):match.start()]
            assert "@jwt_required()" in pre, \
                "servir_arquivo_exame sem decorator @jwt_required"


# ════════════════════════════════════════════════════════════════
# P0-03: PII/senha NÃO aparece em logs de auth
# ════════════════════════════════════════════════════════════════
class TestP03_NoPIIInLogs:
    """Garante que routes/auth.py não loga senha nem identifier."""

    def test_login_has_no_print_of_senha(self):
        with open("routes/auth.py", "r") as f:
            src = f.read()
        # Nenhum print() em produção que mencione senha
        # (todos os prints de DEBUG LOGIN foram removidos)
        assert 'print(f"DEBUG LOGIN' not in src
        assert 'print("DEBUG LOGIN' not in src
        # logger.info não recebe senha nem identifier
        assert 'logger.info(f"LOGIN ATTEMPT - Identificador' not in src
        assert 'Senha length' not in src or 'senha' not in src.split('def login')[1].split('def get_profile')[0].lower().split('print')[0] if 'print' in src else True

    def test_login_route_source_compiles(self):
        """Garante que routes/auth.py compila via AST (sem importar — limiter é None no test)."""
        with open("routes/auth.py", "r") as f:
            src = f.read()
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            pytest.fail(f"routes/auth.py não compila: {e}")
        # Verifica que 'def login(' está presente
        assert any(
            isinstance(node, ast.FunctionDef) and node.name == "login"
            for node in ast.walk(tree)
        ), "def login não encontrada"


# ════════════════════════════════════════════════════════════════
# P0-04: sanitize_input NUNCA toca em senhas
# ════════════════════════════════════════════════════════════════
class TestP04_SanitizeSkipsPasswords:
    """Garante que sanitize_input preserva senhas intactas."""

    def test_sanitize_str_removes_specials(self):
        from security_config import sanitize_input
        # Em campos NÃO-senha, sanitiza
        assert sanitize_input("<script>alert(1)</script>") == "scriptalert(1)/script"
        assert sanitize_input("hello'world\";") == "helloworld"

    def test_sanitize_dict_skips_passwords(self):
        from security_config import sanitize_input
        data = {
            "nome": "<script>",
            "email": "foo@bar.com",
            "senha": "S3nh@<f'orte>",
            "password": "pass<>",
            "confirm_password": "abc\";",
            "new_password": "x'y",
        }
        result = sanitize_input(data)
        # Senhas preservadas
        assert result["senha"] == "S3nh@<f'orte>"
        assert result["password"] == "pass<>"
        assert result["confirm_password"] == "abc\";"
        assert result["new_password"] == "x'y"
        # Campos não-senha sanitizados
        assert result["nome"] == "script"
        assert result["email"] == "foo@bar.com"

    def REDACTED(self):
        from security_config import sanitize_input
        data = {
            "user": {
                "senha": "Top<>Secret",
                "profile": {"name": "<b>x</b>"},
            }
        }
        result = sanitize_input(data)
        assert result["user"]["senha"] == "Top<>Secret"
        assert result["user"]["profile"]["name"] == "bx/b"


# ════════════════════════════════════════════════════════════════
# P0-05: CSP sem unsafe-inline/eval
# ════════════════════════════════════════════════════════════════
class TestP05_CSPHardening:
    """Garante que CSP removeu unsafe-inline/unsafe-eval de script-src."""

    def REDACTED(self):
        from security_config import SECURITY_HEADERS
        csp_value = SECURITY_HEADERS.get("Content-Security-Policy", "")
        # Pode haver CSP dinâmico; checamos a função
        if csp_value:
            assert "'unsafe-inline'" not in csp_value or "nonce-" in csp_value, \
                f"CSP tem unsafe-inline mas sem nonce: {csp_value}"
            assert "'unsafe-eval'" not in csp_value

    def REDACTED(self):
        """Garante que add_security_headers gera CSP sem unsafe-inline/eval."""
        from security_config import add_security_headers
        from flask import Flask
        app = Flask(__name__)
        with app.test_request_context("/"):
            resp = app.make_response(("OK", 200))
            add_security_headers(resp)
            csp = resp.headers.get("Content-Security-Policy", "")
            assert "unsafe-inline" not in csp or "nonce-" in csp, \
                f"CSP tem unsafe-inline sem nonce: {csp}"
            assert "unsafe-eval" not in csp, f"CSP tem unsafe-eval: {csp}"
            # Nonce presente
            assert "nonce-" in csp

    def test_csp_has_object_src_none(self):
        from security_config import add_security_headers
        from flask import Flask
        app = Flask(__name__)
        with app.test_request_context("/"):
            resp = app.make_response(("OK", 200))
            add_security_headers(resp)
            csp = resp.headers.get("Content-Security-Policy", "")
            assert "object-src 'none'" in csp


# ════════════════════════════════════════════════════════════════
# P0-06: CSRF token nunca None + compare_digest
# ════════════════════════════════════════════════════════════════
class TestP06_CSRFHardening:
    """Garante CSRF token obrigatório + compare_digest."""

    def REDACTED(self):
        from security_config import csrf_protect
        from flask import Flask
        app = Flask(__name__)
        app.config["CSRF_TOKEN"] = None  # ausente
        @csrf_protect
        def dummy():
            return "ok"
        with app.test_request_context("/p", method="POST"):
            result = dummy()
            # Quando CSRF_TOKEN=None, deve retornar 503 (fail closed)
            assert result[1] == 503, f"Esperava 503 fail-closed, recebi {result[1]}"

    def REDACTED(self):
        with open("security_config.py", "r") as f:
            src = f.read()
        # csrf_protect usa compare_digest
        m = re.search(r"def\s+csrf_protect.*?return\s+decorated_function", src, re.DOTALL)
        assert m, "csrf_protect não encontrada"
        body = m.group(0)
        assert "compare_digest" in body, \
            "csrf_protect não usa compare_digest"

    def REDACTED(self):
        """Se em prod o token for fraco/ausente, RuntimeError."""
        os.environ["ENVIRONMENT"] = "production"
        try:
            from security_config import _ensure_csrf_token
            from flask import Flask
            app = Flask(__name__)
            app.config["CSRF_TOKEN"] = ""
            with pytest.raises(RuntimeError):
                _ensure_csrf_token(app)
        finally:
            os.environ.pop("ENVIRONMENT", None)


# ════════════════════════════════════════════════════════════════
# P0-07: MAX_CONTENT_LENGTH uma única fonte
# ════════════════════════════════════════════════════════════════
class TestP07_MaxContentLength:
    """Garante que app_cors_livre NÃO redefine MAX_CONTENT_LENGTH."""

    def REDACTED(self):
        with open("app_cors_livre.py", "r") as f:
            src = f.read()
        # Se setar, deve ser condicional (if not in app.config)
        if 'app.config["MAX_CONTENT_LENGTH"]' in src:
            assert 'if "MAX_CONTENT_LENGTH" not in app.config' in src or \
                   'MAX_CONTENT_LENGTH" not in' in src, \
                   "MAX_CONTENT_LENGTH setado sem fallback condicional"

    def REDACTED(self):
        from config import Config
        assert Config.MAX_CONTENT_LENGTH > 0
        assert Config.MAX_CONTENT_LENGTH <= 100 * 1024 * 1024  # ≤100MB


# ════════════════════════════════════════════════════════════════
# P0-08: tenant_lib bloqueia INSERT/UPDATE/DELETE sem tenant
# ════════════════════════════════════════════════════════════════
class TestP08_TenantLibWrites:
    """Garante que tenant_lib tem listener before_flush."""

    def REDACTED(self):
        with open("tenant_lib.py", "r") as f:
            src = f.read()
        assert "before_flush" in src, "tenant_lib sem before_flush listener"
        assert "IntegrityError" in src, "tenant_lib não aborta INSERT cross-tenant"

    def REDACTED(self):
        with open("tenant_lib.py", "r") as f:
            src = f.read()
        assert "_validate_tenant_on_write" in src


# ════════════════════════════════════════════════════════════════
# P0-09: skip_tenant=True documentado ou validado
# ════════════════════════════════════════════════════════════════
class TestP09_SkipTenantDocumented:
    """skip_tenant=True com user input deve ter validação prévia."""

    def REDACTED(self):
        with open("routes/ai_chat_simples.py", "r") as f:
            src = f.read()
        # buscar_contexto_paciente agora recebe profissional_id e valida acesso
        assert "verificar_acesso_paciente" in src
        assert "def buscar_contexto_paciente(paciente_id, profissional_id)" in src

    def REDACTED(self):
        with open("routes/pacientes.py", "r") as f:
            src = f.read()
        # obter_pacientes_acessiveis tem docstring P0-09
        assert "P0-09" in src
        assert "JUSTIFICADO" in src or "justificativa" in src.lower()


# ════════════════════════════════════════════════════════════════
# P0-10: ENVIRONMENT unificado
# ════════════════════════════════════════════════════════════════
class TestP10_EnvironmentUnified:
    """Detecção de produção via ENVIRONMENT (não FLASK_ENV)."""

    def REDACTED(self):
        from config import is_production, _is_production
        assert callable(is_production)

    def test_is_production_returns_bool(self):
        os.environ["ENVIRONMENT"] = "production"
        try:
            from config import is_production
            assert is_production() is True
        finally:
            os.environ.pop("ENVIRONMENT", None)

        os.environ["ENVIRONMENT"] = "development"
        try:
            from config import is_production
            assert is_production() is False
        finally:
            os.environ.pop("ENVIRONMENT", None)

    def REDACTED(self):
        """security_config.py não deve ler FLASK_ENV diretamente."""
        with open("security_config.py", "r") as f:
            src = f.read()
        # Comentário sobre FLASK_ENV é OK; uso direto em código não
        # Buscar padrões de leitura direta
        assert 'os.getenv("FLASK_ENV"' not in src or "compat" in src.lower(), \
            "security_config.py ainda lê FLASK_ENV diretamente"


# ════════════════════════════════════════════════════════════════
# P0-11: webhook compare_digest em TODAS comparações
# ════════════════════════════════════════════════════════════════
class TestP11_WebhookCompareDigest:
    """Garante que webhooks usam compare_digest (constant-time)."""

    def REDACTED(self):
        from middleware.webhook_auth import _safe_compare
        assert _safe_compare("abc", "abc") is True
        assert _safe_compare("abc", "xyz") is False
        assert _safe_compare(None, "abc") is False
        assert _safe_compare("abc", None) is False

    def REDACTED(self):
        """Nenhum 'if provided_secret != webhook_secret'."""
        with open("middleware/webhook_auth.py", "r") as f:
            src = f.read()
        assert "if provided_secret != webhook_secret" not in src, \
            "webhook ainda usa comparação não-constant-time"

    def REDACTED(self):
        from middleware.webhook_auth import verify_webhook_signature
        # Payload qualquer com assinatura vazia → False
        assert verify_webhook_signature({"foo": "bar"}, "", "secret") is False
        # Assinatura absurda → False (proteção DoS)
        assert verify_webhook_signature({"foo": "bar"}, "x" * 10000, "secret") is False


# ════════════════════════════════════════════════════════════════
# P0-12: Tenant vem SÓ do JWT (X-Association-ID removido)
# ════════════════════════════════════════════════════════════════
class TestP12_TenantFromJWTOnly:
    """X-Association-ID não pode spoof tenant."""

    def REDACTED(self):
        with open("middleware/tenant_middleware.py", "r") as f:
            src = f.read()
        # Procura pelo uso REAL (não comentário)
        # Comentários têm ' # ' antes. Uso real está em código: request.headers.get(...)
        for line in src.split("\n"):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            assert "X-Association-ID" not in line, \
                f"tenant_middleware ainda lê X-Association-ID em código: {line!r}"

    def REDACTED(self):
        with open("app_cors_livre.py", "r") as f:
            src = f.read()
        # X-Association-ID removido de allow_headers
        assert '"X-Association-ID"' not in src
        assert "'X-Association-ID'" not in src


# ════════════════════════════════════════════════════════════════
# Sanity: a aplicação inteira compila
# ════════════════════════════════════════════════════════════════
class TestAppCompiles:
    def test_all_modified_files_parse(self):
        files = [
            "config.py",
            "security_config.py",
            "tenant_lib.py",
            "routes/hc_report.py",
            "routes/exames.py",
            "routes/auth.py",
            "routes/ai_chat_simples.py",
            "routes/pacientes.py",
            "middleware/tenant_middleware.py",
            "middleware/webhook_auth.py",
            "app_cors_livre.py",
        ]
        for path in files:
            with open(path, "r") as f:
                src = f.read()
            try:
                ast.parse(src)
            except SyntaxError as e:
                pytest.fail(f"{path} não compila: {e}")
