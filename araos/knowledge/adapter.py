"""
AraOS Knowledge — LLM Knowledge Adapter.

Adaptador que conecta a Knowledge Layer ao Context Builder e LLM.

FLUXO OBRIGATÓRIO:
    Knowledge Layer → Context Builder → LLM
    
    NUNCA:
    LLM → busca direta na Knowledge Layer

Week 8 — Knowledge Layer v1
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .repository import KnowledgeRepository
from .retrieval import KnowledgeRetrievalEngine, RetrievalResult
from .types import KnowledgeType
from .models import KnowledgeDocument

from araos.intelligence.llm import LLMMessage, MessageRole
from araos.intelligence.context.builder import ClinicalContextBuilder


@dataclass
class KnowledgeContext:
    """
    Contexto de conhecimento para injeção no prompt LLM.
    
    Attributes:
        documents: Documentos recuperados
        context_text: Texto formatado para o prompt
        sources: Lista de fontes utilizadas
        metadata: Metadados da recuperação
    """
    documents: List[KnowledgeDocument] = field(default_factory=list)
    context_text: str = ""
    sources: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMKnowledgeAdapter:
    """
    Adaptador entre Knowledge Layer e LLM.
    
    Responsabilidades:
        1. Consultar Knowledge Layer antes do LLM
        2. Formatar documentos recuperados em contexto
        3. Injetar contexto no prompt do LLM
        4. Registrar quais documentos foram usados
    
    Uso:
        adapter = LLMKnowledgeAdapter(repository)
        
        # Consultar knowledge
        k_context = adapter.retrieve(
            tenant_id="tenant_001",
            query="protocolo de hipertensão",
            knowledge_types=[KnowledgeType.CLINICAL, KnowledgeType.ORGANIZATIONAL],
        )
        
        # Construir mensagens LLM com contexto
        messages = adapter.build_messages(
            user_question="Como tratar hipertensão?",
            knowledge_context=k_context,
        )
    """
    
    def __init__(self, repository: KnowledgeRepository):
        self.repository = repository
        self.retrieval = KnowledgeRetrievalEngine(repository)
    
    def retrieve(
        self,
        tenant_id: str,
        query: str,
        knowledge_types: Optional[List[KnowledgeType]] = None,
        patient_id: Optional[str] = None,
        limit: int = 5,
    ) -> KnowledgeContext:
        """
        Recupera conhecimento relevante para uma consulta.
        
        Args:
            tenant_id: ID do tenant
            query: Pergunta do usuário
            knowledge_types: Tipos de conhecimento a buscar
            patient_id: ID do paciente (para busca específica)
            limit: Máximo de documentos
        
        Returns:
            KnowledgeContext com documentos e texto formatado
        """
        documents = []
        sources = []
        
        # Buscar por tipo de conhecimento
        if knowledge_types:
            for k_type in knowledge_types:
                results = self.retrieval.search(
                    tenant_id=tenant_id,
                    query=query,
                    knowledge_type=k_type,
                    limit=limit,
                )
                for result in results:
                    if result.document not in documents:
                        documents.append(result.document)
                        sources.append(f"{result.document.source_type.value}:{result.document.document_id}")
        else:
            # Busca geral
            results = self.retrieval.search(
                tenant_id=tenant_id,
                query=query,
                limit=limit,
            )
            for result in results:
                documents.append(result.document)
                sources.append(f"{result.document.source_type.value}:{result.document.document_id}")
        
        # Formatar contexto
        context_text = self._format_context(documents, query)
        
        return KnowledgeContext(
            documents=documents,
            context_text=context_text,
            sources=sources,
            metadata={
                "query": query,
                "document_count": len(documents),
                "knowledge_types": [k.value for k in knowledge_types] if knowledge_types else [],
                "patient_id": patient_id,
            },
        )
    
    def build_messages(
        self,
        user_question: str,
        knowledge_context: KnowledgeContext,
        system_prompt: Optional[str] = None,
    ) -> List[LLMMessage]:
        """
        Constrói mensagens LLM com contexto de conhecimento.
        
        Args:
            user_question: Pergunta do usuário
            knowledge_context: Contexto recuperado da Knowledge Layer
            system_prompt: Prompt de sistema customizado (opcional)
        
        Returns:
            Lista de LLMMessage pronta para o LLMRuntime
        """
        messages = []
        
        # System prompt
        if system_prompt:
            messages.append(LLMMessage(role=MessageRole.SYSTEM, content=system_prompt))
        else:
            messages.append(LLMMessage(
                role=MessageRole.SYSTEM,
                content=(
                    "Você é Ara, assistente de uma clínica médica. "
                    "Use o conhecimento fornecido para responder. "
                    "Se o conhecimento não for suficiente, diga que não sabe. "
                    "NUNCA faça diagnósticos ou prescrições."
                ),
            ))
        
        # Contexto de conhecimento
        if knowledge_context.context_text:
            messages.append(LLMMessage(
                role=MessageRole.SYSTEM,
                content=f"=== CONHECIMENTO RELEVANTE ===\n{knowledge_context.context_text}",
            ))
        
        # Pergunta do usuário
        messages.append(LLMMessage(role=MessageRole.USER, content=user_question))
        
        return messages
    
    def _format_context(self, documents: List[KnowledgeDocument], query: str) -> str:
        """Formata documentos em texto de contexto."""
        if not documents:
            return ""
        
        parts = []
        for i, doc in enumerate(documents, 1):
            parts.append(f"[Documento {i}] {doc.title}")
            parts.append(f"Tipo: {doc.knowledge_type.value}")
            parts.append(f"Fonte: {doc.source_type.value}")
            
            # Usar conteúdo completo se curto, ou preview se longo
            content = doc.content
            if len(content) > 800:
                content = content[:800] + "\n[... conteúdo truncado ...]"
            
            parts.append(f"Conteúdo:\n{content}")
            parts.append("")
        
        return "\n".join(parts)
    
    def get_used_documents(self, knowledge_context: KnowledgeContext) -> List[Dict[str, Any]]:
        """
        Retorna metadados dos documentos utilizados.
        
        Útil para observabilidade e audit.
        """
        return [
            {
                "document_id": doc.document_id,
                "title": doc.title,
                "knowledge_type": doc.knowledge_type.value,
                "source_type": doc.source_type.value,
                "version": doc.metadata.version,
                "author": doc.metadata.author_id,
            }
            for doc in knowledge_context.documents
        ]
