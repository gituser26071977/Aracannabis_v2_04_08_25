"""
AraOS Clinical — Summary Engine.

Gera resumos clínicos estruturados a partir do ClinicalProfile.

Totalmente rules-based.
Sem LLM.
Sem embeddings.

Saída: texto estruturado pronto para Voice, Concierge e futuros agentes.

Exemplo de saída:
    "Paciente masculino, 45 anos.
    Hipertensão arterial ativa.
    Diabetes mellitus tipo 2.
    Uso atual: Losartana 50mg, Metformina 850mg.
    Última HbA1c: 7,3% (jun/2026).
    Sem alergias registradas."
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SummaryResult:
    """Resultado do Summary Engine."""
    text: str
    sections: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    version: int = 1
    generated_at: str = ""


class ClinicalSummaryEngine:
    """
    Engine de resumos clínicos baseado em regras.
    
    Uso:
        engine = ClinicalSummaryEngine()
        summary = engine.generate(profile)
        print(summary.text)
    """
    
    def generate(
        self,
        profile: Dict[str, Any],
        patient_demographics: Optional[Dict[str, Any]] = None,
    ) -> SummaryResult:
        """
        Gera resumo clínico a partir de perfil.
        
        Args:
            profile: ClinicalProfile como dict
            patient_demographics: Dados demográficos do paciente
        
        Returns:
            SummaryResult com texto e seções
        """
        sections: Dict[str, str] = {}
        warnings: List[str] = []
        
        # Cabeçalho demográfico
        sections["header"] = self._build_header(patient_demographics)
        
        # Diagnósticos ativos
        sections["diagnoses"] = self._build_diagnoses(
            profile.get("active_diagnoses", [])
        )
        
        # Medicações ativas
        sections["medications"] = self._build_medications(
            profile.get("active_medications", [])
        )
        
        # Alergias
        sections["allergies"] = self._build_allergies(
            profile.get("allergies", [])
        )
        
        # Fatores de risco
        sections["risk_factors"] = self._build_risk_factors(
            profile.get("risk_factors", [])
        )
        
        # Últimos exames
        sections["exams"] = self._build_exams(
            profile.get("last_exams", {})
        )
        
        # Procedimentos recentes
        sections["procedures"] = self._build_procedures(
            profile.get("procedures", [])
        )
        
        # Detectar alertas
        warnings = self._detect_warnings(profile)
        
        # Montar texto final
        text = self._assemble_text(sections)
        
        return SummaryResult(
            text=text,
            sections=sections,
            warnings=warnings,
            version=profile.get("summary_version", 0) + 1,
            generated_at=datetime.utcnow().isoformat() + "Z",
        )
    
    def _build_header(self, demographics: Optional[Dict[str, Any]]) -> str:
        """Constrói cabeçalho demográfico."""
        if not demographics:
            return "Paciente sem dados demográficos registrados."
        
        parts = []
        if demographics.get("gender"):
            parts.append(f"Paciente {demographics['gender']}")
        if demographics.get("age"):
            parts.append(f", {demographics['age']} anos")
        if demographics.get("name"):
            parts.insert(0, demographics["name"])
        
        return "".join(parts) + "." if parts else "Paciente."
    
    def _build_diagnoses(self, diagnoses: List[Dict[str, Any]]) -> str:
        """Constrói seção de diagnósticos."""
        if not diagnoses:
            return "Sem diagnósticos ativos registrados."
        
        lines = ["Diagnósticos ativos:"]
        for d in diagnoses:
            line = f"  • {d.get('description', 'Diagnóstico não especificado')}"
            if d.get("icd10_code"):
                line += f" (ICD-10: {d['icd10_code']})"
            if d.get("is_primary"):
                line += " [primário]"
            if d.get("is_chronic"):
                line += " [crônico]"
            lines.append(line)
        
        return "\n".join(lines)
    
    def _build_medications(self, medications: List[Dict[str, Any]]) -> str:
        """Constrói seção de medicações."""
        if not medications:
            return "Sem medicações ativas registradas."
        
        lines = ["Uso atual:"]
        for m in medications:
            line = f"  • {m.get('name', 'Medicação não especificada')}"
            if m.get("dosage"):
                line += f" {m['dosage']}"
            if m.get("frequency"):
                line += f", {m['frequency']}"
            if m.get("route"):
                line += f" ({m['route']})"
            lines.append(line)
        
        return "\n".join(lines)
    
    def _build_allergies(self, allergies: List[Dict[str, Any]]) -> str:
        """Constrói seção de alergias."""
        if not allergies:
            return "Sem alergias registradas."
        
        lines = ["Alergias:"]
        for a in allergies:
            line = f"  • {a.get('substance', 'Substância não especificada')}"
            if a.get("reaction"):
                line += f" — Reação: {a['reaction']}"
            if a.get("severity"):
                line += f" [{a['severity']}]"
            if a.get("verified"):
                line += " (verificada)"
            lines.append(line)
        
        return "\n".join(lines)
    
    def _build_risk_factors(self, risk_factors: List[Dict[str, Any]]) -> str:
        """Constrói seção de fatores de risco."""
        if not risk_factors:
            return "Sem fatores de risco registrados."
        
        lines = ["Fatores de risco:"]
        for r in risk_factors:
            line = f"  • {r.get('factor_type', 'Fator não especificado')}"
            if r.get("severity"):
                line += f" [{r['severity']}]"
            lines.append(line)
        
        return "\n".join(lines)
    
    def _build_exams(self, exams: Dict[str, Any]) -> str:
        """Constrói seção de exames."""
        if not exams:
            return "Sem exames recentes registrados."
        
        lines = ["Exames recentes:"]
        for exam_type, result in exams.items():
            value = result.get("value", "N/A") if isinstance(result, dict) else result
            date = result.get("date", "") if isinstance(result, dict) else ""
            line = f"  • {exam_type}: {value}"
            if date:
                line += f" ({date})"
            lines.append(line)
        
        return "\n".join(lines)
    
    def _build_procedures(self, procedures: List[Dict[str, Any]]) -> str:
        """Constrói seção de procedimentos."""
        if not procedures:
            return "Sem procedimentos recentes registrados."
        
        lines = ["Procedimentos recentes:"]
        for p in procedures[:5]:  # Últimos 5
            line = f"  • {p.get('description', 'Procedimento não especificado')}"
            if p.get("performed_at"):
                line += f" em {p['performed_at']}"
            lines.append(line)
        
        return "\n".join(lines)
    
    def _detect_warnings(self, profile: Dict[str, Any]) -> List[str]:
        """Detecta alertas clínicos no perfil."""
        warnings = []
        
        # Alergia grave
        for a in profile.get("allergies", []):
            if a.get("severity") in ("severe", "life_threatening"):
                warnings.append(f"Alergia grave: {a.get('substance')}")
        
        # Múltiplos diagnósticos crônicos
        chronic_count = sum(
            1 for d in profile.get("active_diagnoses", [])
            if d.get("is_chronic")
        )
        if chronic_count >= 3:
            warnings.append(f"Paciente com múltiplas doenças crônicas ({chronic_count})")
        
        # Sem medicação para diagnóstico crônico
        has_chronic = any(
            d.get("is_chronic") for d in profile.get("active_diagnoses", [])
        )
        if has_chronic and not profile.get("active_medications"):
            warnings.append("Diagnóstico crônico sem medicação ativa")
        
        return warnings
    
    def _assemble_text(self, sections: Dict[str, str]) -> str:
        """Monta texto final do resumo."""
        order = [
            "header",
            "diagnoses",
            "medications",
            "allergies",
            "risk_factors",
            "exams",
            "procedures",
        ]
        
        parts = []
        for key in order:
            if sections.get(key):
                parts.append(sections[key])
        
        return "\n\n".join(parts)
