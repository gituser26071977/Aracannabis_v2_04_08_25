import requests
import logging

logger = logging.getLogger(__name__)

class BrasilAPIService:
    """Service to interact with BrasilAPI (https://brasilapi.com.br/)"""
    
    BASE_URL = "https://brasilapi.com.br/api"
    
    @staticmethod
    def get_address_by_cep(cep: str):
        """
        Fetches address information for a given CEP.
        """
        # Remove non-digits
        cep = "".join(filter(str.isdigit, cep))
        
        if len(cep) != 8:
            return {"success": False, "error": "CEP inválido. Deve ter 8 dígitos."}
            
        try:
            url = f"{BrasilAPIService.BASE_URL}/cep/v2/{cep}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            elif response.status_code == 404:
                # Fallback to v1 if v2 fails or for different structures
                url_v1 = f"{BrasilAPIService.BASE_URL}/cep/v1/{cep}"
                response_v1 = requests.get(url_v1, timeout=10)
                if response_v1.status_code == 200:
                    return {"success": True, "data": response_v1.json()}
                return {"success": False, "error": "CEP não encontrado."}
            else:
                return {"success": False, "error": f"Erro na API BrasilAPI: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Erro ao consultar CEP {cep}: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_cnpj_info(cnpj: str):
        """
        Fetches company information for a given CNPJ.
        """
        cnpj = "".join(filter(str.isdigit, cnpj))
        
        try:
            url = f"{BrasilAPIService.BASE_URL}/cnpj/v1/{cnpj}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"Erro na API BrasilAPI (CNPJ): {response.status_code}"}
        except Exception as e:
            logger.error(f"Erro ao consultar CNPJ {cnpj}: {e}")
            return {"success": False, "error": str(e)}
