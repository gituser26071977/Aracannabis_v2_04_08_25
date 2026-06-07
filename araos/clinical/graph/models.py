"""
AraOS Clinical — Graph Model.

Modelo conceitual de grafo clínico.
NÃO usa Neo4j ainda — é preparação para Knowledge Graph futuro.

Conceito:
    Paciente
    ├─ Diagnósticos
    ├─ Medicamentos
    ├─ Exames
    ├─ Procedimentos
    ├─ Alergias
    └─ Eventos

Este modelo pode ser serializado para:
    - JSON
    - GraphML (Neo4j futuro)
    - Cypher queries (Neo4j futuro)
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class NodeType(str, Enum):
    """Tipos de nós no grafo clínico."""
    PATIENT = "patient"
    DIAGNOSIS = "diagnosis"
    MEDICATION = "medication"
    ALLERGY = "allergy"
    PROCEDURE = "procedure"
    EXAM = "exam"
    RISK_FACTOR = "risk_factor"
    SYMPTOM = "symptom"
    CONSULTATION = "consultation"
    EVENT = "event"


class RelationshipType(str, Enum):
    """Tipos de relacionamentos no grafo clínico."""
    HAS_DIAGNOSIS = "HAS_DIAGNOSIS"
    TAKES = "TAKES"
    IS_ALLERGIC_TO = "IS_ALLERGIC_TO"
    UNDERWENT = "UNDERWENT"
    HAD_EXAM = "HAD_EXAM"
    HAS_RISK_FACTOR = "HAS_RISK_FACTOR"
    REPORTED = "REPORTED"
    ATTENDED = "ATTENDED"
    CAUSED = "CAUSED"
    CONTRAINDICATES = "CONTRAINDICATES"
    TREATS = "TREATS"
    RESULTED_IN = "RESULTED_IN"


@dataclass
class ClinicalNode:
    """Nó do grafo clínico."""
    id: str
    node_type: NodeType
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.node_type.value,
            "label": self.label,
            "properties": self.properties,
        }
    
    def to_cypher(self) -> str:
        """Gera Cypher para Neo4j futuro."""
        props = ", ".join([f"{k}: {repr(v)}" for k, v in self.properties.items()])
        return f"(:{self.node_type.value} {{id: '{self.id}', label: '{self.label}', {props}}})"


@dataclass
class ClinicalRelationship:
    """Relacionamento do grafo clínico."""
    source_id: str
    target_id: str
    rel_type: RelationshipType
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.rel_type.value,
            "properties": self.properties,
        }
    
    def to_cypher(self) -> str:
        """Gera Cypher para Neo4j futuro."""
        props = ", ".join([f"{k}: {repr(v)}" for k, v in self.properties.items()])
        return (
            f"MATCH (a {{id: '{self.source_id}'}}), (b {{id: '{self.target_id}'}}) "
            f"CREATE (a)-[:{self.rel_type.value} {{{props}}}]->(b)"
        )


@dataclass
class ClinicalGraph:
    """
    Grafo clínico completo de um paciente.
    
    Pode ser serializado para múltiplos formatos.
    """
    
    patient_id: str
    nodes: List[ClinicalNode] = field(default_factory=list)
    relationships: List[ClinicalRelationship] = field(default_factory=list)
    
    def add_node(self, node: ClinicalNode) -> None:
        """Adiciona nó ao grafo."""
        self.nodes.append(node)
    
    def add_relationship(self, rel: ClinicalRelationship) -> None:
        """Adiciona relacionamento ao grafo."""
        self.relationships.append(rel)
    
    def get_neighbors(self, node_id: str) -> List[ClinicalNode]:
        """Retorna nós vizinhos."""
        neighbor_ids = {
            rel.target_id
            for rel in self.relationships
            if rel.source_id == node_id
        }
        return [n for n in self.nodes if n.id in neighbor_ids]
    
    def find_diagnoses(self) -> List[ClinicalNode]:
        """Retorna diagnósticos do paciente."""
        return [n for n in self.nodes if n.node_type == NodeType.DIAGNOSIS]
    
    def find_medications(self) -> List[ClinicalNode]:
        """Retorna medicações do paciente."""
        return [n for n in self.nodes if n.node_type == NodeType.MEDICATION]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dict."""
        return {
            "patient_id": self.patient_id,
            "nodes": [n.to_dict() for n in self.nodes],
            "relationships": [r.to_dict() for r in self.relationships],
            "node_count": len(self.nodes),
            "relationship_count": len(self.relationships),
        }
    
    def to_cypher(self) -> str:
        """Serializa para Cypher (Neo4j futuro)."""
        lines = []
        for node in self.nodes:
            lines.append(f"CREATE {node.to_cypher()}")
        for rel in self.relationships:
            lines.append(rel.to_cypher())
        return "\n".join(lines)
    
    def to_graphml(self) -> str:
        """Serializa para GraphML."""
        # Simplificado — em produção gerar XML completo
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<graphml>
  <graph id="clinical_graph_{self.patient_id}" edgedefault="directed">
    {''.join(f'<node id="{n.id}"/>' for n in self.nodes)}
    {''.join(f'<edge source="{r.source_id}" target="{r.target_id}"/>' for r in self.relationships)}
  </graph>
</graphml>"""


class ClinicalGraphBuilder:
    """
    Builder para construir grafo clínico a partir de entidades.
    
    Uso:
        builder = ClinicalGraphBuilder(patient_id)
        builder.add_diagnoses(diagnoses)
        builder.add_medications(medications)
        graph = builder.build()
    """
    
    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        self.graph = ClinicalGraph(patient_id=patient_id)
        
        # Adicionar nó paciente
        self.graph.add_node(ClinicalNode(
            id=patient_id,
            node_type=NodeType.PATIENT,
            label=f"Patient {patient_id}",
        ))
    
    def add_diagnoses(self, diagnoses: List[Dict[str, Any]]) -> None:
        """Adiciona diagnósticos ao grafo."""
        for d in diagnoses:
            node = ClinicalNode(
                id=d.get("id", ""),
                node_type=NodeType.DIAGNOSIS,
                label=d.get("description", ""),
                properties={
                    "icd10_code": d.get("icd10_code"),
                    "status": d.get("status"),
                    "is_chronic": d.get("is_chronic"),
                },
            )
            self.graph.add_node(node)
            self.graph.add_relationship(ClinicalRelationship(
                source_id=self.patient_id,
                target_id=node.id,
                rel_type=RelationshipType.HAS_DIAGNOSIS,
            ))
    
    def add_medications(self, medications: List[Dict[str, Any]]) -> None:
        """Adiciona medicações ao grafo."""
        for m in medications:
            node = ClinicalNode(
                id=m.get("id", ""),
                node_type=NodeType.MEDICATION,
                label=m.get("name", ""),
                properties={
                    "dosage": m.get("dosage"),
                    "frequency": m.get("frequency"),
                    "status": m.get("status"),
                },
            )
            self.graph.add_node(node)
            self.graph.add_relationship(ClinicalRelationship(
                source_id=self.patient_id,
                target_id=node.id,
                rel_type=RelationshipType.TAKES,
            ))
    
    def add_allergies(self, allergies: List[Dict[str, Any]]) -> None:
        """Adiciona alergias ao grafo."""
        for a in allergies:
            node = ClinicalNode(
                id=a.get("id", ""),
                node_type=NodeType.ALLERGY,
                label=a.get("substance", ""),
                properties={
                    "reaction": a.get("reaction"),
                    "severity": a.get("severity"),
                },
            )
            self.graph.add_node(node)
            self.graph.add_relationship(ClinicalRelationship(
                source_id=self.patient_id,
                target_id=node.id,
                rel_type=RelationshipType.IS_ALLERGIC_TO,
            ))
    
    def build(self) -> ClinicalGraph:
        """Retorna grafo construído."""
        return self.graph
