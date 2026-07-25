"""
araos.clinical.knowledge — Clinical Knowledge Engine v1.0.

Sprint 4.4 — primeira camada de inteligência clínica sobre o
Clinical Gene Engine (Sprint 4.3). Construída como pure domain +
InMemory + Demo Parcial, sem persistência definitiva.

Arquitetura:
    - ClinicalGenome Projection  (read-model, derivado)
    - Correlation Engine          (associação, nunca causalidade)
    - Hypothesis Engine           (conhecimento inferido)
    - Knowledge Graph             (projeção reconstruível)
    - Cohort Builder              (consultas estruturadas)
    - Research Workspace          (sessões reproduzíveis)
    - Explainability Pipeline     (toda inferência é explicada)

Foundation Freeze (ADR-0006):
    Este módulo NÃO modifica AS-000, AS-001, AS-002, ASM-001.
    Prepara o domínio que sustentará AS-004 (Clinical Knowledge).

Pure Domain:
    Zero dependências de SQL/HTTP/ORM/framework.
    Apenas stdlib + tipos validados do genome/.
"""