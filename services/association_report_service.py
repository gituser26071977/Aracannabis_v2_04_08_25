"""
Serviço de Relatórios para Associações
Ferramentas e funções para geração de relatórios inteligentes com IA
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from association.models import Associacao, Membro, Dispensacao, Estoque

class AssociationReportService:
    """Serviço para geração de relatórios de associações"""
    
    @staticmethod
    def get_association_overview(associacao_id: int) -> Dict[str, Any]:
        """Retorna visão geral completa da associação"""
        try:
            assoc = Associacao.query.get(associacao_id)
            if not assoc:
                return {"error": "Associação não encontrada"}
            
            # Estatísticas de membros
            total_membros = Membro.query.filter_by(associacao_id=associacao_id).count()
            membros_ativos = Membro.query.filter_by(
                associacao_id=associacao_id, 
                status='ativo'
            ).count()
            
            # Estatísticas de dispensações (últimos 30 dias)
            data_inicio = datetime.utcnow() - timedelta(days=30)
            dispensacoes_mes = Dispensacao.query.filter(
                Dispensacao.associacao_id == associacao_id,
                Dispensacao.data_dispensacao >= data_inicio
            ).count()
            
            # Estoque
            itens_estoque = Estoque.query.filter_by(associacao_id=associacao_id).count()
            
            return {
                "associacao": {
                    "id": assoc.id,
                    "nome": assoc.nome,
                    "cnpj": assoc.cnpj,
                    "ativo": assoc.ativo
                },
                "estatisticas": {
                    "total_membros": total_membros,
                    "membros_ativos": membros_ativos,
                    "membros_inativos": total_membros - membros_ativos,
                    "dispensacoes_30d": dispensacoes_mes,
                    "itens_estoque": itens_estoque
                },
                "data_consulta": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"error": f"Erro ao obter overview: {str(e)}"}
    
    @staticmethod
    def get_member_activity_report(associacao_id: int, member_id: Optional[int] = None) -> Dict[str, Any]:
        """Relatório de atividade de membros"""
        try:
            query = Membro.query.filter_by(associacao_id=associacao_id)
            if member_id:
                query = query.filter_by(id=member_id)
            
            membros = query.all()
            
            relatorio = []
            for membro in membros:
                # Buscar dispensações do membro
                dispensacoes = Dispensacao.query.filter_by(
                    membro_id=membro.id
                ).order_by(Dispensacao.data_dispensacao.desc()).limit(10).all()
                
                relatorio.append({
                    "membro": {
                        "id": membro.id,
                        "nome": membro.nome,
                        "cpf": membro.cpf,
                        "status": membro.status,
                        "data_filiacao": membro.data_filiacao.isoformat() if membro.data_filiacao else None
                    },
                    "atividade": {
                        "total_dispensacoes": len(dispensacoes),
                        "ultima_dispensacao": dispensacoes[0].data_dispensacao.isoformat() if dispensacoes else None,
                        "dispensacoes_recentes": [
                            {
                                "data": d.data_dispensacao.isoformat(),
                                "quantidade": d.quantidade,
                                "produto_id": d.produto_id
                            } for d in dispensacoes[:5]
                        ]
                    }
                })
            
            return {
                "associacao_id": associacao_id,
                "total_membros": len(relatorio),
                "membros": relatorio,
                "data_geracao": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"error": f"Erro ao gerar relatório de atividade: {str(e)}"}
    
    @staticmethod
    def get_dispensation_analytics(associacao_id: int, dias: int = 30) -> Dict[str, Any]:
        """Análise de dispensações com estatísticas"""
        try:
            data_inicio = datetime.utcnow() - timedelta(days=dias)
            
            dispensacoes = Dispensacao.query.filter(
                Dispensacao.associacao_id == associacao_id,
                Dispensacao.data_dispensacao >= data_inicio
            ).all()
            
            # Agrupar por produto
            por_produto = {}
            por_membro = {}
            por_dia = {}
            
            for disp in dispensacoes:
                # Por produto
                prod_id = disp.produto_id or "sem_produto"
                if prod_id not in por_produto:
                    por_produto[prod_id] = {"quantidade": 0, "count": 0}
                por_produto[prod_id]["quantidade"] += disp.quantidade or 0
                por_produto[prod_id]["count"] += 1
                
                # Por membro
                membro_id = disp.membro_id
                if membro_id not in por_membro:
                    por_membro[membro_id] = {"quantidade": 0, "count": 0}
                por_membro[membro_id]["quantidade"] += disp.quantidade or 0
                por_membro[membro_id]["count"] += 1
                
                # Por dia
                dia = disp.data_dispensacao.date().isoformat()
                if dia not in por_dia:
                    por_dia[dia] = 0
                por_dia[dia] += 1
            
            return {
                "periodo": {
                    "inicio": data_inicio.isoformat(),
                    "fim": datetime.utcnow().isoformat(),
                    "dias": dias
                },
                "totais": {
                    "dispensacoes": len(dispensacoes),
                    "produtos_diferentes": len(por_produto),
                    "membros_atendidos": len(por_membro)
                },
                "por_produto": por_produto,
                "por_membro": por_membro,
                "timeline": por_dia,
                "data_geracao": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"error": f"Erro ao gerar analytics: {str(e)}"}
    
    @staticmethod
    def get_stock_status(associacao_id: int) -> Dict[str, Any]:
        """Status atual do estoque"""
        try:
            itens = Estoque.query.filter_by(associacao_id=associacao_id).all()
            
            estoque_detalhado = []
            alertas = []
            
            for item in itens:
                item_dict = {
                    "id": item.id,
                    "produto_id": item.produto_id,
                    "lote": item.lote,
                    "quantidade_disponivel": item.quantidade_disponivel,
                    "quantidade_inicial": item.quantidade_inicial,
                    "data_entrada": item.data_entrada.isoformat() if item.data_entrada else None,
                    "data_validade": item.data_validade.isoformat() if item.data_validade else None
                }
                
                # Verificar alertas
                if item.quantidade_disponivel and item.quantidade_disponivel < 10:
                    alertas.append({
                        "tipo": "estoque_baixo",
                        "produto_id": item.produto_id,
                        "quantidade": item.quantidade_disponivel
                    })
                
                if item.data_validade:
                    dias_validade = (item.data_validade - datetime.utcnow().date()).days
                    if dias_validade < 30:
                        alertas.append({
                            "tipo": "vencimento_proximo",
                            "produto_id": item.produto_id,
                            "dias_restantes": dias_validade
                        })
                
                estoque_detalhado.append(item_dict)
            
            return {
                "associacao_id": associacao_id,
                "total_itens": len(itens),
                "estoque": estoque_detalhado,
                "alertas": alertas,
                "data_consulta": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"error": f"Erro ao consultar estoque: {str(e)}"}
