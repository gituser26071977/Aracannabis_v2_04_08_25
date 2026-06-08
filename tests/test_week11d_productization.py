"""
AraOS Week 11D — Productization Layer Integration Tests.

Valida:
- Cannabis Module APIs (persistent)
- Digital Twin APIs
- Follow-up Engine APIs
- API response standardization
"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app_cors_livre import create_app
from models import db, Profissional, Paciente
from association.models import Associacao
from models_extra import UsuarioAssociacao
from werkzeug.security import generate_password_hash
from datetime import datetime, date


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            tenant, doctor, patient = _seed_test_data()
            yield {"client": client, "tenant_id": tenant.id, "doctor_email": doctor.email, "patient_id": patient.id}
            # Cleanup: remove test data instead of drop_all (avoids FK constraints)
            from araos.specialties.cannabis.db_models import CannabisProfileModel
            from araos.followup.db_models import FollowupProgramModel
            db.session.query(CannabisProfileModel).filter(CannabisProfileModel.tenant_id == tenant.id).delete(synchronize_session=False)
            db.session.query(FollowupProgramModel).filter(FollowupProgramModel.tenant_id == tenant.id).delete(synchronize_session=False)
            db.session.query(Paciente).filter(Paciente.id == patient.id).delete(synchronize_session=False)
            db.session.query(UsuarioAssociacao).filter(UsuarioAssociacao.associacao_id == tenant.id).delete(synchronize_session=False)
            db.session.query(Profissional).filter(Profissional.id == doctor.id).delete(synchronize_session=False)
            db.session.query(Associacao).filter(Associacao.id == tenant.id).delete(synchronize_session=False)
            db.session.commit()


def _seed_test_data():
    import uuid
    uid = uuid.uuid4().hex[:8]
    tenant = Associacao(nome=f"Test Tenant {uid}", slug=f"test-tenant-{uid}", cnpj=f"TEST{uuid.uuid4().hex[:12].upper()}")
    db.session.add(tenant)
    db.session.commit()

    doctor = Profissional(
        nome=f"Dr. Test {uid}", email=f"test{uid}@doctor.com", usuario=f"test{uid}@doctor.com",
        senha=generate_password_hash("Medico@123"), role="profissional",
        crm=f"TEST{uid[:4].upper()}", uf_crm="SP", status_cadastro="aprovado",
        data_aprovacao=datetime.utcnow(),
    )
    db.session.add(doctor)
    db.session.commit()

    link = UsuarioAssociacao(profissional_id=doctor.id, associacao_id=tenant.id, role="admin", status="active")
    db.session.add(link)

    patient = Paciente(
        nome="Paciente Teste", data_nascimento=date(1990, 1, 1),
        profissional_responsavel_id=doctor.id, associacao_id=tenant.id,
        em_tratamento=True, condicao_medica="Dor Crônica",
    )
    db.session.add(patient)
    db.session.commit()

    return tenant, doctor, patient


def _login(client_info):
    r = client_info["client"].post("/api/auth/login", json={"email": client_info["doctor_email"], "senha": "Medico@123"})
    assert r.status_code == 200
    token = r.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}", "X-Association-ID": str(client_info["tenant_id"])}


class TestApiStandardization:
    def test_response_envelope(self, client):
        from routes.cannabis import success_response, error_response
        with client["client"].application.app_context():
            resp, code = success_response(data={"test": True})
            assert code == 200
            assert resp.get_json()["success"] is True
            assert resp.get_json()["data"]["test"] is True
            assert resp.get_json()["error"] is None
            assert "meta" in resp.get_json()

            resp, code = error_response("TEST_ERROR", "Mensagem", 400)
            assert code == 400
            assert resp.get_json()["success"] is False
            assert resp.get_json()["error"]["code"] == "TEST_ERROR"


class TestCannabisApis:
    def test_full_cannabis_flow(self, client):
        headers = _login(client)
        patient_id = client["patient_id"]

        # 1. Create profile
        r = client["client"].post("/api/cannabis/profiles", headers=headers, json={
            "patient_id": patient_id,
            "primary_condition": "Dor Crônica",
            "treatment_status": "active",
        })
        assert r.status_code == 201
        body = r.get_json()
        assert body["success"] is True
        assert body["data"]["primary_condition"] == "Dor Crônica"

        # 2. Create product
        r = client["client"].post("/api/cannabis/products", headers=headers, json={
            "name": "CBD 50mg/ml", "cbd_mg": 50.0, "thc_mg": 2.0,
            "formulation": "oil", "route": "sublingual",
        })
        assert r.status_code == 201
        product_id = r.get_json()["data"]["id"]

        # 3. Create medication
        r = client["client"].post(f"/api/cannabis/profiles/{patient_id}/medications", headers=headers, json={
            "product_id": product_id, "prescribed_dose_mg": 25.0, "frequency": "twice_daily",
        })
        assert r.status_code == 201

        # 4. Create dose
        r = client["client"].post("/api/cannabis/doses", headers=headers, json={
            "patient_id": patient_id, "dose_mg": 25.0, "thc_mg": 1.0, "cbd_mg": 12.5,
            "entry_type": "administered", "reason": "Dor",
        })
        assert r.status_code == 201

        # 5. Create outcome
        r = client["client"].post("/api/cannabis/outcomes", headers=headers, json={
            "patient_id": patient_id, "metric_name": "Dor", "score": 4.0, "max_score": 10.0,
        })
        assert r.status_code == 201

        # 6. List outcomes
        r = client["client"].get(f"/api/cannabis/outcomes/{patient_id}", headers=headers)
        assert r.status_code == 200
        assert len(r.get_json()["data"]) == 1

        # 7. Get full profile
        r = client["client"].get(f"/api/cannabis/profiles/{patient_id}", headers=headers)
        assert r.status_code == 200
        data = r.get_json()["data"]
        assert data["primary_condition"] == "Dor Crônica"
        assert len(data["medications"]) == 1
        assert len(data["dose_entries"]) == 1
        assert len(data["outcome_scores"]) == 1


class TestDigitalTwinApis:
    def test_twin_endpoints(self, client):
        headers = _login(client)
        patient_id = client["patient_id"]

        # Seed legacy data
        from models import Sintoma, Dosagem, Evolucao, Consulta
        tenant_id = client["tenant_id"]
        db.session.add(Sintoma(paciente_id=patient_id, associacao_id=tenant_id, data=date.today(), sintoma="Dor", intensidade=5))
        db.session.add(Dosagem(paciente_id=patient_id, associacao_id=tenant_id, data=date.today(), dosagem="CBD 50mg", gotas=5))
        db.session.add(Evolucao(paciente_id=patient_id, profissional_id=1, associacao_id=tenant_id, data_evolucao=datetime.utcnow(), nota_evolucao="Melhora"))
        db.session.commit()

        for endpoint in ["", "/summary", "/timeline", "/outcomes", "/dashboard"]:
            r = client["client"].get(f"/api/twin/{patient_id}{endpoint}", headers=headers)
            assert r.status_code == 200, f"Failed at {endpoint}: {r.status_code}"
            body = r.get_json()
            assert body["success"] is True
            assert "meta" in body

        # Validate timeline structure
        r = client["client"].get(f"/api/twin/{patient_id}/timeline", headers=headers)
        data = r.get_json()["data"]
        assert "events" in data
        assert data["total_events"] > 0


class TestFollowupApis:
    def test_full_followup_flow(self, client):
        headers = _login(client)
        patient_id = client["patient_id"]

        # 1. Create program
        r = client["client"].post("/api/followup/programs", headers=headers, json={
            "patient_id": patient_id, "name": "Acompanhamento Cannabis", "specialty_code": "cannabis",
        })
        assert r.status_code == 201
        program_id = r.get_json()["data"]["id"]

        # 2. Create phase
        r = client["client"].post("/api/followup/phases", headers=headers, json={
            "program_id": program_id, "name": "Titulação", "order_index": 1,
        })
        assert r.status_code == 201

        # 3. Create checkpoint
        r = client["client"].post("/api/followup/checkpoints", headers=headers, json={
            "program_id": program_id, "name": "Avaliação D+7", "due_date": "2026-06-15T10:00:00",
        })
        assert r.status_code == 201
        cp_id = r.get_json()["data"]["id"]

        # 4. Update checkpoint status
        r = client["client"].put(f"/api/followup/checkpoints/{cp_id}", headers=headers, json={"status": "completed"})
        assert r.status_code == 200

        # 5. Create questionnaire
        r = client["client"].post("/api/followup/questionnaires", headers=headers, json={
            "program_id": program_id, "name": "Escala de Dor", "category": "pain",
        })
        assert r.status_code == 201
        qn_id = r.get_json()["data"]["id"]

        # 6. Create question
        r = client["client"].post("/api/followup/questions", headers=headers, json={
            "questionnaire_id": qn_id, "text": "Qual a intensidade da dor?", "question_type": "scale", "max_value": 10,
        })
        assert r.status_code == 201
        q_id = r.get_json()["data"]["id"]

        # 7. Create response
        r = client["client"].post("/api/followup/responses", headers=headers, json={
            "questionnaire_id": qn_id, "question_id": q_id, "patient_id": patient_id,
            "numeric_value": 4.0, "value": "4",
        })
        assert r.status_code == 201

        # 8. List responses
        r = client["client"].get(f"/api/followup/responses?patient_id={patient_id}", headers=headers)
        assert r.status_code == 200
        assert len(r.get_json()["data"]) == 1

        # 9. Get program deep
        r = client["client"].get(f"/api/followup/programs/{program_id}", headers=headers)
        assert r.status_code == 200
        data = r.get_json()["data"]
        assert len(data["phases"]) == 1
        assert len(data["checkpoints"]) == 1
        assert len(data["questionnaires"]) == 1
