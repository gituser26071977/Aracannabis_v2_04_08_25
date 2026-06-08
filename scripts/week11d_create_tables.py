#!/usr/bin/env python3
"""Create Week 11D database tables without dropping existing data."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_cors_livre import create_app
from models import db

# Import all new models so they register with SQLAlchemy metadata
from araos.specialties.cannabis.db_models import (
    CannabisProfileModel,
    CannabisTherapeuticGoalModel,
    CannabisProductModel,
    CannabisMedicationModel,
    CannabisDoseEntryModel,
    CannabisOutcomeScoreModel,
    CannabisAlertModel,
)
from araos.followup.db_models import (
    FollowupProgramModel,
    FollowupPhaseModel,
    FollowupCheckpointModel,
    FollowupQuestionnaireModel,
    FollowupQuestionModel,
    FollowupResponseModel,
    FollowupAlertModel,
    FollowupEscalationModel,
)

app = create_app()
with app.app_context():
    # Create only tables that don't exist yet
    db.create_all()
    print("✅ Week 11D tables created (or already exist).")
