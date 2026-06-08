import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, redirect
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from models import db
from config import get_config
from security_config import ALLOWED_ORIGINS, init_limiter, add_security_headers
from tenant_lib import configure_tenant_filters
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

    # Configurar token CSRF
    app.config["CSRF_TOKEN"] = secrets.token_hex(32)

    # Configurações de upload de arquivos
    app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500MB max file size
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
            "X-Association-ID",
        ],
        expose_headers=[
            "Content-Type",
            "Authorization",
            "X-CSRF-Token",
            "X-Association-ID",
        ],
        supports_credentials=True,
        max_age=86400,
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
                "name": "Aracannabis API",
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
                "message": "API Aracannabis funcionando corretamente",
                "cors": "Configurado com origens permitidas",
                "security": "CSRF e rate limiting habilitados",
                "documentation": "Swagger UI available at /api/swagger",
            }
        )

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

    # Patient Portal (NEW)
    from routes.patient_auth import patient_auth_bp
    from routes.patient_portal import patient_portal_bp

    app.register_blueprint(patient_auth_bp, url_prefix="/api/patient-auth")
    app.register_blueprint(patient_portal_bp, url_prefix="/api/patient-portal")

    # Association Management Module
    from association.routes import association_bp

    app.register_blueprint(association_bp, url_prefix="/api/association")

    # [NEW] AI Clinical Pipeline
    from routes.ai_clinical import ai_clinical_bp
    from routes.hc_report import hc_report_bp

    app.register_blueprint(ai_clinical_bp, url_prefix="/api/ai-clinical")
    app.register_blueprint(hc_report_bp, url_prefix="/api/hc-report")

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

    # Inicializar banco de dados e diretórios
    with app.app_context():
        # 1. Criar tabelas primeiro
        try:
            # Importar models_extra para garantir que todas as tabelas sejam criadas
            import models_extra
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
    print("🚀 SERVIDOR ARACANNABIS INICIADO!")
    print("🔒 CORS: Configurado com origens permitidas")
    print("🔑 CSRF: Habilitado")
    print("🛡️ Rate limiting: Ativo")
    print(f"📡 Porta: {args.port}")
    # Desativar debug mode para evitar locks e recarregamentos em background
    app.run(host="0.0.0.0", port=args.port, debug=False, threaded=True)
