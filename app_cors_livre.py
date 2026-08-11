import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, redirect, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from models import db
from config import get_config, is_production
from security_config import ALLOWED_ORIGINS, init_limiter, add_security_headers
from tenant_lib import configure_tenant_filters
from services.webhook_auth import assert_required_secrets_on_startup
import secrets


def create_app(config_obj=None):
    app = Flask(__name__)

    # Carregar configurações
    if config_obj:
        app.config.from_object(config_obj)
    else:
        current_config = get_config()
        app.config.from_object(current_config)

    # Configurar chave secreta para sessões
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))

    # P0-A FASE 4: abortar startup em producao se secrets de webhook faltarem
    is_prod = is_production()
    assert_required_secrets_on_startup(
        env_vars=[
            "MERCADOPAGO_WEBHOOK_SECRET",
            "MERCADOPAGO_MODULOS_WEBHOOK_SECRET",
            "DR_ANDERSON_WEBHOOK_SECRET",
            "INTERNAL_SERVICE_KEY",
        ],
        is_production=is_prod,
    )

    # Configurar token CSRF
    # P0-06 (Missão 18): gerar placeholder, mas garantir via _ensure_csrf_token
    app.config["CSRF_TOKEN"] = secrets.token_hex(32)
    try:
        from security_config import _ensure_csrf_token
        _ensure_csrf_token(app)
    except RuntimeError as exc:
        # Em produção ABORTA startup se CSRF_TOKEN ausente
        if is_prod:
            raise
        # Em dev apenas loga warning
        print(f"[WARN] CSRF token: {exc}")

    # Configurações de upload de arquivos
    # P0-07 (Missão 18): MAX_CONTENT_LENGTH vem EXCLUSIVAMENTE de config.py
    # (fonte única de verdade). Nunca redefinir aqui.
    if "MAX_CONTENT_LENGTH" not in app.config:
        app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # fallback 16MB
    app.config["UPLOAD_FOLDER_EXAMES"] = os.path.join(os.getcwd(), "uploads", "exames")
    app.config["ALLOWED_EXTENSIONS"] = {
        "txt",
        "pdf",
        "png",
        "jpg",
        "jpeg",
        "gif",
        "doc",
        "docx",
    }

    # Configurações adicionais para upload
    app.config["MAX_CONTENT_PATH"] = None
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    # Inicializar extensões
    db.init_app(app)
    configure_tenant_filters(db)  # Ativar isolamento multi-tenant
    jwt = JWTManager(app)
    migrate = Migrate()
    migrate.init_app(app, db)

    # Sprint S1 — EPIC 1: inicializar provider de identidade AraOS
    # (unificação do JWT; coexiste com flask_jwt_extended durante a migração
    # gradual das rotas legadas — S2/S3 removerão flask_jwt_extended das rotas)
    from services.araos_auth import init_araos_auth
    init_araos_auth(app)

    # Inicializar rate limiter
    limiter = init_limiter(app)

    # CORS amplo para front (localhost:3000) e acessos externos; se quiser restringir, ajuste ALLOWED_ORIGINS em security_config
    CORS(
        app,
        origins=ALLOWED_ORIGINS,
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-CSRF-Token",
            "X-Requested-With",
        ],
        expose_headers=[
            "Content-Type",
            "Authorization",
            "X-CSRF-Token",
        ],
        supports_credentials=True,
        max_age=600,  # cache curto: mudanças de CORS propagam rápido
    )

    # Handler para arquivos muito grandes
    @app.errorhandler(413)
    def too_large(e):
        return jsonify(
            {
                "error": "Arquivo muito grande",
                "message": "O arquivo enviado excede o limite de 50MB",
                "max_size": "50MB",
                "status": 413,
            }
        ), 413

    # Rota para obter token CSRF
    @app.route("/api/csrf-token", methods=["GET"])
    def get_csrf_token():
        return jsonify({"csrf_token": app.config["CSRF_TOKEN"]})

    # Rota raiz da API
    @app.route("/")
    def root():
        return redirect("/api/status", code=302)

    @app.route("/api")
    def api_root():
        return jsonify(
            {
                "name": "AraOS API",
                "version": "1.0.0",
                "status": "online",
                "endpoints": {
                    "auth": "/api/auth",
                    "patients": "/api/pacientes",
                    "symptoms": "/api/sintomas",
                    "dosages": "/api/dosagens",
                    "evolutions": "/api/evolucoes",
                    "exams": "/api/exames",
                    "products": "/api/produtos",
                    "status": "/api/status",
                },
                "documentation": "http://localhost:5002/api/status",
            }
        )

    # Rota de status da API
    @app.route("/api/status")
    def status():
        return jsonify(
            {
                "status": "online",
                "message": "AraOS API operacional",
                "cors": "Configurado com origens permitidas",
                "security": "CSRF e rate limiting habilitados",
                "documentation": "Swagger UI available at /api/swagger",
            }
        )

    # Rota de healthcheck (MISSÃO 20 — FASE 3 monitoramento)
    # Verifica dependências: DB, Redis, Secrets obrigatórios.
    # Retorna 200 quando tudo OK; 503 quando algo está down.
    @app.route("/api/health")
    def health():
        checks = {}
        overall_ok = True

        # 1. PostgreSQL
        try:
            db.session.execute(db.text("SELECT 1"))
            checks["postgres"] = "ok"
        except Exception as exc:
            checks["postgres"] = f"fail: {type(exc).__name__}"
            overall_ok = False

        # 2. Redis (via flask-limiter storage se configurado)
        try:
            import redis as _redis
            from config import get_config
            cfg = get_config()
            redis_url = getattr(cfg, "REDIS_URL", None) or "redis://localhost:6379/0"
            r = _redis.Redis.from_url(redis_url, socket_connect_timeout=2)
            r.ping()
            checks["redis"] = "ok"
        except Exception as exc:
            checks["redis"] = f"fail: {type(exc).__name__}"
            overall_ok = False

        # 3. Secrets obrigatórios (não revela valores)
        import os as _os
        for secret in ("JWT_SECRET_KEY", "SECRET_KEY", "CSRF_TOKEN"):
            v = _os.environ.get(secret) or app.config.get(secret)
            if not v or len(str(v)) < 32:
                checks[f"secret:{secret}"] = "fail: ausente ou <32 chars"
                overall_ok = False
            else:
                checks[f"secret:{secret}"] = "ok"

        # 4. Disk space (mínimo 1GB livre)
        try:
            import shutil
            free_gb = shutil.disk_usage("/").free / (1024**3)
            checks["disk_free_gb"] = round(free_gb, 2)
            if free_gb < 1.0:
                overall_ok = False
        except Exception:
            pass

        body = {
            "status": "ok" if overall_ok else "degraded",
            "checks": checks,
            "timestamp": _os.environ.get("_TS", "") or "",
        }
        # Não cachear health
        resp = jsonify(body)
        resp.headers["Cache-Control"] = "no-store"
        return resp, (200 if overall_ok else 503)

    # Rota de schema/version (MISSAO 28 — FASE 4)
    # Retorna informacoes de migrations + schema para observabilidade pos-deploy.
    # Apenas leitura. NAO autentica (uso operacional).
    @app.route("/api/schema-version", methods=["GET"])
    def schema_version():
        from services.deploy_guard import get_schema_version
        try:
            info = get_schema_version(db)
            # status 200 sempre — frontend decide se esta saudavel
            return jsonify(info), 200
        except Exception as exc:
            return jsonify({
                "error": "schema_version_unavailable",
                "detail": str(exc),
            }), 503

    # Registrar blueprints
    from routes.auth import auth_bp, profissionais_bp
    from routes.pacientes import pacientes_bp
    from routes.sintomas import sintomas_bp
    from routes.dosagens import dosagens_bp
    from routes.evolucoes import evolucoes_bp
    from routes.lgpd import lgpd_bp
    from routes.consultas import consultas_bp
    from routes.import_export import import_export_bp
    from routes.produtos import produtos_bp
    from routes.catalogo_routes import catalogo_bp
    from routes.voice import voice_bp
    from routes.cadastro_profissionais import (
        cadastro_profissionais_bp as cadastro_prof_bp,
    )
    from routes.exames import exames_bp
    from routes.anuncios import anuncios_bp
    from routes.snap_iv import snap_iv_bp
    from routes.beck_depression import beck_depression_bp
    from routes.phq9 import phq9_bp
    from routes.ai_config import ai_config_bp
    from routes.admin import admin_bp
    from routes.ai_management import ai_management_bp
    from routes.crew_ai import crew_ai_bp
    from routes.billing import billing_bp
    from routes.webhooks import webhooks_bp
    from routes.ai_chat_simples import ai_chat_simples_bp
    from routes.gad7 import gad7_bp
    from routes.dynamic_tenant_webhook import tenant_webhook_bp
    from routes.config_ia_tenant import config_ia_tenant_bp
    from routes.sdr import sdr_bp
    from routes.anamneses import anamneses_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(profissionais_bp, url_prefix="/api")
    app.register_blueprint(exames_bp)
    app.register_blueprint(pacientes_bp, url_prefix="/api/pacientes")
    app.register_blueprint(sintomas_bp, url_prefix="/api/sintomas")
    app.register_blueprint(dosagens_bp, url_prefix="/api/dosagens")
    app.register_blueprint(evolucoes_bp, url_prefix="/api/evolucoes")
    app.register_blueprint(lgpd_bp, url_prefix="/api/lgpd")
    app.register_blueprint(consultas_bp, url_prefix="/api/consultas")
    app.register_blueprint(import_export_bp, url_prefix="/api/import-export")
    app.register_blueprint(produtos_bp, url_prefix="/api")
    app.register_blueprint(catalogo_bp)
    app.register_blueprint(voice_bp)
    app.register_blueprint(tenant_webhook_bp, url_prefix="/api/tenant")
    app.register_blueprint(config_ia_tenant_bp, url_prefix="/api/tenant-config")
    app.register_blueprint(sdr_bp, url_prefix="/api/sdr")
    app.register_blueprint(anamneses_bp)
    app.register_blueprint(cadastro_prof_bp, url_prefix="/api/cadastro_profissionais")
    app.register_blueprint(anuncios_bp, url_prefix="/api")

    # Week 11D — Cannabis Module API
    from routes.cannabis import cannabis_bp
    app.register_blueprint(cannabis_bp, url_prefix="/api/cannabis")

    # Week 11D — Digital Twin API
    from routes.twin import twin_bp
    app.register_blueprint(twin_bp, url_prefix="/api/twin")

    # Week 11D — Follow-up Engine API
    from routes.followup import followup_bp
    app.register_blueprint(followup_bp, url_prefix="/api/followup")
    app.register_blueprint(snap_iv_bp, url_prefix="/api/snap-iv")
    app.register_blueprint(beck_depression_bp, url_prefix="/api/beck-depression")
    app.register_blueprint(phq9_bp, url_prefix="/api/phq9")
    app.register_blueprint(gad7_bp, url_prefix="/api/gad7")
    from routes.prescricoes import prescricoes_bp

    app.register_blueprint(prescricoes_bp, url_prefix="/api/prescricoes")
    from routes.prescricao_config import prescricao_config_bp

    app.register_blueprint(prescricao_config_bp, url_prefix="/api/prescricao-config")
    from routes.mercadopago import mercadopago_bp

    app.register_blueprint(mercadopago_bp, url_prefix="/api/mercadopago")
    from routes.dashboard import dashboard_bp

    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    from routes.planos import planos_bp

    app.register_blueprint(planos_bp, url_prefix="/api/planos")
    app.register_blueprint(ai_config_bp, url_prefix="/api/ai-config")
    from routes.mobile_upload import mobile_upload_bp

    app.register_blueprint(mobile_upload_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(ai_management_bp, url_prefix="/api/ai-management")
    app.register_blueprint(crew_ai_bp, url_prefix="/api/crew-ai")
    app.register_blueprint(billing_bp, url_prefix="/api/billing")
    from routes.faturamento import faturamento_bp

    app.register_blueprint(faturamento_bp, url_prefix="/api/faturamento")
    from routes.intake_integration import intake_integration_bp

    app.register_blueprint(intake_integration_bp, url_prefix="/api")
    from routes.onboarding_pacientes import onboarding_bp

    app.register_blueprint(onboarding_bp, url_prefix="/api/onboarding")
    from routes.certificacao_digital import certificacao_bp

    app.register_blueprint(certificacao_bp, url_prefix="/api")
    app.register_blueprint(webhooks_bp, url_prefix="/api/webhooks")
    app.register_blueprint(ai_chat_simples_bp, url_prefix="/api")
    from routes.utils import utils_bp

    app.register_blueprint(utils_bp, url_prefix="/api/utils")

    # Onboarding & Email Verification Module
    from routes.onboarding import onboarding_bp
    app.register_blueprint(onboarding_bp)

    from routes.patient_import_agent import patient_import_bp

    app.register_blueprint(patient_import_bp, url_prefix="/api/import-agent")

    # [NEW] Usage / Quotas (Squad B)
    from routes.usage import usage_bp

    app.register_blueprint(usage_bp, url_prefix="/api")

    # [NEW] AAP — Arapath Agent Protocol
    from routes.aap import aap_bp
    app.register_blueprint(aap_bp)

    # [NEW] Virtual Secretary Dr. Anderson
    from routes.dr_anderson_webhook import dr_anderson_bp

    app.register_blueprint(dr_anderson_bp, url_prefix="/api/dr-anderson")

    # [NEW] Visual Smart Flow Integration
    from routes.vsf_integration import vsf_bp

    app.register_blueprint(vsf_bp, url_prefix="/api/vsf")

    # Patient Portal (NEW)
    from routes.patient_auth import patient_auth_bp
    from routes.patient_portal import patient_portal_bp

    app.register_blueprint(patient_auth_bp, url_prefix="/api/patient-auth")
    app.register_blueprint(patient_portal_bp, url_prefix="/api/patient-portal")

    # Association Management Module
    from association.routes import association_bp

    app.register_blueprint(association_bp, url_prefix="/api/association")

    # [NEW] Intelligent Import (multi-tenant staff + schedule import)
    from routes.intelligent_import import intelligent_import_bp

    app.register_blueprint(intelligent_import_bp, url_prefix="/api")

    # [NEW] Ara Intake → AraOS (Clinical Events Fase 0)
    from routes.clinical_intake import clinical_intake_bp

    app.register_blueprint(clinical_intake_bp)

    # [NEW] Clinical Genome — leitura da projeção (Fase 0)
    from routes.clinical_genome import clinical_genome_bp

    app.register_blueprint(clinical_genome_bp)

    # [NEW] Replay histórico — bootstrap do genome (F2 retrofit)
    from routes.historical_replay import replay_bp

    app.register_blueprint(replay_bp)

    # [NEW] AI Clinical Pipeline
    from routes.ai_clinical import ai_clinical_bp
    from routes.hc_report import hc_report_bp

    app.register_blueprint(ai_clinical_bp, url_prefix="/api/ai-clinical")
    app.register_blueprint(hc_report_bp, url_prefix="/api/hc-report")

    # [NEW] Módulos de Especialidade (Fase 4 pre-deploy)
    from routes.modulos import modulos_bp, meus_modulos_bp
    app.register_blueprint(modulos_bp)
    app.register_blueprint(meus_modulos_bp)

    # [NEW] AraOS Neurodevelopmental Registry (Sprint 3.2 / ADR-0002)
    from routes.neuro_registry import neuro_registry_bp
    app.register_blueprint(neuro_registry_bp)

    # [NEW] AraOS Clinical Intelligence Platform (Sprint 4.1 / ADR-0003)
    from routes.intelligence_timeline import intelligence_timeline_bp
    from routes.explainability import explainability_bp
    app.register_blueprint(intelligence_timeline_bp)
    app.register_blueprint(explainability_bp)

    # [NEW] AraOS Clinical Context Engine (Sprint 4.2 / ADR-0003)
    from routes.clinical_context import clinical_context_bp
    app.register_blueprint(clinical_context_bp)

    # [NEW] AraOS Clinical Knowledge Engine — Knowledge REST API (RC1 Gate 2 / Sprint 4.5 §W3)
    # Translation layer only. Foundation-Freeze compliant (no domain mutation).
    from interfaces.rest.v1 import knowledge_bp as knowledge_v1_bp
    from interfaces.rest.v1.observability import register_request_hooks as _register_knowledge_hooks
    app.register_blueprint(knowledge_v1_bp)
    # Configure Knowledge persistence session factory (re-uses Flask-SQLAlchemy session).
    app.config.setdefault(
        "REDACTED",
        lambda: db.session,
    )
    # Install request/correlation_id/latency hooks scoped to /api/v1/knowledge.
    _register_knowledge_hooks(app)

    # [NEW] Tenant Middleware
    from middleware.tenant_middleware import register_tenant_middleware

    register_tenant_middleware(app)

    # [NEW] Subscription Middleware (Squad B)
    from middleware.subscription_middleware import register_subscription_middleware

    register_subscription_middleware(app)

    # Criar headers de segurança
    @app.after_request
    def apply_security_headers(response):
        return add_security_headers(response)

    # Controle de acesso por perfil (Assistencial × Administrativo × Solo).
    # Aplica-se a usuários autenticados em rotas classificadas por área.
    @app.before_request
    def enforce_perfil_acesso():
        if request.method == "OPTIONS":
            return None
        from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

        try:
            verify_jwt_in_request(optional=True)
        except Exception:  # noqa: BLE001 — token inválido: deixa a rota retornar 401
            return None
        identity = get_jwt_identity()
        if identity is None:
            return None  # anônimo: deixa o @jwt_required da rota tratar
        from models import Profissional
        from services.perfil_acesso import verificar_acesso

        profissional = Profissional.query.get(int(identity)) if str(identity).isdigit() else None
        if profissional is None:
            return jsonify({"error": "Perfil não encontrado"}), 404
        if not verificar_acesso(profissional, request.path):
            return (
                jsonify(
                    {
                        "error": "Acesso negado",
                        "message": "Seu perfil não tem acesso a esta área.",
                    }
                ),
                403,
            )
        return None

    # Inicializar banco de dados e diretórios
    with app.app_context():
        # 1. Criar tabelas primeiro
        try:
            # Importar models_extra para garantir que todas as tabelas sejam criadas
            import models_extra
            # Importar modelos de Módulos de Especialidade (Fase 4 pre-deploy)
            import models_modulos  # noqa: F401
            from services.voice.models.voice_models import (
                VoiceSessionModel, VoiceTranscriptModel,
                VoiceEntityModel, VoiceActionModel, VoiceAuditLogModel
            )
            db.create_all()
        except Exception as e:
            print(f"⚠️ Aviso: Erro ao criar tabelas: {e}")

        # 2. Inicializar anúncios (precisa das tabelas)
        try:
            from routes.anuncios import init_anuncios_table
            init_anuncios_table()
        except Exception as e:
            print(f"⚠️ Erro ao inicializar anúncios: {e}")

        # M28 FASE 2+3 — Guard de migrations + schema preflight
        # ABORTA startup se alembic divergir de head OU se colunas criticas
        # estiverem ausentes. Em dev/staging: somente loga.
        from services.deploy_guard import run_all_checks
        try:
            run_all_checks(db, is_production=is_prod)
            print("[deploy_guard] OK: migrations + schema em conformidade")
        except RuntimeError as exc:
            # Em producao isto NAO pode ser silenciado. Logar e re-raise
            # para que o container saia com codigo != 0 e o orchestrator
            # (docker, k8s, systemd) NAO inicie workers.
            print(f"\n🚨 [deploy_guard] STARTUP ABORTADO:\n{exc}\n")
            raise

        # 3. Inicializar feature flags padrão
        try:
            from services.feature_flag_service import FeatureFlagService
            FeatureFlagService.init_defaults()
            print("✅ Feature flags inicializadas")
        except Exception as e:
            print(f"⚠️ Erro ao inicializar feature flags: {e}")

        # 3. Criar diretórios de upload
        upload_dir = app.config.get("UPLOAD_FOLDER_EXAMES")
        if upload_dir and not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
            print(f"📁 Diretório de upload criado: {upload_dir}")

    return app


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port", type=int, default=5002, help="Porta para rodar o servidor"
    )
    args = parser.parse_args()

    app = create_app()
    print("🚀 AraOS SERVER STARTED!")
    print("🔒 CORS: Configurado com origens permitidas")
    print("🔑 CSRF: Habilitado")
    print("🛡️ Rate limiting: Ativo")
    print(f"📡 Porta: {args.port}")
    # Desativar debug mode para evitar locks e recarregamentos em background
    app.run(host="0.0.0.0", port=args.port, debug=False, threaded=True)
