#!/usr/bin/env python3
"""
Script de setup para o módulo de Onboarding & UX (Squad C)
- Adiciona colunas ao Profissional se não existirem
- Cria tabelas EmailVerification e OnboardingProgress
- Ativa feature flags padrão
"""

import os
import sys

# Adicionar raiz do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models import db, Profissional
from models_extra import EmailVerification, OnboardingProgress
from services.feature_flag_service import FeatureFlagService
from app_cors_livre import create_app


def add_column_if_not_exists(table_name, column_name, column_def):
    """Adiciona coluna se não existir (PostgreSQL e SQLite)"""
    from sqlalchemy import text
    try:
        # Tentar adicionar a coluna
        db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"))
        db.session.commit()
        print(f"  ✅ Coluna {column_name} adicionada em {table_name}")
        return True
    except Exception as e:
        db.session.rollback()
        err = str(e).lower()
        if 'already exists' in err or 'duplicate column' in err or 'existe' in err:
            print(f"  ⚡ Coluna {column_name} já existe em {table_name}")
            return False
        print(f"  ⚠️ Erro ao adicionar {column_name}: {e}")
        return False


def setup_profissional_columns():
    """Adiciona colunas de onboarding ao Profissional"""
    print("📋 Verificando colunas em 'profissionais'...")
    # PostgreSQL / SQLite syntax
    add_column_if_not_exists('profissionais', 'status_conta', "VARCHAR DEFAULT 'active' NOT NULL")
    add_column_if_not_exists('profissionais', 'email_verified', "BOOLEAN DEFAULT FALSE")
    add_column_if_not_exists('profissionais', 'onboarding_completed', "BOOLEAN DEFAULT FALSE")
    add_column_if_not_exists('profissionais', 'onboarding_step', "INTEGER DEFAULT 0")


def create_new_tables():
    """Cria tabelas novas se não existirem"""
    print("📋 Verificando tabelas novas...")
    try:
        db.create_all()
        print("  ✅ Tabelas criadas/verificadas")
    except Exception as e:
        print(f"  ⚠️ Erro ao criar tabelas: {e}")


def setup_feature_flags():
    """Inicializa feature flags padrão"""
    print("📋 Inicializando feature flags...")
    try:
        FeatureFlagService.init_defaults()
        print("  ✅ Feature flags inicializadas")
        flags = FeatureFlagService.list_all()
        for name, data in flags.items():
            if name in ('email_verification', 'onboarding_wizard', 'trial_banner'):
                print(f"     • {name}: {'✅ ativa' if data['enabled'] else '❌ inativa'}")
    except Exception as e:
        print(f"  ⚠️ Erro ao inicializar feature flags: {e}")


def main():
    print("=" * 60)
    print("🚀 Setup Onboarding & UX - Squad C")
    print("=" * 60)

    app = create_app()
    with app.app_context():
        setup_profissional_columns()
        create_new_tables()
        setup_feature_flags()

    print("=" * 60)
    print("✅ Setup concluído!")
    print("=" * 60)


if __name__ == '__main__':
    main()
