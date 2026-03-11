from models import Paciente, db
from association.models import Membro

class IntegrationService:
    @staticmethod
    def find_patient_by_cpf(cpf):
        """
        Locates a patient in the Clinical System (SIAP) using CPF.
        Removes non-numeric characters for comparison.
        """
        from sqlalchemy import or_
        
        clean_cpf = ''.join(filter(str.isdigit, cpf))
        
        # Format as XXX.XXX.XXX-XX for searching
        formatted_cpf = f"{clean_cpf[:3]}.{clean_cpf[3:6]}.{clean_cpf[6:9]}-{clean_cpf[9:]}" if len(clean_cpf) == 11 else clean_cpf

        # Search for both raw and formatted
        patient = Paciente.query.filter(or_(Paciente.cpf == clean_cpf, Paciente.cpf == formatted_cpf)).first()
        return patient

    @staticmethod
    def link_member_to_patient(membro_id):
        """
        Attempts to link an existing Member to a Patient via CPF.
        """
        membro = Membro.query.get(membro_id)
        if not membro or not membro.cpf:
            return False, "Member not found or no CPF"

        patient = IntegrationService.find_patient_by_cpf(membro.cpf)
        if patient:
            membro.paciente_id = patient.id
            db.session.commit()
            return True, f"Linked to Patient ID {patient.id}"
        
        return False, "Patient not found in SIAP"
