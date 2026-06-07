import os
import argparse
import pandas as pd
import json
import requests
import re
import logging
import time
import zipfile
import shutil
from PIL import Image
import pdf2image
import pytesseract

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ingest.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configurações Ollama (Local ou Cloud Proxy)
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
MODEL_NAME = "kimi-k2.5:cloud" 
ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.pdf'}

class LLMClient:
    def _call_ollama(self, messages, max_retries=3):
        """Chamada ao endpoint /api/chat do Ollama"""
        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "stream": False,
            "format": "json", # Ollama suporta JSON mode
            "options": {
                "temperature": 0.1
            }
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{OLLAMA_BASE_URL}/api/chat",
                    json=payload,
                    timeout=120
                )
                
                if response.status_code == 200:
                    return response.json()['message']['content']
                else:
                    logger.error(f"Erro Ollama {response.status_code}: {response.text}")
                    # Se 404, modelo não existe
                    if response.status_code == 404:
                         logger.critical(f"Modelo {MODEL_NAME} não encontrado. Execute 'ollama pull {MODEL_NAME}'.")
                         return None
            except Exception as e:
                logger.error(f"Exceção na chamada Ollama: {e}")
                time.sleep(1)
        
        return None

    def classify(self, ocr_text):
        prompt = """
        Analise o texto extraído de um documento (OCR).
        Classifique-o em UMA das seguintes categorias:
        [RECEITA_MEDICA, DOCUMENTO_PESSOAL, LAUDO_MEDICO, COMPROVANTE_RESIDENCIA, OUTRO]
        
        Responda ESTRITAMENTE um JSON no formato:
        {"tipo_documento": "CATEGORIA", "confianca": "ALTA/MEDIA/BAIXA"}
        """
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Texto do Documento:\n\n{ocr_text[:4000]}"}
        ]
        
        try:
            res = self._call_ollama(messages)
            if res:
                cleaned = re.sub(r'```json\s*|\s*```', '', res).strip()
                match = re.search(r'\{.*\}', cleaned, re.DOTALL)
                if match:
                    cleaned = match.group(0)
                return json.loads(cleaned)
        except Exception as e:
            logger.error(f"Erro parse classificação: {e}")
            
        return {"tipo_documento": "OUTRO", "confianca": "BAIXA"}

    def extract(self, doc_type, ocr_text):
        specific_prompt = ""
        if doc_type == "RECEITA_MEDICA":
            specific_prompt = """
            Extraia:
            - nome_paciente
            - cpf
            - data_receita
            - lista_medicamentos (array)
            """
        elif doc_type == "DOCUMENTO_PESSOAL":
            specific_prompt = """
            Extraia:
            - nome_completo
            - cpf
            - rg
            - data_nascimento
            - nome_mae
            """
        elif doc_type == "COMPROVANTE_RESIDENCIA":
            specific_prompt = """
            Extraia:
            - nome_titular
            - endereco_completo
            - data
            """
        else:
            specific_prompt = "Extraia resumo dos dados principais."

        system_prompt = f"""
        Você é um assistente de extração de dados.
        Tipo detectado: {doc_type}.
        {specific_prompt}
        Retorne APENAS JSON válido.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": ocr_text[:8000]}
        ]
        
        try:
            res = self._call_ollama(messages)
            if res:
                # Limpeza robusta de Markdown
                cleaned = re.sub(r'```json\s*|\s*```', '', res).strip()
                # Tentar encontrar o primeiro { e o último }
                match = re.search(r'\{.*\}', cleaned, re.DOTALL)
                if match:
                    cleaned = match.group(0)
                return json.loads(cleaned)
        except Exception as e:
            logger.error(f"Erro parse extração: {e}. Resposta bruta: {res[:200]}")
             
        return {}

def ocr_image(image_path):
    try:
        return pytesseract.image_to_string(Image.open(image_path), lang='por')
    except Exception as e:
        logger.error(f"Erro Tesseract: {e}")
        return ""

def process_file(file_path, llm_client):
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        return {'status': 'IGNORADO', 'observacoes': f'Extensão {ext} não suportada'}

    temp_image_path = file_path
    cleanup_temp = False
    
    if ext == '.pdf':
        try:
            images = pdf2image.convert_from_path(file_path, first_page=1, last_page=1)
            if images:
                temp_image_path = file_path + ".jpg"
                images[0].save(temp_image_path, 'JPEG')
                cleanup_temp = True
            else:
                return {'status': 'ERRO', 'observacoes': 'PDF vazio'}
        except Exception as e:
            return {'status': 'ERRO', 'observacoes': f'Erro convertendo PDF: {e}'}

    ocr_text = ocr_image(temp_image_path)
    if not ocr_text.strip():
        if cleanup_temp and os.path.exists(temp_image_path): os.remove(temp_image_path)
        return {'status': 'ILEGIVEL', 'observacoes': 'Sem texto detectável'}

    class_res = llm_client.classify(ocr_text)
    doc_type = class_res.get('tipo_documento', 'OUTRO')
    
    extract_res = llm_client.extract(doc_type, ocr_text)
    
    if cleanup_temp and os.path.exists(temp_image_path): os.remove(temp_image_path)
    
    output = {
        'status': 'OK',
        'arquivo_origem': os.path.basename(file_path),
        'tipo_documento': doc_type,
        'confianca': class_res.get('confianca', 'BAIXA'),
        'nome_detectado': extract_res.get('nome_paciente') or extract_res.get('nome_completo') or extract_res.get('nome_titular'),
        'cpf_detectado': extract_res.get('cpf'),
        'dados_json': json.dumps(extract_res, ensure_ascii=False),
        'previa_ocr': ocr_text[:100].replace('\n', ' ')
    }
    return output

def process_batch(files, llm_client):
    results = []
    total = len(files)
    for i, file_path in enumerate(files):
        logger.info(f"[{i+1}/{total}] Processando {os.path.basename(file_path)}...")
        try:
            res = process_file(file_path, llm_client)
            results.append(res)
        except Exception as e:
            logger.error(f"Erro no processamento: {e}")
            results.append({'arquivo_origem': os.path.basename(file_path), 'status': 'ERRO_FATAL', 'observacoes': str(e)})
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    
    llm_client = LLMClient()
    files_to_process = []
    temp_dir = None
    
    if args.input.lower().endswith('.zip'):
        temp_dir = "temp_ingest_ollama"
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        with zipfile.ZipFile(args.input, 'r') as z: z.extractall(temp_dir)
        scan_path = temp_dir
    else:
        scan_path = args.input
        
    for root, _, files in os.walk(scan_path):
        for f in files: files_to_process.append(os.path.join(root, f))
        
    logger.info(f"Iniciando com modelo {MODEL_NAME} via Ollama...")
    data = process_batch(files_to_process, llm_client)
    
    pd.DataFrame(data).to_excel(args.output, index=False)
    logger.info(f"Salvo em {args.output}")
    
    if temp_dir: shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
