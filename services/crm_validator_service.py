"""
CRM Validation Service for Brazilian Medical Council verification

Integrates with CFM (Conselho Federal de Medicina) and regional CRM APIs
to validate medical professional credentials automatically.
"""

import requests
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class CRMValidatorService:
    """Service for validating CRM (medical license) authenticity"""
    
    # CFM API endpoints (these may need to be updated based on actual CFM API)
    CFM_BASE_URL = "https://portal.cfm.org.br/api"
    CFM_SEARCH_ENDPOINT = "/profissional/buscar"
    
    # Regional CRM portals (fallback if CFM API unavailable)
    REGIONAL_CRMS = {
        'SP': 'https://www.cremesp.org.br',
        'RJ': 'https://www.cremerj.org.br',
        'MG': 'https://www.crmmg.org.br',
        'RS': 'https://www.cremers.org.br',
        'PR': 'https://www.crmpr.org.br',
        'SC': 'https://www.cremesc.org.br',
        # Add more states as needed
    }
    
    @staticmethod
    def validate_crm_format(crm: str, uf: str) -> Tuple[bool, Optional[str]]:
        """
        Validate CRM format before API call
        
        Args:
            crm: CRM number (4-6 digits)
            uf: State code (2 letters)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate CRM number format
        if not re.match(r'^\d{4,6}$', crm):
            return False, "CRM deve conter entre 4 e 6 dígitos"
        
        # Validate UF format
        if not re.match(r'^[A-Z]{2}$', uf):
            return False, "UF deve conter 2 letras maiúsculas"
        
        return True, None
    
    @staticmethod
    def validate_crm_cfm(crm: str, uf: str) -> Dict:
        """
        Validate CRM using CFM (Federal Medical Council) API
        
        Args:
            crm: CRM number
            uf: State code
            
        Returns:
            Dict with validation results
        """
        # First validate format
        is_valid_format, error = CRMValidatorService.validate_crm_format(crm, uf)
        if not is_valid_format:
            return {
                'success': False,
                'source': 'format_validation',
                'error': error,
                'data': None
            }
        
        try:
            # NOTA: Este é um exemplo. A API real do CFM pode ter endpoints diferentes
            # Você precisará ajustar baseado na documentação oficial do CFM
            
            # Tentar consulta via API pública (se disponível)
            response = requests.get(
                f"{CRMValidatorService.CFM_BASE_URL}{CRMValidatorService.CFM_SEARCH_ENDPOINT}",
                params={
                    'crm': crm,
                    'uf': uf
                },
                timeout=10,
                headers={'User-Agent': 'Aracannabis-Validator/1.0'}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'source': 'cfm_api',
                    'data': data,
                    'validated_at': datetime.utcnow().isoformat()
                }
            else:
                # API não disponível ou médico não encontrado
                logger.warning(f"CFM API returned {response.status_code} for CRM {crm}/{uf}")
                return {
                    'success': False,
                    'source': 'cfm_api',
                    'error': f'API CFM retornou status {response.status_code}',
                    'data': None
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout ao consultar CFM para CRM {crm}/{uf}")
            return {
                'success': False,
                'source': 'cfm_api',
                'error': 'Timeout na consulta ao CFM',
                'data': None
            }
        except Exception as e:
            logger.error(f"Erro ao validar CRM {crm}/{uf}: {str(e)}")
            return {
                'success': False,
                'source': 'cfm_api',
                'error': str(e),
                'data': None
            }
    
    @staticmethod
    def validate_crm_regional(crm: str, uf: str) -> Dict:
        """
        Fallback validation using regional CRM website
        
        Args:
            crm: CRM number
            uf: State code
            
        Returns:
            Dict with validation results
        """
        if uf not in CRMValidatorService.REGIONAL_CRMS:
            return {
                'success': False,
                'source': 'regional_crm',
                'error': f'Portal CRM-{uf} não configurado',
                'data': None
            }
        
        # NOTA: Implementação simplificada
        # Na prática, você precisaria fazer scraping ou usar APIs específicas de cada regional
        try:
            regional_url = CRMValidatorService.REGIONAL_CRMS[uf]
            
            # Exemplo: tentar acessar página de busca
            # Esta é uma implementação genérica, cada CRM regional tem sua própria estrutura
            logger.info(f"Tentando validação regional para CRM {crm}/{uf} em {regional_url}")
            
            # Por enquanto, retornamos que precisa validação manual
            return {
                'success': False,
                'source': 'regional_crm',
                'error': 'Validação regional requer implementação específica',
                'requires_manual_review': True,
                'data': {
                    'regional_url': regional_url,
                    'crm': crm,
                    'uf': uf
                }
            }
            
        except Exception as e:
            logger.error(f"Erro na validação regional CRM {crm}/{uf}: {str(e)}")
            return {
                'success': False,
                'source': 'regional_crm',
                'error': str(e),
                'data': None
            }
    
    @staticmethod
    def validate_crm(crm: str, uf: str) -> Dict:
        """
        Main validation method that tries all available sources
        
        Args:
            crm: CRM number
            uf: State code
            
        Returns:
            Dict with comprehensive validation results
        """
        results = {
            'crm': crm,
            'uf': uf,
            'validated_at': datetime.utcnow().isoformat(),
            'sources_tried': []
        }
        
        # Try CFM first
        cfm_result = CRMValidatorService.validate_crm_cfm(crm, uf)
        results['sources_tried'].append({
            'name': 'cfm_api',
            'result': cfm_result
        })
        
        if cfm_result['success']:
            results['status'] = 'validated'
            results['source'] = 'cfm_api'
            results['data'] = cfm_result['data']
            return results
        
        # If CFM fails, try regional
        regional_result = CRMValidatorService.validate_crm_regional(crm, uf)
        results['sources_tried'].append({
            'name': 'regional_crm',
            'result': regional_result
        })
        
        if regional_result.get('requires_manual_review'):
            results['status'] = 'manual_review_required'
            results['source'] = 'regional_crm'
            results['data'] = regional_result['data']
            return results
        
        # All sources failed
        results['status'] = 'validation_failed'
        results['error'] = 'Não foi possível validar o CRM em nenhuma fonte disponível'
        return results
    
    @staticmethod
    def extract_professional_data(validation_result: Dict) -> Optional[Dict]:
        """
        Extract structured professional data from validation result
        
        Args:
            validation_result: Result from validate_crm()
            
        Returns:
            Dict with extracted professional data or None
        """
        if validation_result.get('status') != 'validated':
            return None
        
        data = validation_result.get('data', {})
        
        # Extract relevant fields (adjust based on actual API response structure)
        return {
            'nome_completo': data.get('nome') or data.get('name'),
            'crm': validation_result['crm'],
            'uf': validation_result['uf'],
            'situacao': data.get('situacao') or data.get('status'),
            'especialidades': data.get('especialidades') or [],
            'data_inscricao': data.get('data_inscricao'),
            'validated_at': validation_result['validated_at']
        }
