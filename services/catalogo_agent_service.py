"""
Serviço de agentes para catálogo de produtos de cannabis
Integra processamento de documentos, busca e recomendação
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from models import db
from models_produto import ProdutoCannabis, CatalogoImportacao, SugestaoPrescricao

logger = logging.getLogger(__name__)


class CatalogoAgentService:
    """
    Agente especializado em catálogo de produtos de cannabis
    Responsabilidades:
    1. Processar e importar catálogos de empresas
    2. Estruturar e normalizar dados de produtos
    3. Buscar e filtrar produtos por critérios
    4. Sugerir produtos para prescrições
    5. Validar informações com agente farmacêutico
    6. Buscar atualizações na web
    """
    
    def __init__(self):
        from services.catalogo_document_processor import document_processor
        from services.ai_agents import ai_manager
        
        self.document_processor = document_processor
        self.ai_manager = ai_manager
        
    def processar_catalogo(self, arquivo_path: str, filename: str, 
                          profissional_id: int, associacao_id: int = None,
                          empresa_origem: str = None) -> Dict[str, Any]:
        """
        Processa um arquivo de catálogo e importa produtos
        
        Returns:
            Dict com resultado da importação
        """
        # Cria registro de importação
        importacao = CatalogoImportacao(
            nome_arquivo=filename,
            tipo_arquivo=filename.rsplit('.', 1)[1].lower(),
            empresa_origem=empresa_origem,
            profissional_id=profissional_id,
            associacao_id=associacao_id,
            arquivo_path=arquivo_path,
            status='processando'
        )
        db.session.add(importacao)
        db.session.commit()
        
        try:
            # Processa o arquivo
            resultado = self.document_processor.process_file(arquivo_path, filename)
            
            if 'error' in resultado:
                importacao.status = 'erro'
                importacao.erros = resultado['error']
                db.session.commit()
                return {
                    'success': False,
                    'importacao_id': importacao.id,
                    'error': resultado['error']
                }
            
            # Extrai produtos
            produtos_extraidos = resultado.get('dados', [])
            importacao.total_produtos = len(produtos_extraidos)
            
            if not produtos_extraidos:
                importacao.status = 'concluido'
                db.session.commit()
                return {
                    'success': True,
                    'importacao_id': importacao.id,
                    'message': 'Nenhum produto encontrado no arquivo',
                    'produtos_importados': 0
                }
            
            # Valida e importa produtos
            produtos_importados = 0
            produtos_atualizados = 0
            erros = []
            
            for produto_data in produtos_extraidos:
                try:
                    resultado_import = self._importar_ou_atualizar_produto(
                        produto_data, 
                        profissional_id, 
                        associacao_id,
                        filename
                    )
                    
                    if resultado_import['acao'] == 'importado':
                        produtos_importados += 1
                    elif resultado_import['acao'] == 'atualizado':
                        produtos_atualizados += 1
                        
                except Exception as e:
                    erros.append(f"Erro em {produto_data.get('nome', 'desconhecido')}: {str(e)}")
                    continue
            
            # Atualiza registro de importação
            importacao.produtos_importados = produtos_importados
            importacao.produtos_atualizados = produtos_atualizados
            importacao.status = 'concluido' if not erros else 'parcial'
            importacao.erros = '\n'.join(erros) if erros else None
            importacao.completed_at = datetime.utcnow()
            db.session.commit()
            
            return {
                'success': True,
                'importacao_id': importacao.id,
                'produtos_importados': produtos_importados,
                'produtos_atualizados': produtos_atualizados,
                'erros': erros if erros else None,
                'detalhes': resultado
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar catálogo: {str(e)}")
            importacao.status = 'erro'
            importacao.erros = str(e)
            db.session.commit()
            return {
                'success': False,
                'importacao_id': importacao.id,
                'error': str(e)
            }
    
    def _importar_ou_atualizar_produto(self, produto_data: Dict, 
                                        profissional_id: int, 
                                        associacao_id: int,
                                        arquivo_origem: str) -> Dict[str, str]:
        """Importa produto novo ou atualiza existente"""
        
        # Busca produto existente por nome/marca similares
        nome = produto_data.get('nome', '')
        marca = produto_data.get('marca', '')
        
        produto_existente = ProdutoCannabis.query.filter(
            db.func.lower(ProdutoCannabis.nome).like(f"%{nome.lower()}%"),
            db.func.lower(ProdutoCannabis.marca).like(f"%{marca.lower()}%")
        ).first()
        
        if produto_existente:
            # Atualiza produto existente
            self._atualizar_produto(produto_existente, produto_data)
            acao = 'atualizado'
            produto_id = produto_existente.id
        else:
            # Cria novo produto
            produto = self._criar_produto(produto_data, profissional_id, associacao_id, arquivo_origem)
            db.session.add(produto)
            acao = 'importado'
            produto_id = produto.id
        
        db.session.commit()
        return {'acao': acao, 'produto_id': produto_id}
    
    def _criar_produto(self, data: Dict, profissional_id: int, 
                       associacao_id: int, arquivo_origem: str) -> ProdutoCannabis:
        """Cria novo produto a partir dos dados extraídos"""
        return ProdutoCannabis(
            nome=data.get('nome', 'Produto sem nome'),
            nome_comercial=data.get('nome_comercial'),
            marca=data.get('marca', 'Marca desconhecida'),
            categoria=data.get('categoria'),
            laboratorio=data.get('laboratorio'),
            cbd_total_mg=data.get('cbd_mg'),
            thc_total_mg=data.get('thc_mg'),
            cbg_mg=data.get('cbg_mg'),
            volume_ml=data.get('volume'),
            quantidade_cps=data.get('quantidade_cps'),
            via_administracao=data.get('via_administracao'),
            indicacoes=data.get('indicacoes'),
            composicao_veiculo=data.get('composicao'),
            registro_anvisa=data.get('registro_anvisa'),
            preco_referencia=data.get('preco'),
            quimiotipo=data.get('quimiotipo'),
            razao_cbd_thc=data.get('razao_cbd_thc'),
            associacao_id=associacao_id,
            created_by=profissional_id,
            arquivo_origem=arquivo_origem,
            fonte_dados='Importação Automática'
        )
    
    def _atualizar_produto(self, produto: ProdutoCannabis, data: Dict):
        """Atualiza produto existente com novos dados"""
        # Só atualiza campos não nulos nos novos dados
        if data.get('nome'):
            produto.nome = data['nome']
        if data.get('marca'):
            produto.marca = data['marca']
        if data.get('categoria'):
            produto.categoria = data['categoria']
        if data.get('cbd_mg'):
            produto.cbd_total_mg = data['cbd_mg']
        if data.get('thc_mg'):
            produto.thc_total_mg = data['thc_mg']
        if data.get('cbg_mg'):
            produto.cbg_mg = data['cbg_mg']
        if data.get('volume'):
            produto.volume_ml = data['volume']
        if data.get('via_administracao'):
            produto.via_administracao = data['via_administracao']
        if data.get('indicacoes'):
            produto.indicacoes = data['indicacoes']
        if data.get('preco'):
            produto.preco_referencia = data['preco']
        if data.get('quimiotipo'):
            produto.quimiotipo = data['quimiotipo']
        
        produto.updated_at = datetime.utcnow()
    
    def buscar_produtos(self, filtros: Dict[str, Any]) -> List[Dict]:
        """
        Busca produtos com filtros avançados
        """
        query = ProdutoCannabis.query
        
        # Filtro por texto (nome/marca)
        if filtros.get('nome'):
            termo = f"%{filtros['nome'].lower()}%"
            query = query.filter(
                db.or_(
                    db.func.lower(ProdutoCannabis.nome).like(termo),
                    db.func.lower(ProdutoCannabis.marca).like(termo)
                )
            )
        
        # Filtro por categoria
        if filtros.get('categoria'):
            query = query.filter(ProdutoCannabis.categoria.ilike(f"%{filtros['categoria']}%"))
        
        # Filtros de range CBD
        if filtros.get('cbd_min'):
            query = query.filter(ProdutoCannabis.cbd_total_mg >= float(filtros['cbd_min']))
        if filtros.get('cbd_max'):
            query = query.filter(ProdutoCannabis.cbd_total_mg <= float(filtros['cbd_max']))
        
        # Filtros de range THC
        if filtros.get('thc_min'):
            query = query.filter(ProdutoCannabis.thc_total_mg >= float(filtros['thc_min']))
        if filtros.get('thc_max'):
            query = query.filter(ProdutoCannabis.thc_total_mg <= float(filtros['thc_max']))
        
        # Filtro por quimiotipo
        if filtros.get('quimiotipo'):
            query = query.filter(ProdutoCannabis.quimiotipo.ilike(f"%{filtros['quimiotipo']}%"))
        
        # Filtro por via
        if filtros.get('via_administracao'):
            query = query.filter(ProdutoCannabis.via_administracao.ilike(f"%{filtros['via_administracao']}%"))
        
        # Filtro por indicação
        if filtros.get('indicacao'):
            query = query.filter(ProdutoCannabis.indicacoes.ilike(f"%{filtros['indicacao']}%"))
        
        # Filtro por marca
        if filtros.get('marca'):
            query = query.filter(ProdutoCannabis.marca.ilike(f"%{filtros['marca']}%"))
        
        # Filtro por disponibilidade
        if filtros.get('disponivel') is not None:
            query = query.filter(ProdutoCannabis.disponivel_brasil == filtros['disponivel'])
        
        # Filtro por associação
        if filtros.get('associacao_id'):
            query = query.filter(ProdutoCannabis.associacao_id == filtros['associacao_id'])
        else:
            # Por padrão, mostra produtos globais (sem associação específica)
            query = query.filter(ProdutoCannabis.associacao_id.is_(None))
        
        # Só ativos
        query = query.filter(ProdutoCannabis.ativo == True)
        
        # Ordena por nome
        query = query.order_by(ProdutoCannabis.marca, ProdutoCannabis.nome)
        
        # Limita resultados
        limit = filtros.get('limit', 100)
        query = query.limit(limit)
        
        produtos = query.all()
        return [p.to_dict() for p in produtos]
    
    def sugerir_produtos_prescricao(self, paciente_id: int, profissional_id: int,
                                     condicao: str, sintomas: str,
                                     preferencias: Dict = None) -> Dict[str, Any]:
        """
        Usa IA para sugerir produtos adequados para um paciente
        """
        preferencias = preferencias or {}
        
        # Busca produtos disponíveis
        produtos_disponiveis = self.buscar_produtos({'disponivel': True, 'limit': 50})
        
        if not produtos_disponiveis:
            return {
                'success': False,
                'message': 'Nenhum produto disponível no catálogo',
                'sugestoes': []
            }
        
        # Busca histórico do paciente
        from services.db_tools import DatabaseTools
        db_tools = DatabaseTools(profissional_id=profissional_id)
        
        paciente = db_tools.buscar_paciente(paciente_id)
        historico_dosagens = db_tools.buscar_dosagens_paciente(paciente_id)
        
        # Prepara contexto para IA
        contexto = {
            'paciente': paciente,
            'condicao_medica': condicao,
            'sintomas_alvo': sintomas,
            'historico_tratamento': historico_dosagens[-5:] if historico_dosagens else [],
            'preferencias': preferencias,
            'produtos_disponiveis': produtos_disponiveis[:30]
        }
        
        # Consulta agente farmacêutico via IA
        system_prompt = """Você é um farmacêutico especialista em cannabis medicinal.
        
        Analise o caso do paciente e sugira os 3-5 produtos MAIS adequados do catálogo disponível.
        
        Critérios de seleção:
        1. Adequação à condição médica e sintomas
        2. Composição de canabinoides (CBD/THC)
        3. Quimiotipo apropriado
        4. Via de administração preferida
        5. Histórico de resposta do paciente
        6. Perfil de terpenos se relevante
        7. Contraindicações e interações
        
        Para cada produto sugerido, forneça:
        - id do produto (use o id fornecido)
        - nome e marca
        - justificativa clínica detalhada
        - posologia sugerida inicial
        - precauções específicas
        - alternativas se não tolerado
        
        Formato de resposta (JSON):
        {
            "sugestoes": [
                {
                    "produto_id": 123,
                    "nome": "...",
                    "marca": "...",
                    "justificativa": "...",
                    "posologia_sugerida": "...",
                    "precaucoes": "..."
                }
            ],
            "consideracoes_gerais": "...",
            "recomendacao_farmaceutica": "..."
        }
        
        IMPORTANTE: 
        - Explique o raciocínio clínico
        - Mencione possíveis interações
        - Sugira monitoramento"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Caso clínico: {json.dumps(contexto, ensure_ascii=False, default=str)}"}
        ]
        
        response = self.ai_manager.chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=3000
        )
        
        try:
            content = response.get('content', '')
            
            # Extrai JSON
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
            resultado = json.loads(content.strip())
            
            # Salva sugestão no banco
            sugestao = SugestaoPrescricao(
                paciente_id=paciente_id,
                profissional_id=profissional_id,
                condicao_medica=condicao,
                sintomas_alvo=sintomas,
                evitar_thc=preferencias.get('evitar_thc', False),
                preferencia_cbd=preferencias.get('preferencia_cbd', False),
                via_preferida=preferencias.get('via_preferida'),
                produtos_sugeridos=resultado.get('sugestoes', []),
                justificativa_ia=resultado.get('consideracoes_gerais', '')
            )
            db.session.add(sugestao)
            db.session.commit()
            
            return {
                'success': True,
                'sugestao_id': sugestao.id,
                'sugestoes': resultado.get('sugestoes', []),
                'consideracoes_gerais': resultado.get('consideracoes_gerais', ''),
                'recomendacao_farmaceutica': resultado.get('recomendacao_farmaceutica', '')
            }
            
        except Exception as e:
            logger.error(f"Erro ao parsear sugestão: {str(e)}")
            return {
                'success': False,
                'message': f'Erro ao processar sugestão: {str(e)}',
                'raw_response': response.get('content', '')
            }
    
    def validar_produto_com_farmaceutico(self, produto_id: int) -> Dict[str, Any]:
        """
        Valida dados de um produto com o agente farmacêutico
        """
        produto = ProdutoCannabis.query.get(produto_id)
        if not produto:
            return {'success': False, 'error': 'Produto não encontrado'}
        
        produto_dict = produto.to_dict()
        
        system_prompt = """Você é um farmacêutico especialista em cannabis medicinal.
        
        Valide as informações deste produto e identifique:
        1. Possíveis inconsistências nos dados
        2. Informações faltantes críticas
        3. Questões regulatórias
        4. Recomendações de uso
        5. Alertas de segurança
        
        Formato de resposta (JSON):
        {
            "validacao": {
                "status": "aprovado|pendente|rejeitado",
                "confianca": "alta|media|baixa",
                "dados_completos": true/false
            },
            "inconsistencias": ["..."],
            "dados_faltantes": ["..."],
            "alertas": ["..."],
            "recomendacoes": ["..."],
            "notas_regulatorias": "..."
        }"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Valide este produto: {json.dumps(produto_dict, ensure_ascii=False, default=str)}"}
        ]
        
        response = self.ai_manager.chat_completion(
            messages=messages,
            temperature=0.2,
            max_tokens=2000
        )
        
        try:
            content = response.get('content', '')
            
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
            validacao = json.loads(content.strip())
            
            # Atualiza produto com validação
            if validacao.get('validacao', {}).get('status') == 'aprovado':
                produto.verificado = True
                db.session.commit()
            
            return {
                'success': True,
                'produto_id': produto_id,
                'validacao': validacao
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro na validação: {str(e)}',
                'raw_response': response.get('content', '')
            }
    
    def buscar_atualizacoes_web(self, marca: str = None) -> Dict[str, Any]:
        """
        Busca atualizações de produtos na web
        """
        marcas_conhecidas = marca if marca else [
            'Prisma', 'Phexia', 'Verd', 'Cannabis Brasil',
            'Real Scientific', 'Canabidiol Life', 'Weedoo'
        ]
        
        return {
            'success': True,
            'message': 'Busca web - estrutura preparada para integração',
            'marcas_monitoradas': marcas_conhecidas if isinstance(marcas_conhecidas, list) else [marcas_conhecidas],
            'novos_produtos_encontrados': [],
            'atualizacoes_precos': [],
            'recomendacao': 'Implementar integração com SerpAPI ou similar'
        }
    
    def comparar_produtos(self, produto_ids: List[int]) -> Dict[str, Any]:
        """
        Compara múltiplos produtos lado a lado
        """
        produtos = ProdutoCannabis.query.filter(ProdutoCannabis.id.in_(produto_ids)).all()
        
        if len(produtos) < 2:
            return {
                'success': False,
                'error': 'Selecione pelo menos 2 produtos para comparar'
            }
        
        # Prepara dados comparativos
        comparacao = {
            'produtos': [p.to_dict() for p in produtos],
            'diferencas': self._calcular_diferencas(produtos)
        }
        
        # Análise com IA
        system_prompt = """Compare estes produtos de cannabis medicinal destacando:
        1. Diferenças principais
        2. Vantagens de cada um
        3. Indicações específicas
        4. Custo-benefício
        5. Recomendação de escolha"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(comparacao, ensure_ascii=False, default=str)}
        ]
        
        response = self.ai_manager.chat_completion(
            messages=messages,
            temperature=0.4,
            max_tokens=1500
        )
        
        return {
            'success': True,
            'comparacao_tecnica': comparacao,
            'analise_ia': response.get('content', '')
        }
    
    def _calcular_diferencas(self, produtos: List[ProdutoCannabis]) -> Dict[str, Any]:
        """Calcula diferenças entre produtos"""
        cbd_vals = [p.cbd_total_mg for p in produtos if p.cbd_total_mg]
        thc_vals = [p.thc_total_mg for p in produtos if p.thc_total_mg]
        preco_vals = [p.preco_referencia for p in produtos if p.preco_referencia]
        
        diferencas = {
            'cbd_max': max(cbd_vals) if cbd_vals else 0,
            'cbd_min': min(cbd_vals) if cbd_vals else 0,
            'thc_max': max(thc_vals) if thc_vals else 0,
            'thc_min': min(thc_vals) if thc_vals else 0,
            'preco_max': float(max(preco_vals)) if preco_vals else 0,
            'preco_min': float(min(preco_vals)) if preco_vals else 0,
            'quimiotipos': list(set([p.quimiotipo for p in produtos if p.quimiotipo])),
            'vias': list(set([p.via_administracao for p in produtos if p.via_administracao]))
        }
        return diferencas


# Instância global
catalogo_service = CatalogoAgentService()