import os
import requests
import re

class ExternalAssociationService:
    @staticmethod
    def _get_api_config():
        """Helper to get API config"""
        # Default to host.docker.internal for local dev between containers/host
        api_url = os.getenv('EXTERNAL_ASSOC_API_URL', 'http://host.docker.internal:8011/api')
        # Default assoc ID to 1 if not set
        assoc_id = os.getenv('EXTERNAL_ASSOC_ID', '1')
        api_token = os.getenv('EXTERNAL_ASSOC_API_TOKEN')
        return api_url, assoc_id, api_token

    @staticmethod
    def search_associate(cpf):
        """
        Busca associado em sistema externo via API.
        Retorna dicionário com dados do associado ou None.
        """
        api_url, assoc_id, api_token = ExternalAssociationService._get_api_config()
        
        try:
            # Limpar CPF
            clean_cpf = re.sub(r'\D', '', cpf)
            
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            } if api_token else {}
            
            # Endpoint: /association/{id}/members/search?cpf=...
            response = requests.get(
                f"{api_url}/association/{assoc_id}/members/search", 
                params={'cpf': clean_cpf},
                headers=headers, 
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if not data:
                    return None
                    
                # API returns list, get first item
                if isinstance(data, list):
                    if len(data) > 0:
                        member_data = data[0]
                    else:
                        return None
                else:
                    member_data = data

                # Create normalized dict using AGROBUDS schema keys
                return {
                    'nome': member_data.get('full_name'),
                    'email': member_data.get('email'),
                    'telefone': member_data.get('phone'),
                    'endereco': member_data.get('address'),
                    'data_nascimento': member_data.get('data_nascimento'),
                    'rg': member_data.get('rg'), # Check if AGROBUDS has RG, might be in "address" or custom field? Schema didn't show RG explicitly in MemberBase, assuming standard fields or ignoring if missing.
                    'id': member_data.get('id'),
                    'external_id': member_data.get('id')
                }
            return None
        except Exception as e:
            print(f"Error searching external association: {str(e)}")
            return None

    @staticmethod
    def sync_patient_to_association(paciente_data):
        """
        Envia dados do paciente do Prontuário para o sistema de Associação.
        Usado quando um paciente é criado ou atualizado no Prontuário.
        """
        api_url, assoc_id, api_token = ExternalAssociationService._get_api_config()
        
        if not api_url:
            print("External Association API URL not configured. Skipping sync.")
            return False
            
        try:
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            } if api_token else {}
            
            # 1. Search if member exists first to decide Create vs Update
            cpf_clean = re.sub(r'\D', '', paciente_data.get('cpf', ''))
            existing_member = ExternalAssociationService.search_associate(cpf_clean)
            
            # Map Prontuário fields to AGROBUDS Schema (MemberBase)
            payload = {
                'full_name': paciente_data.get('nome'),
                'cpf': cpf_clean,
                'email': paciente_data.get('email'),
                'phone': paciente_data.get('telefone'),
                'address': paciente_data.get('endereco'),
                'data_nascimento': paciente_data.get('data_nascimento').isoformat() if paciente_data.get('data_nascimento') else None,
                # 'status': 'Ativo', # Optional
            }
            
            if existing_member:
                # UPDATE
                member_id = existing_member['id']
                print(f"Syncing (UPDATE) member {member_id} in association...")
                # Endpoint: PUT /association/members/{member_id}
                # Note: AGROBUDS router prefix is /association, main prefix /api -> /api/association/members/{id}
                # Wait, router has `prefix="/association"`. Update route is `@router.put("/members/{member_id}")`.
                # So full path: /api/association/members/{id}
                response = requests.put(
                    f"{api_url}/association/members/{member_id}", 
                    json=payload,
                    headers=headers, 
                    timeout=10
                )
            else:
                # CREATE
                print(f"Syncing (CREATE) new member in association {assoc_id}...")
                # Endpoint: POST /association/{id}/members/
                response = requests.post(
                    f"{api_url}/association/{assoc_id}/members/", 
                    json=payload,
                    headers=headers, 
                    timeout=10
                )
            
            if response.status_code in [200, 201]:
                return True
            else:
                print(f"Failed to sync patient to association. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"Error syncing to external association: {str(e)}")
            return False
